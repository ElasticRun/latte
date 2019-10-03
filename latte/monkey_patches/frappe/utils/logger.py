import frappe
import frappe.utils.logger
import uuid
import logging
from logging.handlers import RotatingFileHandler
from pygelf import GelfUdpHandler
from six import string_types
from frappe.model.document import Document

old_get_logger = frappe.utils.logger.get_logger

class CustomAttributes(logging.Filter):
	def __init__(self, *args, modulename=None, **kwargs):
		self.__module = modulename
		super().__init__(*args, **kwargs)

	def filter(self, record):
		message = frappe._dict()
		logged_msg = record.msg
		# print(logged_msg)

		if isinstance(logged_msg, dict):
			message.update(logged_msg)
		elif isinstance(logged_msg, Document):
			message.update(logged_msg.as_dict())
		else:
			message['info'] = logged_msg

		frappe.local.flags.request_id_number = (frappe.local.flags.request_id_number or 0) + 1

		request_id = frappe.flags.request_id

		if not request_id:
			request_id = frappe.flags.request_id = str(uuid.uuid4())

		message.request_id = request_id
		message.task_id = frappe.flags.task_id
		message.runner_type = frappe.flags.runner_type
		message.module = self.__module
		message.log_number = frappe.local.flags.request_id_number
		message.site = getattr(frappe.local, 'site', None)

		# WARNING: Dangerous if PII is present in system.
		message.session = frappe.session

		record.msg = frappe.as_json(message, indent=None)

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
	logger.addFilter(CustomAttributes(modulename=module))

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
	# formatter = logging.Formatter('%(message)s')
	# handler.setFormatter(formatter)
	return logger


def get_gelf_handler():
	gelf_config = frappe.local.conf.gelf_config
	if not gelf_config:
		return

	gelf_gelf_host = gelf_config.get('host', '127.0.0.1')
	gelf_gelf_port = gelf_config.get('port', 32000)
	return GelfUdpHandler(host=gelf_gelf_host, port=gelf_gelf_port, include_extra_fields=True)

frappe.utils.logger.get_logger = get_logger
