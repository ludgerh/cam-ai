import cv2
import numpy as np
import asyncio
import mpmath
import random
from time import time
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
    i = 0
    length = random.randint(100, 1000)
    while len(pi_str) < length:
      pi_str += str(i)
      i = (i + 1) % 10
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

async def main():
  ts = time()
  buffer = l_buffer('OLNB', m_proc=False)
  # Run producer and consumer concurrently in the same event loop
  producer_task = asyncio.create_task(producer(buffer))
  consumer_task = asyncio.create_task(consumer(buffer))
  await producer_task
  print('Producer beendet...')
  await consumer_task
  print('Consumer beendet...')
  print('Time:', time() - ts)

if __name__ == '__main__':
  asyncio.run(main())

