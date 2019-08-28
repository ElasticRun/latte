import frappe
import time
import os
from frappe.utils import cstr
from frappe.utils.background_jobs import get_queue, queue_timeout
from six import string_types

def enqueue(method, queue='default', timeout=None, event=None, job_run_id=None,
	is_async=True, job_name=None, now=False, enqueue_after_commit=False, **kwargs):
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
	is_async = kwargs.pop('async', is_async)

	if now or frappe.flags.in_migrate:
		return frappe.call(method, **kwargs)

	q = get_queue(queue, is_async=is_async)
	if not timeout:
		timeout = queue_timeout.get(queue) or 300
	queue_args = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"method": method,
		"event": event,
		"job_name": job_name or cstr(method),
		"is_async": is_async,
		"job_run_id": job_run_id,
		"kwargs": kwargs
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
		return q.enqueue_call(execute_job, timeout=timeout,
			kwargs=queue_args)

def execute_job(site, method, event, job_name, kwargs, user=None, is_async=True, retry=0, job_run_id=None):
	'''Executes job in a worker, performs commit/rollback and logs if there is any error'''
	from frappe.utils.scheduler import log

	if is_async:
		frappe.connect(site)
		if os.environ.get('CI'):
			frappe.flags.in_test = True

		if user:
			frappe.set_user(user)

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
	frappe.set_value('Job Run', job_id, 'status', status)
