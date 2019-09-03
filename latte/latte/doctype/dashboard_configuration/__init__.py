
import frappe


@frappe.whitelist()
def run(dashboard_name=None, filters=None):
    if not dashboard_name:
        frappe.throw('Dashboard Name Required')

    dashboard_doc = frappe.get_doc('Dashboard Configuration', dashboard_name)

    if not dashboard_doc:
        frappe.throw('Dashboard %s not found', dashboard_name)

    dashboard_configuration_data = {
        'name': dashboard_name,
        'data_slice_data': [],
    }
    slice_data = []
    for data_slice in dashboard_doc.data_slices:
        sD = frappe.get_doc('Data Slice', data_slice.data_slice)
        slice_data.append({
            'name': data_slice.name,
            'data_slice_name': data_slice.data_slice,
            'data_type': sD.data_type,
            'dashboard_level': data_slice.dashboard_level,
            'html_content': sD.html_content,
            'priority': data_slice.priority,
            'result': sD.execute()
        })
    dashboard_configuration_data['data_slice_data'] = slice_data
    return dashboard_configuration_data
