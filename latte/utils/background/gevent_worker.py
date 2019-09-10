import gevent
from gevent import monkey
monkey.patch_all()
import frappe
import asyncio
import aioredis
import pickle
import zlib
from uuid import uuid4
from frappe.app import _sites_path as SITES_PATH

loop = asyncio.get_event_loop()

def start(queue, quiet):
    print(f'Starting Gevent worker on queue {queue}')
    loop.run_until_complete(deque_and_enqueue(queue))

async def deque_and_enqueue(queue):
    try:
        print('Connecting')
        conn = await aioredis.create_connection('redis://localhost:11000', loop=loop)
        print('Connected')
        async for task in fetch_jobs(conn, queue):
            task.process_task()
    finally:
        conn.close()
        await conn.wait_closed()

async def fetch_jobs(conn, queue):
    while True:
        print('Fetching')
        job_id = str((await conn.execute('blpop', f'rq:queue:{queue}', 0))[1], 'utf-8')
        job_meta = await conn.execute('hgetall', f'rq:job:{job_id}')
        print('Fetched')
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

class Task(object):
    def __init__(self, site, method, user, method_name, kwargs, **_):
        self.id = str(uuid4())
        self.site = site
        self.method = method
        self.user = user
        self.method_name = method_name or f'{self.method.__module__}.{self.method.__name__}'
        self.kwargs = kwargs

    def process_task(self):
        # TODO: Implement pooling logic here
        gevent.spawn(runner, self)

def runner(task):
    frappe.init(site=task.site, sites_path=SITES_PATH)
    frappe.connect()
    frappe.local.lang = frappe.db.get_default('lang')
    frappe.db.connect()
    log = frappe.logger()
    log.debug(f"Executing function {task.method_name} as part of task execution")
    try:
        task.method(**task.kwargs)
        frappe.db.commit()
    except:
        frappe.db.rollback()
        raise
    finally:
        frappe.destroy()
    log.debug(f"Completed function execution for {task.method_name}")
