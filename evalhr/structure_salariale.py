# import frappe
# from frappe import _
# import json

# @frappe.whitelist(allow_guest=True)
# def import_grille_salaire():
#     try:
#         data = frappe.request.get_json()
#         grille = data.get("grilles")

#         if not grille or not isinstance(grille, list):
#             return {
#                 "status": "error",
#                 "message": _("Le champ 'grilles' est requis et doit être une liste.")
#             }

#         processed_structures = {}

#         for row in grille:
#             structure_name = row.get("salary_structure")
#             company = row.get("company")
#             composant_nom = row.get("name")
#             abbr = row.get("abbr")
#             type_comp = row.get("type")     
#             formule = row.get("valeur")

#             if not (structure_name and company and composant_nom and type_comp):
#                 continue

#             # Vérifie si le Salary Component existe
#             composant_existant = frappe.db.exists("Salary Component", {
#                 "salary_component": composant_nom,
#                 "company": company
#             })
            
#             composant_non_existant = frappe.db.exists("Salary Component",
#                 composant_nom
#             )
            

#             if not composant_existant and not composant_non_existant:
#                 comp = frappe.new_doc("Salary Component")
#                 comp.salary_component = composant_nom
#                 comp.salary_component_abbr = abbr
#                 comp.type = "Earning" if type_comp.lower() == "earning" else "Deduction"
#                 comp.company = company
#                 comp.depends_on_payment_days = 0

#                 # is_formula = bool(formule and not formule.replace('.', '', 1).isdigit())
#                 # comp.is_formula_based = is_formula

#                 # if is_formula:
#                 #     comp.amount_based_on_formula = 1
#                 #     comp.formula = formule
#                 # else:
#                 #     comp.amount = float(formule or 0)

#                 default_account = get_default_account(company)
#                 # if default_account:
#                 comp.default_account = default_account

#                 comp.insert()

#             # Création de Salary Structure si pas déjà créée
#             if structure_name not in processed_structures:
#                 if frappe.db.exists("Salary Structure", {"name": structure_name}):
#                     structure=frappe.get_doc("Salary Structure", structure_name)
#                 # if not frappe.db.exists("Salary Structure", {"name": structure_name}):
#                 else:
#                     structure = frappe.new_doc("Salary Structure")
#                     structure.name = structure_name
#                     structure.salary_structure_name = structure_name
#                     structure.company = company
#                     structure.is_active = "Yes"
#                     structure.insert()
#                 # processed_structures.add(structure_name)
#                 processed_structures[structure_name]=structure
                

#             # Ajout du Salary Component à la Salary Structure
#             # structure = frappe.get_doc("Salary Structure", structure_name)
#             structure=processed_structures[structure_name]

#             is_formula = bool(formule and not formule.replace('.', '', 1).isdigit())
#             amount_val = 0.0 if is_formula else float(formule or 0)

#             ligne = {
#                 "salary_component": composant_nom,
#                 "amount": amount_val,
#                 "amount_based_on_formula": 1 if is_formula else 0,
#                 "formula": formule if is_formula else ""
#             }

#             if type_comp.lower() == "earning":
#                 if not any(e.salary_component == composant_nom for e in structure.earnings):
#                     structure.append("earnings", ligne)
#             else:
#                 if not any(d.salary_component == composant_nom for d in structure.deductions):
#                     structure.append("deductions", ligne)

#             # structure.save()
#             # structure.validate()
#         for structure in processed_structures.values():
#             structure.save()
#             # if structure.docstatus== 0:
#             structure.submit()
#             # else:
#             #      return {
#             #         "status": "error",
#             #         "message": _("Erreur lors de la validation de la structure")
#             #     }


#         return {
#             "status": "success",
#             "message": _("Grille salariale importée avec succès")
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Erreur import grille salaire"))
#         return {
#             "status": "error",
#             "message": _("Erreur lors de l'import: {0}").format(str(e))
#         }


# def get_default_account(company):
#     abbr = frappe.get_value("Company", company, "abbr")
#     # account = f"Salaires - {abbr}"
#     account = "Paie à Payer - " + frappe.get_value('Company', company, 'abbr')

    
#     if frappe.db.exists("Account", account):
#         return account
#     return None






