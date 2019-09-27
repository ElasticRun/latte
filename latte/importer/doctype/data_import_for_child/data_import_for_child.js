// Copyright (c) 2019, Sachin Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Data Import For Child', {
	onload: function(frm) {
		if(frm.doc.__islocal) {
			frm.set_value("action", "");
		}

		frm.set_query("reference_doctype", function() {
			return {
				"filters": {
					"issingle": 0,
					"istable": 0,
					"name": ['in', frappe.boot.user.can_import]
				}
			};
		});

		// should never check public

		frm.fields_dict["import_file"].df.is_private = 1;

	},
	refresh: function(frm) {
		frm.add_custom_button(__("Download template"), function() {
			let get_template_url = '/api/method/latte.importer.doctype.data_import_for_child.child_import_export.export_data';
			open_url_post(get_template_url, {'doctype': frm.doc.reference_doctype, 'child_doc': frm.doc.child_document_type});
		});

		frm.disable_save();
		frm.dashboard.clear_headline();
		if (frm.doc.reference_doctype && !frm.doc.import_file) {
			frm.page.set_indicator(__('Attach file'), 'orange');
		} else {
			if (frm.doc.import_status) {
				const listview_settings = frappe.listview_settings['Data Import For Child'];
				const indicator = listview_settings.get_indicator(frm.doc);

				frm.page.set_indicator(indicator[0], indicator[1]);

				if (frm.doc.import_status === "In Progress") {
					frm.dashboard.add_progress("Data Import For Child Progress", "0");
					frm.set_read_only();
					frm.refresh_fields();
				}
			}
		}

		if (frm.doc.reference_doctype && frm.doc.import_file &&
			frm.doc.docstatus === 0 && (!frm.doc.import_status || frm.doc.import_status == "Failed")) {
			frm.page.set_primary_action(__("Start Import"), function() {
				frappe.call({
					method: "latte.importer.doctype.data_import_for_child.data_import_for_child.import_data_for_child",
					args: {
						data_import: frm.doc.name
					}
				});
			}).addClass('btn btn-primary');
		}

		if (frm.doc.log_details) {
			frm.events.create_log_table(frm);
		} else {
			$(frm.fields_dict.import_log.wrapper).empty();
		}

		var help_content =`<table class="table table-bordered" style="background-color: #f9f9f9;">
			<tr><td>
				<h4>
					<i class="fa fa-hand-right"></i>
					${__('Notes')}
				</h4>
				<ul>
					<li>
						${__("Use Download Template for Data Import Excel Template<br>")}
					
						${__("Document Type and Child Document Type is mandatory")}
					</li>
					<li>
						${__("Action: Append new records will append records in Child Document")}
					</li>
				</ul>
			</td></tr>
		</table>`;

		set_field_options("html_note", help_content);

	},
	action: function(frm) {
		if(!frm.doc.action) return;
		if(!frm.doc.reference_doctype) {
			frappe.msgprint(__("Please select document type first."));
			frm.set_value("action", "");
			return;
		}

		if(frm.doc.action == "Append new records") {
			frm.doc.insert_new = 1;
		} else if (frm.doc.action == "Update records"){
			frm.doc.overwrite = 1;
		}
		frm.save();
	},
	create_log_table: function(frm) {
		let msg = JSON.parse(frm.doc.log_details);
		var $log_wrapper = $(frm.fields_dict.import_log.wrapper).empty();
		$(frappe.render_template("log_details", {
			data: msg.messages,
			import_status: frm.doc.import_status,
			show_only_errors: frm.doc.show_only_errors,
		})).appendTo($log_wrapper);
	}
});
