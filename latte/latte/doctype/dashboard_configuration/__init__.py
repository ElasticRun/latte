
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
    dashboard_slice_data = []
    for dashboard_data_slice in dashboard_doc.dashboard_data_slices:
        data_slice = frappe.get_doc('Dashboard Data Slice', dashboard_data_slice.dashboard_data_slice)
        dash_level = frappe.get_doc('Dashboard Level', dashboard_data_slice.dashboard_level)

        dashboard_slice_data.append({
            'dashboard_name': dashboard_data_slice.name,
            'data_slice_name': data_slice.data_slice_name,
            'data_type': data_slice.data_type,
            'data_source': data_slice.data_source,
            'dash_level': dash_level,
            'result': data_slice.execute(filters)
        })
    dashboard_configuration_data['data_slice_data'] = dashboard_slice_data
    return dashboard_configuration_data    
