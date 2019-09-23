frappe.provide("latte.dashboard")

// Latte Dashboard Page
frappe.pages['dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard',
		single_column: true
	});

	// Expanding Container
	$('.container').removeClass('container').addClass('container-fluid');

	latte.dashboard = new latte.Dashboard(wrapper);
	$(wrapper).bind('show', function() {
		 latte.dashboard.show();
	});
	
}

latte.Dashboard = class GenericDashboard {
	constructor(wrapper) {
		const that = this;
		// debugger
		this.wrapper = $(wrapper);
		$(`<div class="dashboard">
			<div class="dashboard-graph row"></div>
		</div>`).appendTo(this.wrapper.find(".page-content"));
		// Changing margin to 0px
		$('.row.layout-main .layout-main-section-wrapper').css({'margin':'0px'});
		this.filters = {};
		this.container = this.wrapper.find(".dashboard-graph");
		this.page = wrapper.page;
		this.page.set_primary_action(
			__('Refresh'),
			() => { me.reload(); }, 'icon-refresh',
		);
	}

	show() {
		this.route = frappe.get_route();
		if (this.route.length > 1) {
			// from route
			this.show_dashboard(this.route.slice(-1)[0]);
		} else {
			// last opened
			if (frappe.last_dashboard) {
				frappe.set_route('dashboard', frappe.last_dashboard);
			} else {
				// default dashboard
				frappe.db.get_list('Dashboard Configuration', {filters: {is_default: 1}}).then(data => {
					if (data && data.length) {
						frappe.set_route('dashboard', data[0].name);
					} else {
						// no default, get the latest one
						frappe.db.get_list('Dashboard Configuration', {limit: 1}).then(data => {
							if (data && data.length) {
								frappe.set_route('dashboard', data[0].name);
							} else {
								// create a new dashboard!
								frappe.new_doc('Dashboard Configuration');
							}
						});
					}
				});
			}
		}
	}


	show_dashboard(current_dashboard_name) {
		if(this.dashboard_name !== current_dashboard_name) {
			this.dashboard_name = current_dashboard_name;
			let title = this.dashboard_name;
			if (!this.dashboard_name.toLowerCase().includes(__('dashboard'))) {
				// ensure dashboard title has "dashboard"
				title = __('{0} Dashboard', [title]);
			}
			this.page.set_title(title);
			//this.set_dropdown();
			this.container.empty();
			this.refresh();
		}
		this.charts = {};
		frappe.last_dashboard = current_dashboard_name;
	}

	refresh() {
		var that = this;	
		this.get_dashboard_doc().then((doc) => {
			this.dashboard_doc = doc
			this.dashboard_data_slices = this.dashboard_doc.dashboard_data_slices;
			if (this.container.children().length > 0)
				this.container.children().empty();
			this.fetch_all().then((data) => {
				this.data = data;
				this.data.data_slice_data.map((slice) => {
					let slice_container = $('#row'+slice.dash_level.position);
					// Will make Rows based on 
				 	if (slice.dash_level && slice.dash_level.name && slice_container.length <= 0) {
				 		slice_container = $(`<div id="row${slice.dash_level.position}" class="row"></div>`);
						 slice_container.appendTo(this.container);
						 if (slice.dash_level.height)
						 	$(slice_container).css({"height": slice.dash_level.height, 'overflow-y': 'auto'});
					}
					frappe.model.with_doc("Dashboard Data Slice", slice.data_slice_name).then( slice_doc => {
						let slice_data = data.data_slice_data.filter((dt) => dt.data_slice_name == slice_doc.name);			
						let slice = new latte.Dashboard.DataSlice(slice_doc, slice_container, 
						  		undefined != slice_data && slice_data.length > 0 ? slice_data[0].result: undefined);
						slice.show();
					});
				});
			})
		});
	}

	// Fetch all Dashboard Data for a particular dashboard Name
	// To handle Slice based filters, need to handle in fetch for every Data Slice
	fetch_all() {
		let method = 'latte.latte.doctype.dashboard_configuration.run';
		//debugger
		return frappe.xcall(
			method,
			{
				filters: this.filters,
				dashboard_name: this.dashboard_name
			}
		);
	}

	get_dashboard_doc() {
		return frappe.model.with_doc('Dashboard Configuration', this.dashboard_name);
	}
}

