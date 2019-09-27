from __future__ import unicode_literals
import frappe
from frappe.utils import cint
from frappe import _

def create_enable_disable_log(ref_doctype, ref_name, disabled, reason, processed):
    frappe.get_doc({
    'doctype': 'Enable Disable Reason Log',
    'ref_name': ref_name,
    'ref_doctype': ref_doctype,
    'disabled': disabled,
    'reason': reason,
    'processed': processed,
    }).insert(ignore_permissions=True)

@frappe.whitelist()
def apply_doc_status_tracker(ref_doctype, docname, reason=None, disabled=None):
    frappe.get_doc({
    'doctype': 'Communication',
    'reference_name': docname,
    'reference_doctype': ref_doctype,
    'communication_type': 'Comment',
    'comment_type': 'Workflow',
    'content': f"""Doc updated reason: <b>{reason or ''}</b>""",
    }).insert(ignore_permissions=True)

    frappe.utils.background_jobs.enqueue(
        create_enable_disable_log,
		queue='default',
		enqueue_after_commit=True,
        ref_doctype=ref_doctype,
        ref_name=docname,
        disabled=disabled,
        reason=reason,
        processed=1
	)

    return

@frappe.whitelist()
def get_enable_disable_reason(doctype, txt, searchfield, start, page_len, filters):
    if filters and filters.get('disabled') == 1:
        query = """select dri.disable_reason as name
        from
            `tabDisable Reason Item` dri
        join
            `tabDoc Status Tracker` dst
        on
            dst.name = dri.parent
        where
            dri.disable_reason like '{txt}'
            and dri.parenttype = 'Doc Status Tracker'
            and dst.document_type = '{doctype}'
        """.format(txt = frappe.db.escape('%{0}%'.format(txt)), doctype=filters.get('doctype'), debug=1)
    else:
        query = """select eri.enable_reason as name
        from
            `tabEnable Reason Item` eri
        join
            `tabDoc Status Tracker` dst
        on
            dst.name = eri.parent
        where
            eri.enable_reason like '{txt}'
            and eri.parenttype='Doc Status Tracker'
            and dst.document_type = '{doctype}'
        """.format(txt = frappe.db.escape('%{0}%'.format(txt)), doctype=filters.get('doctype'), debug=1)

    return frappe.db.sql(query)
