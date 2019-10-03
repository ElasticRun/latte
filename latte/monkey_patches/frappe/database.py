import frappe
import traceback
from frappe.database import Database
from io import StringIO
from latte.utils.background.job import enqueue_after_commit
from latte.database_utils.connection_pool import PooledDatabase

old_sql = Database.sql

def sql(self, query, values=(), *args, **kwargs):
	log_explain(query, values)
	return old_sql(self, query, values, *args, **kwargs)

if Database.sql is not sql:
	Database.sql = sql
	Database.unpatched_sql = old_sql

def log_explain(query, values):
	sql_log_verbosity = frappe.local.conf.sql_log_verbosity
	if not sql_log_verbosity:
		return

	output_stream = StringIO()
	traceback.print_stack(file=output_stream)
	stack_trace = output_stream.getvalue().split('\n')
	output_stream.close()

	query_type = query.strip()[:6].lower()

	log_dict = {
		'stack': stack_trace,
		'query': query,
		'params': values,
		'log_verbosity': sql_log_verbosity,
		'type': 'query_debug',
	}

	if sql_log_verbosity == 'explain':
		if query_type not in ('select', 'update', 'delete'):
			return

		try:
			explanation = frappe.db.unpatched_sql(f'explain {query}', values or (), as_dict=1)
			log_dict['explanation'] = explanation
			frappe.logger().debug(log_dict)
		except Exception as e:
			print(query, values, e)
		return
	elif sql_log_verbosity == 'analyze':
		if query_type not in ('select',):
			return

		frappe.utils.background_jobs.enqueue(
			log_analyze_wrapper,
			log_dict=log_dict,
			queue='self',
			monitor=False,
		)
		return

def log_analyze_wrapper(log_dict):
	try:
		log_analyze(log_dict)
	except Exception as e:
		print(e)

def log_analyze(log_dict):
	analysis_db_host = frappe.local.conf.analysis_db_host
	analysis_db_user = frappe.local.conf.analysis_db_user
	analysis_db_password = frappe.local.conf.analysis_db_password
	logger = frappe.logger()
	if not analysis_db_host:
		logger.debug('No analysis host defined but sql_log_verbosity is set to analyze')
		return

	query = log_dict['query']
	values = log_dict['params']

	db = PooledDatabase(
		host=analysis_db_host,
		user=analysis_db_user,
		password=analysis_db_password,
		db_name=frappe.local.conf.db_name,
	)
	try:
		analysis = db.unpatched_sql(f'analyze {query}', values or (), as_dict=True)
		log_dict['analysis'] = analysis
		logger.debug(log_dict)
	finally:
		db.close()

old_commit = Database.commit

def commit(self):
	enqueue_after_commit()
	old_commit(self)

Database.commit = commit