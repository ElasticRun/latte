# -*- coding: utf-8 -*-
# Copyright (c) 2019, ElasticRun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from latte.latte_core.naming.autoname import lockless_autoname
from latte.utils.indexing import create_index
from latte.latte_core.report.executed_background_jobs.executed_background_jobs \
	import execute as get_scheduled_jobs
import pandas as pd
from frappe.utils.background_jobs import get_jobs, enqueue
from latte.utils.background.job import create_job_run

class JobRun(Document):
	def autoname(self):
		self.naming_series = 'JRUN-.#######'
		return lockless_autoname(self)

	def before_save(self):
		self.run_date = frappe.utils.nowdate()
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and self.status != doc_before_save.status:
			if self.status == 'Started':
				self.started = frappe.utils.now_datetime()
			elif self.status == 'Failure' or self.status == 'Success':
				self.finished = frappe.utils.now_datetime()

def on_doctype_update():
	create_index('tabJob Run', ['method', 'run_date'])

def ensure_job_run():
	jobs = get_scheduled_jobs(as_df=True)
	now = frappe.utils.now_datetime()
	failed_jobs = jobs[jobs.status == 'Failure']
	unfinished_jobs = jobs[jobs.expected_finish < now]
	if not unfinished_jobs.empty:
		unfinished_jobs = unfinished_jobs[unfinished_jobs.status == 'Started']
	to_retry = pd.concat([failed_jobs, unfinished_jobs])
	site_name = frappe.local.site
	running_jobs = set([job for job in (get_jobs(site=site_name).get(site_name) or []) if job in to_retry.index.values])
	for method, row in to_retry.iterrows():
		frappe.set_value('Job Run', row.job_run_id, 'status', 'Retried')
		if method in running_jobs:
			continue
		running_jobs.add(method)
		retry_job(method, row.queue_name)

def retry_job(method, queue):
	job_run_id = create_job_run(queue, method)
	enqueue(method, queue, job_run_id=job_run_id)

# def test():
# 	frappe.db.sql('delete from `tabJob Run`')
# 	sys = frappe.get_doc("System Settings")
# 	sys.scheduler_last_event = "2019-02-03 09:24:33"
# 	sys.save()
# 	frappe.db.commit()
# 	frappe.get_attr('frappe.utils.scheduler.enqueue_events_for_all_sites')()

def remove_old_logs():
	frappe.db.sql('delete from `tabJob Run` where run_date <= %(today)s - interval 4 day', {
		'today': frappe.utils.nowdate(),
	})
	frappe.db.commit()