# Copyright (c) 2013, ElasticRun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from croniter import croniter
from datetime import datetime
import pandas as pd
from datetime import timedelta
import pytz

def execute(filters=None, as_df=False):
	filters = filters or {}
	run_date = filters.get('run_date', frappe.utils.nowdate())
	status = filters.get('status')
	frappe.cache().flushall()
	hooks = frappe.get_hooks('scheduler_events')
	events = hooks.get('daily') + hooks.get('daily_long')
	all_jobs = []
	for event in events:
		all_jobs.append(['0 0 * * *', event])
	for key, jobs in hooks.get('cron').items():
		for row in jobs:
			all_jobs.append([key, row])
	now = frappe.utils.now_datetime()
	filtered_jobs = []
	ensure_run_for = frappe.get_all('Job Watchman', fields=['method', 'expected_run_time'])
	ensure_run_for = {
		row.method: row for row in ensure_run_for
	}
	'''
	[
		expected_status,
		actual_status,
		expected_start,
		actual_start,
	]
	'''
	method_names = set()
	for cron_config, job in all_jobs:
		if job not in ensure_run_for:
			continue
		method_names.add(job)
		# job_line = frappe._dict()
		# status_line = [''] * 4
		status_line = frappe._dict()

		prev_run = croniter(cron_config, now).get_prev(datetime)
		status_line.method = job

		if str(prev_run.date()) == str(now.date()):
			status_line.expected_status = 'Scheduled'
			status_line.expected_start = prev_run
			status_line.expected_finish = prev_run + timedelta(minutes=ensure_run_for.get(job).expected_run_time)
		else:
			next_run = croniter(cron_config, now).get_next(datetime)
			if str(next_run.date()) == str(now.date()):
				status_line.expected_status = 'Will be scheduled'
			else:
				status_line.expected_status = 'Not Scheduled for Today'

		filtered_jobs.append(status_line)

	job_df = pd.DataFrame.from_records(filtered_jobs, index=['method'])
	run_status = pd.read_sql(f'''
		SELECT
			name as job_run_id,
			method,
			queue_name,
			status,
			enqueued_at,
			started,
			finished
		from
			`tabJob Run`
		where
			method in %(methods)s
			and run_date = %(date)s
	''', params={
		'methods': list(method_names),
		'date': run_date,
	}, con=frappe.db._conn, index_col=['method'])
	report_df = job_df.merge(run_status, on='method', how='left')

	if as_df:
		return report_df

	report_df.fillna(0, inplace=True)
	if status:
		report_df = report_df[report_df.status == status]

	# print(frappe.as_json(filtered_jobs))
	return [
		'Job Name::300',
		'Queue::150',
		'Expected Status::200',
		'Actual Status::200',
		'Expected Start::200',
		'Actual Start::200',
		'Expected End::200',
		'Actual End::200',
	], list(zip(
		report_df.index,
		report_df.queue_name,
		report_df.expected_status,
		report_df.status,
		report_df.expected_start.apply(lambda x: x.strftime("%H:%M") if isinstance(x, datetime) else x),
		report_df.started.apply(lambda x: x.strftime("%H:%M") if isinstance(x, datetime) else x),
		report_df.expected_finish.apply(lambda x: x.strftime("%H:%M") if isinstance(x, datetime) else x),
		report_df.finished.apply(lambda x: x.strftime("%H:%M") if isinstance(x, datetime) else x),
	))