import frappe
from frappe import _
from datetime import datetime
from frappe.utils import getdate, nowdate, get_last_day
import json

@frappe.whitelist(allow_guest=True)
def import_salary_data():
    try:
        data = frappe.request.get_json()
        salary_data = data.get("salaries")

        if not salary_data or not isinstance(salary_data, list):
            return format_response(
                status="error",
                message=_("Le champ 'salaries' est requis et doit être une liste.")
            )

        created_slips = []
        created_assignments = []
        created_payments = []
        errors = []

        for row in salary_data:
            try:
                mois = row.get("mois")
                ref_employe = row.get("ref_employe")
                salaire_base = row.get("salaire_base")
                salary_structure = row.get("salary_structure")

                start_date = getdate(mois)
                end_date = get_last_day(start_date)

                if not frappe.db.exists("Employee", {"name": ref_employe, "status": "Active"}):
                    errors.append(f"Employé {ref_employe} introuvable ou inactif")
                    continue

                employee = frappe.get_doc("Employee", ref_employe)
                company = employee.company

                if not frappe.db.exists("Salary Structure", salary_structure):
                    errors.append(f"Structure de salaire {salary_structure} non trouvée")
                    continue

                slip_exists = frappe.db.exists("Salary Slip", {
                    "employee": ref_employe,
                    "start_date": start_date,
                    "end_date": end_date,
                    "docstatus": 1
                })

                if slip_exists:
                    errors.append(
                        f"Fiche de Paie de l'employé {ref_employe} déjà créée pour la période {start_date.strftime('%Y-%m-%d')} à {end_date.strftime('%Y-%m-%d')}"
                    )
                    continue

                assignment = assign_structure_to_employee(
                    ref_employe, salary_structure, start_date, company, salaire_base
                )

                slip = frappe.new_doc("Salary Slip")
                slip.employee = ref_employe
                slip.salary_structure = salary_structure
                slip.start_date = start_date
                slip.end_date = end_date
                # slip.posting_date = nowdate()
                slip.posting_date = start_date
                slip.company = company
                slip.payroll_frequency = "Monthly"
                slip.insert(ignore_permissions=True)
                # slip.run_salary_structure()
                slip.calculate_net_pay()
                slip.save()
                slip.submit()


                # payment_entry = create_payment_entry(employee, slip)

            except Exception as e:
                return format_response(
                    status="error",
                    message=str(e) or _("Une erreur est survenue durant la création des fiches de paie."),
                )


        server_messages = frappe.local.response.get("_server_messages")
        main_message = None

        if server_messages:
            try:
                decoded = json.loads(server_messages)

                for msg in decoded:
                    parsed = json.loads(msg)
                    indicator = parsed.get("indicator")

                    if indicator == "red" and parsed.get("message"):
                        main_message = parsed.get("message")
                        break

                if not main_message and decoded:
                    parsed = json.loads(decoded[0])
                    main_message = parsed.get("message")

            except Exception as e:
                main_message = _("Une erreur système est survenue, mais le message n’a pas pu être interprété.")

            return format_response(
                status="error",
                message=main_message or _("Une erreur est survenue durant la création des fiches de paie."),
            )

        return format_response(
            status="success",
            message=_("{0} Fiches de Paie, {1} Assignations et {2} Paiements créés.").format(
                len(created_slips), len(created_assignments), len(created_payments)
            )
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Erreur globale import salaires"))
        return format_response(
            status="error",
            message=_("Erreur lors de l'import: {0}").format(str(e))
        )

def assign_structure_to_employee(employee, salary_structure, start_date, company, salaire_base):
    existing_assignment = frappe.db.exists("Salary Structure Assignment", {
        "employee": employee,
        "salary_structure": salary_structure,
        "company": company,
        "from_date": start_date,
        "docstatus": 1
    })
    if existing_assignment:
        return frappe.get_doc("Salary Structure Assignment", existing_assignment)

    assignment = frappe.new_doc("Salary Structure Assignment")
    assignment.employee = employee
    assignment.salary_structure = salary_structure
    assignment.company = company
    assignment.from_date = start_date
    assignment.base = salaire_base
    assignment.insert(ignore_permissions=True)
    assignment.submit()
    return assignment

def create_payment_entry(employee, salary_slip):
    try:
        payment = frappe.new_doc("Payment Entry")
        payment.payment_type = "Pay"
        payment.posting_date = nowdate()
        payment.mode_of_payment = "Cash"
        payment.party_type = "Employee"
        payment.party = employee.name
        paid_from_account = frappe.db.get_value("Company", employee.company, "default_payable_account")
        payment.paid_from = paid_from_account
        payment.paid_from_account_currency = frappe.db.get_value("Account", paid_from_account, "account_currency")
        payment.paid_to = frappe.db.get_value("Company", employee.company, "default_cash_account")
        payment.paid_amount = salary_slip.net_pay
        payment.received_amount = salary_slip.net_pay
        payment.source_exchange_rate = 1
        payment.reference_doctype = "Salary Slip"
        payment.reference_name = salary_slip.name
        payment.company = employee.company
        payment.insert(ignore_permissions=True)
        payment.submit()
        # return payment
    except Exception as e:
        raise

def format_response(status=None, message=None, **kwargs):
    response = {
        "status": status,
        "message": message
    }
    response.update(kwargs)
    return response