latte.Dashboard.DataSlice = class GenericDashboardDataSlice {
	constructor(slice_doc, slice_container, slice_data) {
		this.slice_doc = slice_doc;
		this.container = slice_container;
		this.slice_data = slice_data;
	}

	show() {
		this.prepare_container();
		this.render();
		// this.fetch().then((data) => {
		// 	this.data = data;
		// 	debugger
		// })

		// this.get_settings().then(() => {
		// 	this.prepare_chart_object();
		// 	this.prepare_container();
		// 	this.prepare_chart_actions();
		// 	this.fetch(this.filters).then((data) => {
		// 		this.update_last_synced();
		// 		this.data = data;
		// 		this.render();
		// 	});
		// });
	}

	prepare_container() {
		let columns = this.slice_doc.width;//column_width_map['Half'];
		let class_name = this.slice_doc.name.replace(/ /g,'');
		this.chart_container = $(`<div class="col-sm-${columns} chart-column-container">
			<div class="chart-wrapper chart-wrapper-${class_name}">
				<div class="chart-loading-state text-muted">${__("Loading...")}</div>
				<div class="chart-empty-state hide text-muted">${__("No Data")}</div>
			</div>
		</div>`);
		this.chart_container.appendTo(this.container);

		let last_synced_text = $(`<span class="text-muted last-synced-text"></span>`);
		last_synced_text.prependTo(this.chart_container);
	}

	prepare_chart_actions() {
		let actions = [
			{
				label: __("Refresh"),
				action: 'action-refresh',
				handler: () => {
					this.fetch(this.filters, true).then(data => {
						this.update_chart_object();
						this.data = data;
						this.render();
					});
				}
			},
			{
				label: __("Edit..."),
				action: 'action-edit',
				handler: () => {
					frappe.set_route('Form', 'Dashboard Chart', this.chart_doc.name);
				}
			}
		];
		if (this.chart_doc.document_type) {
			actions.push({
				label: __("{0} List", [this.chart_doc.document_type]),
				action: 'action-list',
				handler: () => {
					frappe.set_route('List', this.chart_doc.document_type);
				}
			})
		}
		this.set_chart_actions(actions);
	}

	set_chart_actions(actions) {
		this.chart_actions = $(`<div class="chart-actions btn-group dropdown pull-right">
			<a class="dropdown-toggle" data-toggle="dropdown"
				aria-haspopup="true" aria-expanded="false"> <button class="btn btn-default btn-xs"><span class="caret"></span></button>
			</a>
			<ul class="dropdown-menu" style="max-height: 300px; overflow-y: auto;">
				${actions.map(action => `<li><a data-action="${action.action}">${action.label}</a></li>`).join('')}
			</ul>
		</div>
		`);

		this.chart_actions.find("a[data-action]").each((i, o) => {
			const action = o.dataset.action;
			$(o).click(actions.find(a => a.action === action));
		});
		this.chart_actions.prependTo(this.chart_container);
	}

	fetch(filters, refresh=false) {
		this.chart_container.find('.chart-loading-state').removeClass('hide');
		let method = 'latte.latte.doctype.dashboard_configuration.run';
		return frappe.xcall(
			method,
			{
				dashboard_name: this.dashboard_name,
				filters: {}
			}
		);
	}

	render() {	
		this.chart_container.find('.chart-loading-state').addClass('hide');
		if (this.slice_doc.data_type === 'Grid') {
			// debugger
			if (!this.slice_data.columns) {
				this.slice_data.data = this.slice_data.values;
				this.slice_data.columns = this.slice_data.keys;
			} else 
				this.slice_data.data = this.slice_data.result
			
			$.extend(this.slice_data, { 
				checkboxColumn: true,
				layout: 'fluid',
				noDataMessage: "No Data",
				inlineFilters: true
			});
			new latte.DataTable(this.chart_container.find(".chart-wrapper")[0], this.slice_data);
		} else if (this.slice_doc.data_type === 'Count') {
			//debugger
			let pos = this.slice_doc.report_count_position;
			pos = pos.split(':');
			if(pos) {
				//debugger
				
				//let index = Array.prototype.indexOf.call(this.slice_data.columns, this.slice_doc.report_field);
				$(`<div class="dashboard-count">
						<div><b>${this.slice_doc.report_count_label}</b></div>
						<div class="big-val">${this.slice_data.result[pos[0]][pos[1]]}</div>
					</div>`)
					.appendTo(this.chart_container.find(".chart-wrapper")[0]);
				if(this.slice_doc.report_count_background_color)
					$(this.chart_container.find(".chart-wrapper .dashboard-count").css({'background-color': this.slice_doc.report_count_background_color}))
				if(this.slice_doc.report_count_color)
				$(this.chart_container.find(".chart-wrapper .dashboard-count").css({'color': this.slice_doc.report_count_color}))

			}
		} else if (this.slice_doc.data_type === 'Filter') {
			if ($('.layout-main-section #filters').length <= 0
				&& Object.values(latte.dashboard.filters || []).filter((item) => item != null && item != undefined).length <=0) {
				//$('<div id="dashboard-filters"></div>').appendTo($('.layout-main-section'));
				let index = Array.prototype.indexOf.call(this.slice_data.columns || this.slice_data.keys, this.slice_doc.filter_field);
				latte.dashboard.filters[this.slice_doc.name] = null;
				let that = this;
				latte.dashboard.page.add_field({
						fieldname: this.slice_doc.filter_field,
						label: __(this.slice_doc.filter_field),
						fieldtype: 'Select',
						options: this.slice_data.result != undefined 
							? [''].concat([...new Set(this.slice_data.result.map(item => item[index]))]):
							[''].concat([...new Set(this.slice_data.values.map(item => item[index]))]),
						reqd: 1,
						change() {
							latte.dashboard.filters[that.slice_doc.name] = this.value;
							$(document).trigger('data-attribute-changed');
						},
					});	
			}
		}
	}
}

$(document).on('data-attribute-changed', function() {
	latte.dashboard.refresh();
});