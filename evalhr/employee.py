import frappe
from frappe import _
import json
from datetime import datetime
import random

@frappe.whitelist(allow_guest=True)
def import_employe():
    """
    Importe une liste d'employés depuis le corps de la requête HTTP (JSON)
    Retourne une correspondance ref -> nom de l'employé
    """
    try:
        # Récupérer le JSON depuis le body de la requête
        data = frappe.request.get_json()
        employees = data.get("employees")  # attend {"employees": [ {...}, {...} ]}

        if not employees or not isinstance(employees, list):
            return {
                "status": "error",
                "message": _("Le champ 'employees' est requis et doit être une liste.")
            }

        ref_mapping = {}

        for emp_data in employees:
            company = emp_data.get("company")
            if company and not frappe.db.exists("Company", company):
                create_company(company)

            employee = create_employee(emp_data)
            ref_mapping[emp_data.get("ref")] = employee.name

        return {
            "status": "success",
            "message": _("{0} employés importés avec succès").format(len(employees)),
            "ref_mapping": ref_mapping
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Erreur lors de l'import des employés"))
        return {
            "status": "error",
            "message": _("Erreur lors de l'import des employés: {0}").format(str(e))
        }

def create_company(company_name):
    """Crée une nouvelle company si elle n'existe pas"""
    company = frappe.new_doc("Company")
    company.company_name = company_name
    company.abbr = company_name[:3].upper()
    company.default_currency = "EURO"
    company.country = "Madagascar"
    company.default_holiday_list = "Weekend"
    company.insert()
    return company

def create_employee(emp_data):
    """Crée un nouvel employé à partir des données"""

    # if emp_data.get("ref"):
    #     existing_employee = frappe.db.get_value("Employee", {"custom_ref": emp_data.get("ref")}, "name")
    #     if existing_employee:
    #         return frappe.get_doc("Employee", existing_employee)

    departments = frappe.get_all("Department", pluck="name")
    designations = frappe.get_all("Designation", pluck="name")

    employee = frappe.new_doc("Employee")


    employee.first_name = emp_data.get("prenom", "")
    employee.last_name = emp_data.get("nom", "")
    employee.gender = map_gender(emp_data.get("genre", ""))
    employee.date_of_birth = emp_data.get("date_naissance")
    employee.date_of_joining = emp_data.get("date_embauche")
    employee.company = emp_data.get("company")

    employee.department = random.choice(departments)
    employee.designation = random.choice(designations)


    # employee.custom_ref = emp_data.get("ref")

    employee.insert()
    return employee


def parse_date(date_str):
    """Convertit une date string en format YYYY-MM-DD"""
    if not date_str:
        return None

    try:

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
    except:
        return None

def map_gender(gender):
    """Map le genre vers les valeurs attendues par ERPNext"""
    gender = (gender or "").lower()
    if gender in ("m", "male", "homme", "h","masculin"):
        return "Male"
    elif gender in ("f", "female", "femme","feminin"):
        return "Female"
    return "Other"
