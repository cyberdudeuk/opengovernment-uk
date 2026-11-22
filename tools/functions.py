"""Flag bodies that exist to run government's own central and back-office functions.
The function list is the Government Functional Standards collection on GOV.UK, read 22 November 2026
(https://www.gov.uk/government/collections/functional-standards). GovS 001 defines the functions; there is no GovS 012.
Every flag records its basis, and anything not decided by an explicit rule is left unflagged: no guessing."""
FUNCTIONS = {
    "GovS 002": "Project delivery", "GovS 003": "People", "GovS 004": "Property", "GovS 005": "Digital",
    "GovS 006": "Finance", "GovS 007": "Security", "GovS 008": "Commercial", "GovS 009": "Internal audit",
    "GovS 010": "Analysis", "GovS 011": "Communication", "GovS 013": "Counter fraud", "GovS 014": "Debt", "GovS 015": "Grants",
}
# Cross-government functions that have no functional standard but are recognised functions in GovS 001
OTHER_FUNCTIONS = {"Legal": "Government Legal Profession", "Policy": "Policy Profession", "Science and engineering": "Government Science and Engineering"}


def classify_function(body: dict) -> tuple[str | None, str]:
    """Decide whether one register record is a central or back-office function body.

    body has: name (str), kind (GOV.UK type, e.g. "Executive agency"), family, ons_sector, parent_names (list of str),
    answers_to (str, from the accountability chain).
    Return (code, basis): code is a key of FUNCTIONS, a key of OTHER_FUNCTIONS, or None when not a back-office body;
    basis is one sentence saying which rule decided it, shown on the page as the flag's evidence.

    TODO (your call): the rules that decide it. The judgement is what "back-office" means for the anatomy:
      - Only bodies whose purpose is serving government itself (Government Property Agency, Crown Commercial Service,
        Government Internal Audit Agency, Government Legal Department, Government Digital Service)?
      - Or also mixed bodies whose back-office service is one line of business among public-facing ones
        (HMRC's debt management, a shared services centre inside a department)?
      - And how a closed predecessor is treated (Government Procurement Service before Crown Commercial Service).
    """
    return None, "not classified"
