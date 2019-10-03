import frappe
import time
import os
import gevent
import redis
from frappe.utils import cstr
from frappe.utils.background_jobs import queue_timeout, Queue
from frappe.app import _sites_path as SITES_PATH
from six import string_types
from types import FunctionType, MethodType
from functools import wraps
from uuid import uuid4
from gevent.pool import Pool as GeventPool

def enqueue(method, queue='default', timeout=None, event=None, monitor=True, set_user=None,
	method_name=None, is_async=True, job_name=None, now=False, enqueue_after_commit=False, **kwargs):
	'''
		Enqueue method to be executed using a background worker

		:param method: method string or method object
		:param queue: should be either long, default or short
		:param timeout: should be set according to the functions
		:param event: this is passed to enable clearing of jobs from queues
		:param is_async: if is_async=False, the method is executed immediately, else via a worker
		:param job_name: can be used to name an enqueue call, which can be used to prevent duplicate calls
		:param now: if now=True, the method is executed via frappe.call
		:param kwargs: keyword arguments to be passed to the method
	'''
	# To handle older implementations
	is_async = not not kwargs.pop('async', is_async)

	if queue == 'self':
		if not getattr(frappe.local, 'self_worker_compatible', None):
			queue = 'default'

	if now or frappe.flags.in_migrate:
		return frappe.call(method, **kwargs)

	if not timeout:
		timeout = queue_timeout.get(queue) or 300

	job_run_id = monitor and create_job_run(method, queue)

	queue_args = {
		"site": frappe.local.site,
		"user": set_user or frappe.session.user,
		"method": method,
		"method_name": method_name,
		"event": event,
		"job_name": job_name or cstr(method),
		"is_async": is_async,
		"job_run_id": job_run_id,
		"kwargs": kwargs,
		"queue": queue,
		"request_id": frappe.flags.request_id,
	}

	if enqueue_after_commit:
		if not frappe.flags.enqueue_after_commit:
			frappe.flags.enqueue_after_commit = []

		frappe.flags.enqueue_after_commit.append({
			"queue": queue,
			"is_async": is_async,
			"timeout": timeout,
			"queue_args": queue_args,
		})
		return frappe.flags.enqueue_after_commit
	else:
		if queue == 'self':
			return Task(**queue_args).process_task()

		return get_queue(queue, is_async).enqueue_call(
			execute_job,
			timeout=timeout,
			kwargs=queue_args,
		)

def enqueue_after_commit():
	for job in (frappe.flags.enqueue_after_commit or []):
		if job.get('queue') == 'self':
			Task(**job.get('queue_args')).process_task()

		else:
			get_queue(job['queue'], job['is_async']).enqueue_call(
				execute_job,
				timeout=job.get('timeout'),
				kwargs=job.get('queue_args'),
			)
	frappe.flags.enqueue_after_commit = []

def execute_job(site, method, event, job_name, kwargs,
	method_name=None, user=None, is_async=True, retry=0, job_run_id=None):
	'''Executes job in a worker, performs commit/rollback and logs if there is any error'''
	from frappe.utils.scheduler import log

	if is_async:
		frappe.connect(site)
		if os.environ.get('CI'):
			frappe.flags.in_test = True

		if user:
			frappe.set_user(user)

	if not method_name:
		if isinstance(method, string_types):
			method_name = method
			method = frappe.get_attr(method)
		else:
			method_name = cstr(method.__name__)

	if job_run_id:
		set_job_status(job_run_id, 'Started')
	try:
		method(**kwargs)
	except:
		frappe.db.rollback()
		set_job_status(job_run_id, 'Failure')
		log(method_name, message=repr(locals()))
		raise
	else:
		set_job_status(job_run_id, 'Success')
		frappe.db.commit()

	finally:
		if is_async:
			frappe.destroy()

def set_job_status(job_id, status):
	if not job_id:
		return
	frappe.db.set_value('Job Run', job_id, 'status', status)

def create_job_run(method, queue):
	if type(method) in (FunctionType, MethodType):
		method = f'{method.__module__}.{method.__name__}'
	else:
		method = str(method)

	if not frappe.get_all('Job Watchman', filters={
		'method': method,
	}):
		return

	doc = frappe.get_doc({
		'doctype': 'Job Run',
		'method': method,
		'title': method,
		'status': 'Enqueued',
		'enqueued_at': frappe.utils.now_datetime(),
		'queue_name': queue,
	})
	doc.db_insert()
	return doc.name

fn_map = {}
def background(**dec_args):
	if 'enqueue_after_commit' not in dec_args:
		dec_args['enqueue_after_commit'] = True
	def decorator(fn):
		key = f'{fn.__module__}.{fn.__name__}'
		fn_map[key] = fn
		def decorated(*pos_args, **kw_args):
			return enqueue(
				bg_runner,
				fn_key=key,
				method_name=key,
				pos_args=pos_args,
				kw_args=kw_args,
				**dec_args,
			)
		return decorated
	return decorator

def bg_runner(fn_key, pos_args, kw_args):
	if fn_key not in fn_map:
		frappe.get_attr(fn_key)
	fn_map.get(fn_key)(*pos_args, **kw_args)

class Task(object):
	pool = GeventPool(50)

	def __init__(self, site, method, user, method_name, kwargs, queue, job_run_id,
		request_id, **flags):
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
		self.queue = queue
		self.request_id = request_id
		self.job_run_id = job_run_id
		self.flags = flags

	def process_task(self):
		self.pool.add(gevent.spawn(fastrunner, self))

def fastrunner(task):
	frappe.local.self_worker_compatible = True
	frappe.init(site=task.site, sites_path=SITES_PATH)
	frappe.flags.request_id = task.request_id
	frappe.flags.task_id = str(uuid4())
	frappe.flags.runner_type = f'fastrunner-{task.queue}'
	frappe.connect()
	frappe.local.lang = frappe.db.get_default('lang')
	frappe.db.connect()
	log = frappe.logger()
	if isinstance(task.method, string_types):
		task.method = frappe.get_attr(task.method)
	log.debug(f"Executing function {task.method_name} as part of task execution, task pool size := {len(task.pool)}")
	try:
		task.method(**task.kwargs)
		frappe.db.commit()
		log.debug(f"Completed function execution for {task.method_name}, task pool size := {len(task.pool)}")
	except:
		frappe.db.rollback()
		log.debug(f"Failed function execution for {task.method_name}, task pool size := {len(task.pool)}")
		frappe.log_error(title=task.method_name)
		raise
	finally:
		frappe.destroy()

QUEUE_MAP = {}

def get_queue(queue, is_async):
	queue_async_map = QUEUE_MAP.setdefault(queue, {})

	try:
		return queue_async_map[is_async]
	except KeyError:
		queue_instance = queue_async_map[is_async] = Queue(queue, connection=get_redis_conn(), is_async=is_async)
		return queue_instance

redis_connection = None

def get_redis_conn():
	if not hasattr(frappe.local, 'conf'):
		raise Exception('You need to call frappe.init')

	elif not frappe.local.conf.redis_queue:
		raise Exception('redis_queue missing in common_site_config.json')

	global redis_connection

	if not redis_connection:
		redis_connection = redis.from_url(frappe.local.conf.redis_queue)

	return redis_connection