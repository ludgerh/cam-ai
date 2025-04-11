import cv2
import numpy as np
import asyncio
import mpmath
import multiprocessing as mp
from time import time
from aiomultiprocess import Worker
from random import randint
from l_buffer import l_buffer

async def cb():
  pass

async def producer(buffer):
  height, width = 800, 1400
  for i in range(100):
    frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    data = [
      {'eins': 1, 'zwei': 2, 'drei': 3},
      {'eins': 1, 'zwei': 2, 'drei': 3},
      frame
    ]
    pi_str = str(mpmath.pi)
    j = 0
    length = randint(100, 1000)
    while len(pi_str) < length:
      pi_str += str(j)
      if j == 9:
        j = 0
      else:
        j += 1
    pi_bytes = bytearray(pi_str.encode("utf-8"))
    data.append(pi_bytes)
    data.append(pi_bytes)
    await buffer.put(data)
  await buffer.put('stop')
  await buffer.stop('P')

async def consumer(buffer):
  while True:
    data = await buffer.get()
    if data == 'stop':
      break
    if data:
      cv2.imshow("Received Frame", data[2])
      cv2.waitKey(1)
      print(data[0], data[1], data[3], data[4])
  await buffer.stop('C')

async def producer_proc(buffer):
  await producer(buffer)

async def consumer_proc(buffer):
  await consumer(buffer)

async def main():
  ts = time()
  buffer = l_buffer('OLNB', debug=0)
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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
