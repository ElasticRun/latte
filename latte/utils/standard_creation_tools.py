import frappe
from frappe.modules.export_file import export_to_files as _export_to_files

def export_to_files(doc):
    if (
        doc.is_standard
        and doc.module
        and frappe.local.conf.developer_mode
        and (not frappe.flags.in_migrate)
    ):
        _export_to_files(
            record_list=[[doc.doctype, doc.name]],
            record_module=doc.module,
            create_init=True,
        )
