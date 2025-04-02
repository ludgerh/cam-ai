import cv2
import asyncio
import mpmath
import random
import threading
from time import time
from l_buffer import l_buffer

async def cb():
  """Callback-Funktion."""
  #print('Das ist der Callback...')
  pass

async def producer(buffer):
  """Produziert Videoframes und sendet sie in den Buffer."""
  await buffer.check_in('P')
  cap = cv2.VideoCapture(0)
  if not cap.isOpened():
    print("Kamera nicht verfügbar")
    return
  #ret, frame = await asyncio.to_thread(cap.read)
  #frame = cv2.resize(frame, (20000, 20000))
  for i in range(1000):
    #print(i)
    ret, frame = await asyncio.to_thread(cap.read)
    if not ret:
      continue
    data = [
      {'eins': 1, 'zwei': 2, 'drei': 3}, 
      {'eins': 1, 'zwei': 2, 'drei': 3}, 
      frame
    ]
    pi_str = str(mpmath.pi)
    i = 0
    length = random.randint(100, 1000)
    while len(pi_str) < length:
      pi_str += str(i)
      i = (i + 1) % 10
    pi_bytes = bytearray(pi_str.encode("utf-8"))
    data.append(pi_bytes)
    await buffer.put(data)
  await buffer.stop('P')

async def consumer(buffer):
  """Konsumiert Videoframes aus dem Buffer und zeigt sie an."""
  await buffer.check_in('C')
  while True:
    data = await buffer.get()
    if data == 'stop':
      break
    if data:
      print(data[0], data[1], data[3])
      cv2.imshow("Received Frame", data[2])
      cv2.waitKey(1) 
  await buffer.stop('C')

def run_async_in_thread(async_func, *args):
  asyncio.run(async_func(*args))

async def main():
  ts = time()
  buffer = await l_buffer.init('OLNB', m_proc = False, q_len = None,)

  producer_thread = threading.Thread(target=run_async_in_thread, args=(producer, buffer))
  consumer_thread = threading.Thread(target=run_async_in_thread, args=(consumer, buffer))
  producer_thread.start()
  consumer_thread.start()

  # Producer zuerst abwarten
  producer_thread.join()
  print('Producer beendet...')

  # Dann Consumer abwarten
  consumer_thread.join()
  print('Consumer beendet...')

  print('Time:', time() - ts)

if __name__ == '__main__':
  asyncio.run(main())

