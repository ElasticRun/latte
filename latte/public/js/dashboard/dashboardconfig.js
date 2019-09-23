import DataTable from 'frappe-datatable';

// frappe.provide("latte.dashboard")

latte.DataTable = DataTable;
// latte.Dashboard1 = class GenericDashboard {
// 	constructor(wrapper) {
// 		const that = this;
// 		// debugger
// 		this.wrapper = $(wrapper);
// 		$(`<div class="dashboard">
// 			<div class="dashboard-graph row"></div>
// 		</div>`).appendTo(this.wrapper.find(".page-content"));
// 		// Changing margin to 0px
// 		$('.row.layout-main .layout-main-section-wrapper').css({'margin':'0px'});

// 		this.container = this.wrapper.find(".dashboard-graph");
// 		this.page = wrapper.page;
// 		this.page.set_primary_action(
// 			__('Refresh'),
// 			() => { me.reload(); }, 'icon-refresh',
// 		);
// 	}

// 	show() {
// 		this.route = frappe.get_route();
// 		if (this.route.length > 1) {
// 			// from route
// 			this.show_dashboard(this.route.slice(-1)[0]);
// 		} else {
// 			// last opened
// 			if (frappe.last_dashboard) {
// 				frappe.set_route('dashboard', frappe.last_dashboard);
// 			} else {
// 				// default dashboard
// 				frappe.db.get_list('Dashboard Configuration', {filters: {is_default: 1}}).then(data => {
// 					if (data && data.length) {
// 						frappe.set_route('dashboard', data[0].name);
// 					} else {
// 						// no default, get the latest one
// 						frappe.db.get_list('Dashboard Configuration', {limit: 1}).then(data => {
// 							if (data && data.length) {
// 								frappe.set_route('dashboard', data[0].name);
// 							} else {
// 								// create a new dashboard!
// 								frappe.new_doc('Dashboard Configuration');
// 							}
// 						});
// 					}
// 				});
// 			}
// 		}
// 	}


// 	show_dashboard(current_dashboard_name) {
// 		if(this.dashboard_name !== current_dashboard_name) {
// 			this.dashboard_name = current_dashboard_name;
// 			let title = this.dashboard_name;
// 			if (!this.dashboard_name.toLowerCase().includes(__('dashboard'))) {
// 				// ensure dashboard title has "dashboard"
// 				title = __('{0} Dashboard', [title]);
// 			}
// 			this.page.set_title(title);
// 			//this.set_dropdown();
// 			this.container.empty();
// 			this.refresh();
// 		}
// 		this.charts = {};
// 		frappe.last_dashboard = current_dashboard_name;
// 	}

// 	refresh() {
// 		var that = this;	
// 		this.get_dashboard_doc().then((doc) => {
// 			this.dashboard_doc = doc
// 			this.dashboard_data_slices = this.dashboard_doc.dashboard_data_slices;
// 			if (this.container.children().length > 0)
// 				this.container.children().empty();
// 			this.fetch_all().then((data) => {
// 				this.data = data;
// 				this.data.data_slice_data.map((slice) => {
// 					let slice_container = $('#row'+slice.dash_level.position);
// 					// Will make Rows based on 
// 				 	if (slice.dash_level && slice.dash_level.name && slice_container.length <= 0) {
// 				 		slice_container = $(`<div id="row${slice.dash_level.position}" class="row"></div>`);
// 						 slice_container.appendTo(this.container);
// 						 if (slice.dash_level.height)
// 						 	$(slice_container).css({"height": slice.dash_level.height, 'overflow-y': 'auto'});
// 					}
// 					frappe.model.with_doc("Dashboard Data Slice", slice.data_slice_name).then( slice_doc => {
// 						let slice_data = data.data_slice_data.filter((dt) => dt.data_slice_name == slice_doc.name);			
// 						let slice = new latte.Dashboard.DataSlice(slice_doc, slice_container, 
// 						  		undefined != slice_data && slice_data.length > 0 ? slice_data[0].result: undefined);
// 						slice.show();
// 					});
// 				});
// 			})
// 		});
// 	}

// 	// Fetch all Dashboard Data for a particular dashboard Name
// 	// To handle Slice based filters, need to handle in fetch for every Data Slice
// 	fetch_all() {
// 		let method = 'latte.latte.doctype.dashboard_configuration.run';
// 		//debugger
// 		return frappe.xcall(
// 			method,
// 			{
// 				filters: this.filters,
// 				dashboard_name: this.dashboard_name
// 			}
// 		);
// 	}

// 	get_dashboard_doc() {
// 		return frappe.model.with_doc('Dashboard Configuration', this.dashboard_name);
// 	}
// }