import frappe # type: ignore
from frappe import _ # type: ignore
import json
import re

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

        
        structures_data = {}
        

        for idx,row  in enumerate(grille, start=1):
            try:
                

                structure_name = row["salary_structure"]
                if structure_name not in structures_data:
                    structures_data[structure_name] = {
                        "company": row["company"],
                        "components": [],
                        "abbreviations": set()
                    }

                component_data = {
                    "name": row["name"],
                    "abbr": row.get("abbr", ""),
                    "type": row["type"].lower(),
                    "formule": row.get("valeur", ""),
                    "line": idx
                }
                structures_data[structure_name]["components"].append(component_data)
                
                if component_data["abbr"]:
                    structures_data[structure_name]["abbreviations"].add(component_data["abbr"])

            except Exception as e:
                frappe.log_error(frappe.get_traceback(), _("Erreur préparation ligne {}").format(idx))
                return {
                    "status": "error",
                    "message": _("Erreur ligne {}: {}").format(idx, str(e)),
                }

        for structure_name, data in structures_data.items():
            try:
               
                for component in data["components"]:
                    if component["formule"] and not str(component["formule"]).replace('.', '', 1).isdigit():
                        # used_abbrs = set(re.findall(r'\b[a-zA-Z_]+\b', component["formule"]))
                        # excluded_keywords = {'base'}
        
                       
                        # abbrs_to_check = [abbr for abbr in used_abbrs 
                        #                 if abbr.lower() not in excluded_keywords]
                        
                        # missing_abbrs = [abbr for abbr in abbrs_to_check 
                        #                 if abbr not in data.get("abbreviations", {})]
                        print(data["abbreviations"])
                        missing_abbrs = []
                        for abbr in re.findall(r'\b[a-zA-Z_]+\b', component["formule"]):
                            abbr_lower = abbr.lower()
                            if abbr_lower not in {'base'} and abbr not in data["abbreviations"]:
                                missing_abbrs.append(abbr)
                        
                        if missing_abbrs:
                            return {
                                "status": "error",
                                "message": _("Ligne {}: Composant  non déclarée dans la structure '{}': {}").format(
                                    component["line"],structure_name, ", ".join(missing_abbrs))
                            }

                
                if frappe.db.exists("Salary Structure", {"name": structure_name}):
                    structure = frappe.get_doc("Salary Structure", structure_name)
                else:
                    structure = frappe.new_doc("Salary Structure")
                    structure.name = structure_name
                    structure.salary_structure_name = structure_name
                    structure.company = data["company"]
                    structure.is_active = "Yes"
                    structure.insert()

                
                for component in data["components"]:
                    if not frappe.db.exists("Salary Component", component["name"]):
                        comp = frappe.new_doc("Salary Component")
                        comp.salary_component = component["name"]
                        comp.salary_component_abbr = component["abbr"]
                        comp.type = "Earning" if component["type"] == "earning" else "Deduction"
                        comp.company = data["company"]
                        comp.depends_on_payment_days = 0
                        default_account = get_default_account(data["company"])
                        
                        comp.append("accounts", {
                                    "company": data["company"],
                                    "account": default_account  # Champ correct dans ERPNext
                                })
                        # is_formula = bool(component["formule"] and 
                        #                 not str(component["formule"]).replace('.', '', 1).isdigit())

                        # if is_formula:
                        #     comp.is_formula_based = 1
                        #     comp.formula = component["formule"]
                        # else:
                        #     comp.amount = float(component["formule"] or 0)

                        # default_account = get_default_account(data["company"])
                        # if default_account:
                            
                        #     if not any(acc.company == data["company"] for acc in comp.get("accounts", [])):
                        #         comp.append("accounts", {
                        #             "company": data["company"],
                        #             "account": default_account  # Champ correct dans ERPNext
                        #         })
                        

                        comp.insert()

                    
                    is_formula = bool(component["formule"] and 
                                    not str(component["formule"]).replace('.', '', 1).isdigit())
                    amount_val = 0.0 if is_formula else float(component["formule"] or 0)

                    ligne = {
                        "salary_component": component["name"],
                        "amount": amount_val,
                        "amount_based_on_formula": 1 if is_formula else 0,
                        "formula": component["formule"] if is_formula else ""
                    }

                    if component["type"] == "earning":
                        if not any(e.salary_component == component["name"] 
                                 for e in structure.earnings):
                            structure.append("earnings", ligne)
                    else:
                        if not any(d.salary_component == component["name"] 
                                 for d in structure.deductions):
                            structure.append("deductions", ligne)

                
                structure.save()
                # if structure.docstatus == 0:
                structure.submit()

            except Exception as e:
                frappe.log_error(frappe.get_traceback(), 
                               _("Erreur traitement structure {}").format(structure_name))
                return {
                    "status": "error",
                    "message": _("Erreur dans la structure '{}': {}").format(structure_name, str(e))
                    
                }

        return {
            "status": "success",
            "message": _("Grilles salariales importées avec succès")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Erreur import grille salaire"))
        return {
            "status": "error",
            "message": _("Erreur lors de l'import: {0}").format(str(e))
        }

def get_default_account(company):
    """Retourne le compte par défaut pour les salaires"""
    account_variants = [
        f"Paie à Payer - {frappe.get_value('Company', company, 'abbr')}",
        f"Salaires - {frappe.get_value('Company', company, 'abbr')}",
        "Paie à Payer",
        "Salaires"
    ]
    
    for account in account_variants:
        if frappe.db.exists("Account", account):
            return account
    return None