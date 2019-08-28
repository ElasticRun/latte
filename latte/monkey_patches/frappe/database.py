import frappe
import traceback
from frappe.database import Database
from io import StringIO
from latte.utils.background.job import execute_job

old_sql = Database.sql

def sql(self, query, values=(), *args, **kwargs):
    log_explain(query, values)
    return old_sql(self, query, values, *args, **kwargs)

Database.sql = sql

def log_explain(query, values):
    query_type = query.strip()[:6].lower()
    if frappe.local.conf.log_level == "sql_debug" and query_type in ('select', 'update',):
        output_stream = StringIO()
        traceback.print_stack(file=output_stream)
        stack_trace = output_stream.getvalue().split('\n')
        output_stream.close()
        try:
            explanation = frappe.db.sql(f'explain {query}', values or (), as_dict=1)
            frappe.logger().debug(frappe.as_json({
                'stack': stack_trace,
                'query': query,
                'params': values,
                'type': 'query_debug',
                'explanation': explanation,
            }))
        except Exception as e:
            print(query, values, e)


old_commit = Database.commit

def commit(self):
    enqueue_after_commit()
    old_commit(self)

Database.commit = commit

def enqueue_after_commit():
    for job in (frappe.flags.enqueue_after_commit or []):
        job.get('q').enqueue_call(
            execute_job,
            timeout=job.get('timeout'),
            kwargs=job.get('queue_args'),
        )
    frappe.flags.enqueue_after_commit = []