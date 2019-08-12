import frappe
import frappe.utils.logger
import logging
from pygelf import GelfUdpHandler
import uuid
from six import string_types

old_get_logger = frappe.utils.logger.get_logger

class CustomAttributes(logging.Filter):
	def filter(self, record):
		if frappe.local.conf.log_level == "debug":
			print(record.msg)

		if not isinstance(record.msg, string_types):
			record.msg = frappe.as_json(record.msg)
		request_id = None
		frappe.local.flags.request_id_number = (frappe.local.flags.request_id_number or 0) + 1
		if hasattr(frappe.local, 'request'):
			request_id = frappe.local.request.headers.get('X-Request-Id')
			record.request_id_type = 'From Header'

		if not request_id:
			request_id = frappe.flags.request_id
			record.request_id_type = 'From Flag'

		if not request_id:
			request_id = frappe.flags.request_id = str(uuid.uuid4())
			record.request_id_type = 'Created'

		record.request_id = request_id
		record.log_number = frappe.local.flags.request_id_number
		record.site = getattr(frappe.local, 'site', None)

		# WARNING: Dangerous if PII is present in system.
		record.session = frappe.session

		return True

def get_logger(module, with_more_info=False):
	# logger = old_get_logger(module, False)
	if module in frappe.loggers:
		return frappe.loggers[module]

	logger = logging.getLogger(module)
	frappe.loggers[module] = logger

	if getattr(logger, '__patched', None):
		return logger

	logstash_config = frappe.local.conf.logstash
	if not logstash_config:
		return logger

	logstash_gelf_host = logstash_config.get('host', '127.0.0.1')
	logstash_gelf_port = logstash_config.get('port', 32000)
	gelf_handler = GelfUdpHandler(host=logstash_gelf_host, port=logstash_gelf_port, include_extra_fields=True)
	logger.__patched = True
	logger.addFilter(CustomAttributes())
	logger.addHandler(gelf_handler)
	logger.setLevel(logging.DEBUG)
	logger.propagate = True
	formatter = logging.Formatter('%(message)s')
	gelf_handler.setFormatter(formatter)
	return logger

frappe.utils.logger.get_logger = get_logger
