import frappe
from frappe import _

@frappe.whitelist()
def get_all_doctypes():
    """Retourne tous les DocTypes disponibles avec leur module, en incluant spécifiquement
    les types liés aux demandes de matériel, devis et fournisseurs"""

    # Liste des DocTypes à toujours inclure (même s'ils sont personnalisés ou autrement exclus)
    ALWAYS_INCLUDE = [
        "Item",
        "Material Request",
        "Material Request Item",
        "Request for Quotation",
        "Request for Quotation Supplier",
        "Request for Quotation Item",
        "Supplier",
        "Supplier Quotation",
        "Supplier Quotation Item",
        "Purchase Order",
        "Purchase Order Item",
        "Purchase Receipt",
        "Purchase Receipt Item",
        "Sales Invoice",
        "Sales Invoice Item",
        "Purchase Invoice",
        "Purchase Invoice Item",
        "Payment Entry",
        "Payment Entry Reference"
    ]

    # Récupération des DocTypes standards avec filtres de base
    doctypes = frappe.get_all(
        "DocType",
        fields=["name", "module"],
        filters={
            "istable": 0,
            "is_virtual": 0,
            "name": ["not in", [
                "DocType", "Patch Log", "Module Def", "DocField",
                "Communication", "Version", "Error Log", "Error Snapshot",
                "Scheduled Job Log", "Activity Log", "Document Follow"
            ]]
        },
        order_by="module, name"
    )

    # Récupération des DocTypes spécifiques même s'ils sont personnalisés ou table
    additional_doctypes = frappe.get_all(
        "DocType",
        fields=["name", "module"],
        filters={"name": ["in", ALWAYS_INCLUDE]},
        order_by="module, name"
    )

    # Fusion des deux listes en éliminant les doublons
    combined = doctypes + additional_doctypes
    unique_doctypes = []
    seen = set()

    for doctype in combined:
        if doctype["name"] not in seen:
            seen.add(doctype["name"])
            unique_doctypes.append(doctype)

    return unique_doctypes

@frappe.whitelist()
def reinitialiser_donnees():
    """
    Réinitialise les données des tables liées à la paie :
    Employee, Salary Component, Salary Structure, Salary Structure Assignment,
    Salary Slip, Payroll Entry, Payroll Period.

    Returns:
        dict: Résultat de l'opération avec statut et détails
    """

    # Tables à réinitialiser (DocTypes)
    TARGET_TABLES = [
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

    for doctype_name in TARGET_TABLES:
        try:
            # Vérifie si le DocType existe
            if not frappe.db.exists("DocType", doctype_name):
                results[doctype_name] = _("DocType inexistant")
                skipped_tables.append(doctype_name)
                continue

            # Vérifie si l'utilisateur a la permission d'écriture
            if not frappe.has_permission(doctype_name, "write"):
                results[doctype_name] = _("Permission refusée")
                skipped_tables.append(doctype_name)
                continue

            # Format du nom de table
            table_name = f"tab{doctype_name}"

            # Suppression des données
            frappe.db.sql(f"TRUNCATE `{table_name}`")
            results[doctype_name] = _("Succès")
            tables_cleared += 1

        except Exception as e:
            frappe.log_error(_("Erreur lors de la réinitialisation de {0}").format(doctype_name))
            results[doctype_name] = _("Erreur: {0}").format(str(e))
            skipped_tables.append(doctype_name)

    # Commit ou rollback selon le résultat
    if tables_cleared > 0:
        frappe.db.commit()
    else:
        frappe.db.rollback()

    total_tables = len(TARGET_TABLES)
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
            "Opération terminée: {0} tables vidées sur {1} ({2}% de succès)"
        ).format(tables_cleared, total_tables, round(success_rate, 2))
    }

