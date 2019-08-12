from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException, NotFound
from latte import _dict
from frappe.app import init_request, handle_exception, after_request
import frappe

from datetime import datetime

@Request.application
def application(request):
	response = None
	log_info = _dict()
	log_info.request_start = datetime.utcnow()
	try:
		rollback = True

		init_request(request)

		log_info.request_start = frappe.utils.convert_utc_to_user_timezone(log_info.request_start).replace(tzinfo=None)

		if frappe.local.form_dict.cmd:
			response = frappe.handler.handle()

		elif frappe.request.path.startswith("/api/"):
			if frappe.local.form_dict.data is None:
					frappe.local.form_dict.data = request.get_data(as_text=True)
			response = frappe.api.handle()

		elif frappe.request.path.startswith('/backups'):
			response = frappe.utils.response.download_backup(request.path)

		elif frappe.request.path.startswith('/private/files/'):
			response = frappe.utils.response.download_private_file(request.path)

		elif frappe.local.request.method in ('GET', 'HEAD', 'POST'):
			response = frappe.website.render.render()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except frappe.SessionStopped as e:
		response = frappe.utils.response.handle_session_stopped()

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = after_request(rollback)

	finally:
		if frappe.local.request.method in ("POST", "PUT") and frappe.db and rollback:
			frappe.db.rollback()

		# set cookies
		if response and hasattr(frappe.local, 'cookie_manager'):
			frappe.local.cookie_manager.flush_cookies(response=response)

		log_info.request_end = frappe.utils.now_datetime()
		log_info.turnaround_time = (log_info.request_end - log_info.request_start).total_seconds()
		log_info.cmd = frappe.local.form_dict.cmd
		frappe.logger().debug(log_info)
		frappe.destroy()

	return response