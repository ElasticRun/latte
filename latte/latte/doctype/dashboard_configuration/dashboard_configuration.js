// Copyright (c) 2019, Sachin Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dashboard Configuration', {
	refresh: function (frm) {
		frm.add_custom_button(__("Show Dashboard"), () => frappe.set_route('wr-dashboard', frm.doc.name));
	}
});
