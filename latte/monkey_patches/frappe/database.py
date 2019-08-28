import frappe
from frappe.database import Database
from json import dumps
from frappe.utils.background_jobs import enqueue
from six import string_types
import traceback
import sys
from io import StringIO

old_sql = Database.sql

def sql(self, query, values=(), *args, **kwargs):
    log_explain(query, values)
    return old_sql(self, query, values, *args, **kwargs)

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

Database.sql = sql