import frappe
import frappe.utils.logger
import uuid
import logging
from logging.handlers import RotatingFileHandler
from pygelf import GelfUdpHandler
from six import string_types

old_get_logger = frappe.utils.logger.get_logger

class CustomAttributes(logging.Filter):
	def __init__(self, *args, modulename=None, **kwargs):
		self.__module = modulename
		super().__init__(*args, **kwargs)

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
		record.module = self.__module
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
	logger.__patched = True

	logger_type = frappe.local.conf.logger_type
	logger.addFilter(CustomAttributes(module))

	handler = None
	if logger_type != 'file':
		handler = get_gelf_handler()
	if not handler:
		handler = RotatingFileHandler(
			'../logs/frappe.log',
			maxBytes=100 * 1024 * 1024,
			backupCount=10,
		)

	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)
	logger.propagate = True
	formatter = logging.Formatter('%(message)s')
	handler.setFormatter(formatter)
	return logger


def get_gelf_handler():
	gelf_config = frappe.local.conf.gelf_config
	if not gelf_config:
		return

	gelf_gelf_host = gelf_config.get('host', '127.0.0.1')
	gelf_gelf_port = gelf_config.get('port', 32000)
	return GelfUdpHandler(host=gelf_gelf_host, port=gelf_gelf_port, include_extra_fields=True)

frappe.utils.logger.get_logger = get_logger
