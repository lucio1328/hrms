import frappe
from frappe import _

@frappe.whitelist()
@frappe.whitelist()
def get_all_doctypes():
    """
    Retourne uniquement les DocTypes liés à la gestion de la paie.
    """
    payroll_doctypes = [
        "Employee",
        "Salary Slip",
        # "Salary Slip Deduction",
        # "Salary Slip Earning",
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

    return frappe.get_all(
        "DocType",
        fields=["name", "module"],
        filters={"name": ["in", payroll_doctypes]},
        order_by="module, name"
    )


@frappe.whitelist()
def reinitialiser_donnees(tables):
    """
    Réinitialise les données des tables sélectionnées

    Args:
        tables (list): Liste des noms de tables à vider (sans le préfixe 'tab')

    Returns:
        dict: Résultat de l'opération avec statut et détails
    """
    # Conversion et validation des paramètres
    if isinstance(tables, str):
        try:
            tables = frappe.parse_json(tables)
        except:
            frappe.throw(_("Format des tables invalide"))

    if not tables or not isinstance(tables, (list, tuple)):
        return {
            "success": False,
            "message": _("Aucune table valide sélectionnée")
        }

    # Liste des tables protégées (ne jamais vider)
    PROTECTED_TABLES = [
        "User", "Role", "Module Def", "DocType",
        "DocField", "Custom Field", "Property Setter"
    ]

    results = {}
    tables_cleared = 0
    skipped_tables = []

    for table in tables:
        try:
            # Nettoyage du nom de la table
            table = table.strip()
            if not table:
                continue

            # Vérification des tables protégées
            if table in PROTECTED_TABLES:
                results[table] = _("Table protégée - non modifiable")
                skipped_tables.append(table)
                continue

            # Formatage du nom de table SQL
            table_name = f"tab{table}" if not table.startswith('tab') else table
            doctype_name = table.replace('tab', '')

            # Vérification que le DocType existe
            if not frappe.db.exists("DocType", doctype_name):
                results[table] = _("DocType inexistant")
                skipped_tables.append(table)
                continue

            # Vérification des permissions
            if not frappe.has_permission(doctype_name, "write"):
                results[table] = _("Permission refusée")
                skipped_tables.append(table)
                continue

            # Exécution du TRUNCATE
            frappe.db.sql(f"TRUNCATE `{table_name}`")
            results[table] = _("Succès")
            tables_cleared += 1

        except Exception as e:
            frappe.log_error(_("Erreur lors de la réinitialisation de {0}").format(table))
            results[table] = _("Erreur: {0}").format(str(e))
            skipped_tables.append(table)

    # Validation finale avant commit
    if tables_cleared > 0:
        frappe.db.commit()
    else:
        frappe.db.rollback()

    # Préparation des statistiques
    total_tables = len(tables)
    success_rate = (tables_cleared / total_tables * 100) if total_tables > 0 else 0

    return {
        "success": tables_cleared > 0,
        "results": results,
        "stats": {
            "total": total_tables,
            "cleared": tables_cleared,
            "skipped": len(skipped_tables),
            "success_rate": round(success_rate, 2)
        },
        "message": _(
            "Opération terminée: {0} tables vidées sur {1} demandées ({2}% de succès)"
        ).format(tables_cleared, total_tables, round(success_rate, 2))
    }

# import frappe

# @frappe.whitelist()
# def reinitialiser_donnees():
#     # Exemples : tu choisis ici ce que tu fais
#     frappe.db.sql('DELETE FROM `tabCustomer`')
#     # frappe.db.sql('DELETE FROM `tabMaDeuxiemeTable`')

#     frappe.db.commit()
#     return 'Réinitialisation terminée'
