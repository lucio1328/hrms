frappe.pages['reset_hr'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Réinitialisation des données'),
		single_column: true
	});

	const html = `
		<div class="reset-page grid" style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; padding: 32px;">
			<!-- Liste de tables -->
			<div class="left-panel">
				<div class="card" style="padding: 24px; border-radius: 8px; box-shadow: var(--shadow-sm);">
					<h5 style="margin-bottom: 16px;">${__('Tables disponibles')}</h5>
					<input type="text" id="doctype-search" class="form-control mb-3" placeholder="${__('Rechercher une table...')}">

					<div id="doctype-list" style="max-height: 400px; overflow-y: auto; border: 1px solid #d1d8dd; border-radius: 6px; padding: 12px;"></div>
				</div>
			</div>

			<!-- Résumé + Action -->
			<div class="right-panel">
				<div class="card" style="padding: 24px; border-radius: 8px; box-shadow: var(--shadow-sm); background-color: #fff3f3;">
					<h4 style="color: #d43f00;">⚠️ ${__('Action irréversible')}</h4>
					<p class="text-muted" style="margin-top: 10px;">${__('Les données des tables sélectionnées seront définitivement supprimées.')}</p>

					<div class="mt-4 mb-2">
						<strong>${__('Tables sélectionnées :')}</strong>
						<div id="selected-count" class="badge bg-light text-dark ml-2">0</div>
					</div>

					<div class="form-check mt-3">
						<input type="checkbox" id="select-all" class="form-check-input">
						<label class="form-check-label" for="select-all">${__('Tout sélectionner')}</label>
					</div>

					<button id="reset-btn" class="btn btn-danger btn-block mt-4" disabled>
						🔁 ${__('Réinitialiser maintenant')}
					</button>
				</div>
			</div>
		</div>
	`;

	$(page.main).html(html);

	const listContainer = $('#doctype-list');
	const searchInput = $('#doctype-search');
	const resetBtn = $('#reset-btn');
	const selectedCount = $('#selected-count');

	// Récupération des doctypes
	frappe.call({
		method: 'hrms.reset_hr.page.reset_hr.reset_hr.get_all_doctypes',
		callback: function(r) {
			if (r.message) {
				r.message.sort((a, b) => a.name.localeCompare(b.name));

				const PRESELECTED = [
					"Employee",
					"Salary Component",
					"Salary Structure",
					"Salary Structure Assignment",
					"Salary Slip",
					"Payroll Entry",
					"Payroll Period"
				];

				r.message.forEach(dt => {
					const isPreselected = PRESELECTED.includes(dt.name);
					const item = $(`
						<div class="form-check mb-2" data-name="${dt.name}">
							<input class="form-check-input doctype-checkbox" type="checkbox" value="${dt.name}" id="${dt.name}" ${isPreselected ? 'checked' : ''}>
							<label class="form-check-label" for="${dt.name}">${dt.name}</label>
						</div>
					`);
					listContainer.append(item);
				});

				updateSelectedCount();
			}
		}
	});

	// Filtrage
	searchInput.on('input', function() {
		const query = $(this).val().toLowerCase();
		$('.form-check').each(function() {
			const match = $(this).data('name').toLowerCase().includes(query);
			$(this).toggle(match);
		});
	});

	// Compteur sélection
	function updateSelectedCount() {
		const count = $('.doctype-checkbox:checked').length;
		selectedCount.text(count);
		resetBtn.prop('disabled', count === 0);
	}

	$(document).on('change', '.doctype-checkbox', updateSelectedCount);

	$('#select-all').on('change', function() {
		const checked = $(this).is(':checked');
		$('.doctype-checkbox').prop('checked', checked);
		updateSelectedCount();
	});

	// Action réinitialisation
	resetBtn.on('click', function() {
		const selected = $('.doctype-checkbox:checked').map(function() {
			return this.value;
		}).get();

		frappe.confirm(
			__('Confirmez-vous la suppression des données de {0} table(s) ?', [selected.length]),
			() => {
				const $btn = $(this).prop('disabled', true).text(__('Traitement...'));

				frappe.call({
					method: 'hrms.reset_hr.page.reset_hr.reset_hr.reinitialiser_donnees',
					args: { tables: selected },
					callback: function(r) {
						frappe.show_alert({
							message: __('Tables réinitialisées.', [r.message.tables_cleared]),
							indicator: 'green'
						});
					},
					always: function() {
						$btn.prop('disabled', false).text(__('Réinitialiser maintenant'));
					}
				});
			}
		);
	});
};
