import cv2
import asyncio
import mpmath
import multiprocessing as mp
from time import time
from aiomultiprocess import Worker
from random import randint
from l_buffer import l_buffer

async def cb():
  """Callback-Funktion."""
  pass
  #print('Das ist der Callback...')

async def producer(buffer):
  """Produziert Videoframes und sendet sie in den Buffer."""
  await buffer.check_in('P')
  cap = cv2.VideoCapture(0)
  if not cap.isOpened():
    print("Kamera nicht verfügbar")
    return
  #ret, frame = await asyncio.to_thread(cap.read)
  #frame = cv2.resize(frame, (2829, 2829))
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
    length = randint(100, 1000)
    while len(pi_str) < length:
      pi_str += str(i)
      if i == 9:
        i = 0
      else:  
        i += 1
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

async def producer_proc(buffer):
  await producer(buffer)

async def consumer_proc(buffer):
  await consumer(buffer)

async def main():
  ts = time()
  buffer = await l_buffer.init('OLNB')

  producer_process = Worker(target=producer_proc, args=(buffer,))
  consumer_process = Worker(target=consumer_proc, args=(buffer,))

  producer_process.start()
  consumer_process.start()

  await producer_process.join()
  print('Producer beendet...')
  await consumer_process.join()
  print('Consumer beendet...')
  print('Time:', time() - ts)

if __name__ == '__main__':
  mp.set_start_method("spawn", force=True)
  asyncio.run(main())

