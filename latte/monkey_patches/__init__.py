import latte.monkey_patches.whitelist
import latte.monkey_patches.frappe.utils.logger
import latte.monkey_patches.frappe.database
import frappe.utils.background_jobs
from latte.utils.background.job import enqueue
frappe.utils.background_jobs.enqueue = enqueue