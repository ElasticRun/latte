import gevent
import frappe
import asyncio
import aioredis
import pickle
import zlib
import signal
from uuid import uuid4
from frappe.app import _sites_path as SITES_PATH
from six import string_types
from gevent.pool import Pool as GeventPool
from sys import exit

loop = asyncio.get_event_loop()

GRACEFUL_SHUTDOWN_WAIT = 10

def start(queue, quiet):
    print(f'Starting Gevent worker on queue {queue}')
    loop.add_signal_handler(signal.SIGINT, graceful_shutdown)
    loop.add_signal_handler(signal.SIGTERM, graceful_shutdown)
    loop.run_until_complete(deque_and_enqueue(queue))

async def deque_and_enqueue(queue):
    async for task in fetch_jobs(queue):
        task.process_task()

def graceful_shutdown():
    print('Warm shutdown requested')
    graceful = Task.pool.join(timeout=GRACEFUL_SHUTDOWN_WAIT)
    print('Shutting down, Gracefully=', graceful)
    exit(0 if graceful else 1)

async def fetch_jobs(queue):
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
    finally:
        conn.close()
        await conn.wait_closed()

class Task(object):
    pool = GeventPool(50)
    def __init__(self, site, method, user, method_name, kwargs, **flags):
        self.id = str(uuid4())
        self.site = site
        self.method = method
        self.user = user
        if not method_name:
            if isinstance(method, string_types):
                method_name = method
            else:
                method_name = f'{self.method.__module__}.{self.method.__name__}'

        self.method_name = method_name
        self.kwargs = kwargs
        self.flags = flags

    def process_task(self):
        self.pool.add(gevent.spawn(runner, self))

def runner(task):
    frappe.init(site=task.site, sites_path=SITES_PATH)
    frappe.connect()
    frappe.local.lang = frappe.db.get_default('lang')
    frappe.db.connect()
    log = frappe.logger()
    if isinstance(task.method, string_types):
        task.method = frappe.get_attr(task.method)
    print(f"Executing function {task.method_name} as part of task execution, task pool size :=", len(task.pool))
    try:
        task.method(**task.kwargs)
        frappe.db.commit()
        print(f"Completed function execution for {task.method_name}, task pool size :=", len(task.pool))
    except:
        frappe.db.rollback()
        print(f"Failed function execution for {task.method_name}, task pool size :=", len(task.pool))
        frappe.log_error(title=task.method_name)
        raise
    finally:
        frappe.destroy()
