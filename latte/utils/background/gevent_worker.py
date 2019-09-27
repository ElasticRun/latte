import frappe

import asyncio
import signal

import aioredis, pickle, zlib

from six import string_types
from sys import exit
from latte.utils.background.job import Task

loop = asyncio.get_event_loop()

GRACEFUL_SHUTDOWN_WAIT = 10

def start(queue, quiet):
    print(f'Starting Gevent worker on queue {queue}')
    loop.add_signal_handler(signal.SIGINT, graceful_shutdown)
    loop.add_signal_handler(signal.SIGTERM, graceful_shutdown)
    loop.run_until_complete(deque_and_enqueue(queue))

async def deque_and_enqueue(queue):
    async for task in fetch_jobs_from_redis(queue, loop):
        task.process_task()

def graceful_shutdown():
    print('Warm shutdown requested')
    graceful = Task.pool.join(timeout=GRACEFUL_SHUTDOWN_WAIT)
    print('Shutting down, Gracefully=', graceful)
    exit(0 if graceful else 1)

async def fetch_jobs_from_redis(queue, loop):
    try:
        print('Connecting')
        conn = await aioredis.create_connection('redis://localhost:11000', loop=loop)
        print('Connected')
        while True:
            job_id = str((await conn.execute('blpop', f'rq:queue:{queue}', 0))[1], 'utf-8')
            job_meta = await conn.execute('hgetall', f'rq:job:{job_id}')
            # print('Fetched')
            job_dict = frappe._dict()
            for idx, data in enumerate(job_meta):
                try:
                    job_meta[idx] = str(data, 'utf-8')
                except UnicodeDecodeError:
                    job_meta[idx] = data
            for i in range(0, len(job_meta), 2):
                job_dict[job_meta[i]] = job_meta[i + 1]

            _, _, _, job_kwargs = pickle.loads(zlib.decompress(job_dict.data))
            yield Task(**job_kwargs)
            await conn.execute('del', f'rq:job:{job_id}')
    finally:
        conn.close()
        await conn.wait_closed()