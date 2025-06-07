import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def import_grille_salaire():
    try:
        data = frappe.request.get_json()
        grille = data.get("grilles")

        if not grille or not isinstance(grille, list):
            return {
                "status": "error",
                "message": _("Le champ 'grilles' est requis et doit être une liste.")
            }

        processed_structures = {}

        for row in grille:
            structure_name = row.get("salary_structure")
            company = row.get("company")
            composant_nom = row.get("name")
            abbr = row.get("abbr")
            type_comp = row.get("type")
            formule = row.get("valeur")

            if not (structure_name and company and composant_nom and type_comp):
                continue

            # Vérifie si le Salary Component existe
            composant_existant = frappe.db.exists("Salary Component", {
                "salary_component": composant_nom,
                "company": company
            })

            # Optionnellement, vérifie aussi par nom exact (clé primaire)
            nom_existant = frappe.db.exists("Salary Component", composant_nom)

            if not composant_existant and not nom_existant:
                comp = frappe.new_doc("Salary Component")
                comp.salary_component = composant_nom
                comp.salary_component_abbr = abbr
                comp.type = "Earning" if type_comp.lower() == "earning" else "Deduction"
                comp.company = company
                comp.depends_on_payment_days = 0

                # is_formula = bool(formule and not formule.replace('.', '', 1).isdigit())
                # comp.is_formula_based = is_formula

                # if is_formula:
                #     comp.amount_based_on_formula = 1
                #     comp.formula = formule
                # else:
                #     comp.amount = float(formule or 0)

                default_account = get_default_account(company)
                if default_account:
                    comp.default_account = default_account

                comp.insert()

            # Création de Salary Structure si pas déjà créée
            if structure_name not in processed_structures:
                if frappe.db.exists("Salary Structure", {"name": structure_name}):
                    structure = frappe.get_doc("Salary Structure", structure_name)
                else:
                    structure = frappe.new_doc("Salary Structure")
                    structure.name = structure_name
                    structure.salary_structure_name = structure_name
                    structure.company = company
                    structure.is_active = "Yes"
                    structure.insert()

                processed_structures[structure_name] = structure


            # Ajout du Salary Component à la Salary Structure
            # structure = frappe.get_doc("Salary Structure", structure_name)
            structure = processed_structures[structure_name]

            is_formula = bool(formule and not formule.replace('.', '', 1).isdigit())
            amount_val = 0.0 if is_formula else float(formule or 0)

            ligne = {
                "salary_component": composant_nom,
                "amount": amount_val,
                "amount_based_on_formula": 1 if is_formula else 0,
                "formula": formule if is_formula else ""
            }

            if type_comp.lower() == "earning":
                if not any(e.salary_component == composant_nom for e in structure.earnings):
                    structure.append("earnings", ligne)
            else:
                if not any(d.salary_component == composant_nom for d in structure.deductions):
                    structure.append("deductions", ligne)

            # structure.save()
            # try:
            #     if structure.docstatus == 0:
            #         structure.submit()
            # except Exception as e:
            #     frappe.log_error(frappe.get_traceback(), "Erreur lors de la soumission de Salary Structure")
            #     raise e
        for structure in processed_structures.values():
            structure.save()
            try:
                if structure.docstatus == 0:
                    structure.submit()
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Erreur lors de la soumission de Salary Structure")
                raise e

        return {
            "status": "success",
            "message": _("Grille salariale importée avec succès"),
            "structures_traitees": list(processed_structures.keys())
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Erreur import grille salaire"))
        return {
            "status": "error",
            "message": _("Erreur lors de l'import: {0}").format(str(e))
        }


def get_default_account(company):
    abbr = frappe.get_value("Company", company, "abbr")
    account = f"Salaires - {abbr}"
    if frappe.db.exists("Account", account):
        return account
    return None
