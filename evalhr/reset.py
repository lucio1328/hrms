import frappe
from frappe import _

@frappe.whitelist()
def reset():
    """
    Réinitialise uniquement les données des tables liées à la paie :
    Employee, Salary Component, Salary Structure, Salary Structure Assignment,
    Salary Slip, Payroll Entry, Payroll Period.

    Returns:
        dict: Résultat de l'opération avec statut et détails
    """

    ALLOWED_TABLES = [
        "Employee",
        "Salary Component",
        "Salary Structure",
        "Salary Structure Assignment",
        "Salary Slip",
        "Payroll Entry",
        "Payroll Period"
    ]

    results = {}
    tables_cleared = 0
    skipped_tables = []

    for table in ALLOWED_TABLES:
        try:
            table_name = f"tab{table}"

            # Vérifie si le DocType existe
            if not frappe.db.exists("DocType", table):
                results[table] = _("DocType inexistant")
                skipped_tables.append(table)
                continue

            # Vérifie les permissions
            if not frappe.has_permission(table, "write"):
                results[table] = _("Permission refusée")
                skipped_tables.append(table)
                continue

            # Exécution du TRUNCATE
            frappe.db.sql(f"TRUNCATE `{table_name}`")
            results[table] = _("Succès")
            tables_cleared += 1

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), _("Erreur lors de la réinitialisation de {0}").format(table))
            results[table] = _("Erreur: {0}").format(str(e))
            skipped_tables.append(table)

    # Commit ou rollback
    if tables_cleared > 0:
        frappe.db.commit()
    else:
        frappe.db.rollback()

    # Statistiques
    total_tables = len(ALLOWED_TABLES)
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

