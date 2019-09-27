// Copyright (c) 2019, Sachin Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dashboard Data Slice', {
	refresh: function(frm) {
		frm.trigger('update_displays');
	},
	data_type: function(frm) {
		
		frm.trigger('remove_all_set');
		frm.trigger('update_displays');
	},
	data_source: function(frm) {
		frm.trigger('update_displays');
	},
	report: function(frm) {
		frm.trigger('update_options');
	},
	remove_all_set: function(frm) {
		frm.set_value('data_source', '');
		frm.set_value('report', '');
		frm.set_value('report_count_position', '');
		frm.set_value('report_count_label', '');
		frm.set_value('report_count_background_color', '');
		frm.set_value('report_count_color', '');
		frm.set_value('method', '');
		frm.set_value('filter', '');
		frm.set_value('filter_field', '');
		frm.set_df_property('report', 'hidden', 1);
		frm.set_df_property('report_count_position', 'hidden', 1);
		frm.set_df_property('report_count_label', 'hidden', 1);
		frm.set_df_property('report_count_background_color', 'hidden', 1);
		frm.set_df_property('report_count_color', 'hidden', 1);
		frm.set_df_property('method', 'hidden', 1);
		frm.set_df_property('filter_field', 'hidden', 1);
	},
	update_displays: function(frm) {
		if (!frm.doc.data_source) {
			frm.set_df_property("report", "hidden", 1);
			frm.set_df_property("report_count_position", "hidden", 1);
			frm.set_df_property('report_count_label', 'hidden', 1);
			frm.set_df_property('report_count_background_color', 'hidden', 1);
			frm.set_df_property('report_count_color', 'hidden', 1);
			frm.set_df_property("method", "hidden", 1);
		} else if (frm.doc.data_source === 'Report') {
			frm.set_df_property("report", "hidden", 0);
			if (frm.doc.data_type === 'Count') {
				frm.set_df_property("report_count_position", "hidden", 0);
				frm.set_df_property('report_count_label', 'hidden', 0);
				frm.set_df_property('report_count_background_color', 'hidden', 0);
				frm.set_df_property('report_count_color', 'hidden', 0);
			} else {
				frm.set_df_property("report_count_position", "hidden", 1);
				frm.set_df_property('report_count_label', 'hidden', 1);
				frm.set_df_property('report_count_background_color', 'hidden', 1);
				frm.set_df_property('report_count_color', 'hidden', 1);
				frm.set_df_property("method", "hidden", 1);
			}
		} else if (frm.doc.data_source === 'Method') {
			frm.set_df_property("method", "hidden", 0);
			frm.set_df_property("report_count_position", "hidden", 0);
			frm.set_df_property('report_count_label', 'hidden', 0);
			frm.set_df_property('report_count_background_color', 'hidden', 0);
			frm.set_df_property('report_count_color', 'hidden', 0);
			frm.set_df_property("report", "hidden", 0);
		}
		if (frm.doc.data_type === 'Filter') {
			frm.set_df_property('filter', 'hidden', 1);
			frm.set_df_property('filter_field', 'hidden', 0);
		} else {
			frm.set_df_property('filter', 'hidden', 0);
			frm.set_df_property('filter_field', 'hidden', 1);
		}
	}
});
