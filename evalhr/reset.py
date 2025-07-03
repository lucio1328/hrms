import frappe # type: ignore
from frappe import _ # type: ignore

@frappe.whitelist()
def reset():
    """
    Réinitialise toutes les données des tables liées à la gestion de la paie.
    """
    payroll_doctypes = [
        "Employee",
        "Salary Slip",
        "Salary Slip Deduction",
        "Salary Slip Earning",
        "Salary Structure",
        "Salary Structure Assignment",
        "Salary Detail",
        "Salary Component",
        "Additional Salary",
        "Employee Tax Exemption Declaration",
        "Employee Tax Exemption Proof Submission",
        "Employee Tax Exemption Category",
        "Employee Tax Exemption Sub Category",
        "Payroll Entry",
        "Payroll Period",
        "Process Payroll",
        "Timesheet"
    ]

    # Tables protégées à ne jamais toucher
    PROTECTED_TABLES = [
        "User", "Role", "Module Def", "DocType",
        "DocField", "Custom Field", "Property Setter"
    ]

    results = {}
    tables_cleared = 0
    skipped_tables = []

    for doctype in payroll_doctypes:
        try:
            if doctype in PROTECTED_TABLES:
                results[doctype] = _("Table protégée - non modifiable")
                skipped_tables.append(doctype)
                continue

            # Vérification du DocType
            if not frappe.db.exists("DocType", doctype):
                results[doctype] = _("DocType inexistant")
                skipped_tables.append(doctype)
                continue

            if not frappe.has_permission(doctype, "write"):
                results[doctype] = _("Permission refusée")
                skipped_tables.append(doctype)
                continue

            # Suppression des données
            table_name = f"tab{doctype}"
            frappe.db.sql(f"TRUNCATE `{table_name}`")
            results[doctype] = _("Succès")
            tables_cleared += 1

        except Exception as e:
            frappe.log_error(title="Erreur réinitialisation paie", message=frappe.get_traceback())
            results[doctype] = _("Erreur: {0}").format(str(e))
            skipped_tables.append(doctype)

    if tables_cleared > 0:
        frappe.db.commit()
    else:
        frappe.db.rollback()

    total = len(payroll_doctypes)
    success_rate = round((tables_cleared / total) * 100, 2) if total > 0 else 0

    return {
        "status":"success",
        "message": _(
            "Réinitialisation terminée : {0} sur {1} tables vidées ({2}% de succès)."
        ).format(tables_cleared, total, success_rate)
    }




# DELETE FROM `tabSalary Detail`;
# DELETE FROM `tabAdditional Salary`;
# DELETE FROM `tabEmployee Tax Exemption Proof Submission`;
# DELETE FROM `tabEmployee Tax Exemption Declaration`;
# DELETE FROM `tabEmployee Tax Exemption Sub Category`;
# DELETE FROM `tabEmployee Tax Exemption Category`;
# DELETE FROM `tabSalary Slip`;
# DELETE FROM `tabSalary Structure Assignment`;
# DELETE FROM `tabSalary Structure`;
# DELETE FROM `tabSalary Component`;
# DELETE FROM `tabPayroll Entry`;
# DELETE FROM `tabPayroll Period`;
# DELETE FROM `tabProcess Payroll`;
# DELETE FROM `tabTimesheet`;
# DELETE FROM `tabEmployee`;
