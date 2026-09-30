"""
Rule-based risk flagging.

This intentionally does NOT rely on the LLM to decide what's risky —
risk rules should be deterministic and auditable. The LLM is only used
for drafting/explaining language (see llm_service.py).
"""


def flag_risks(template_type: str, answers: dict) -> list:
    """
    Inspect the wizard answers for a document and return a list of
    risk-flag dicts: {clause, level, message}.
    """
    flags = []

    if template_type == "nda":
        flags.extend(_flag_nda_risks(answers))
    elif template_type == "lease":
        flags.extend(_flag_lease_risks(answers))
    elif template_type == "employment":
        flags.extend(_flag_employment_risks(answers))
    elif template_type == "freelance":
        flags.extend(_flag_freelance_risks(answers))

    return flags


def _flag_nda_risks(answers: dict) -> list:
    flags = []

    penalty = answers.get("penalty")
    if penalty == "fixed":
        amount = answers.get("penalty_amount") or answers.get("penaltyAmount")
        try:
            amount_val = float(amount) if amount else 0
        except (TypeError, ValueError):
            amount_val = 0

        flags.append({
            "clause": "liquidated_damages",
            "level": "warning",
            "message": (
                "Fixed-dollar penalty clauses can be struck down by courts "
                "if the amount isn't a reasonable estimate of actual harm. "
                "Recommend attorney review."
            ),
        })
        if amount_val > 250000:
            flags.append({
                "clause": "liquidated_damages",
                "level": "high",
                "message": f"Penalty amount (${amount_val:,.0f}) is unusually high for a standard NDA and risks unenforceability.",
            })

    term_years = answers.get("term")
    try:
        if term_years and float(term_years) > 5:
            flags.append({
                "clause": "term",
                "level": "warning",
                "message": "Confidentiality terms over 5 years are uncommon and may be challenged as overbroad.",
            })
    except (TypeError, ValueError):
        pass

    if not answers.get("jurisdiction"):
        flags.append({
            "clause": "governing_law",
            "level": "info",
            "message": "No governing law selected — this should be set before signing to avoid venue ambiguity.",
        })

    if answers.get("mutual") == "oneway":
        flags.append({
            "clause": "direction",
            "level": "info",
            "message": "One-way NDA protects only one party's disclosures. Ensure your interests are protected if sharing info.",
        })

    return flags


def _flag_lease_risks(answers: dict) -> list:
    flags = []
    deposit = answers.get("security_deposit") or answers.get("deposit")
    rent = answers.get("monthly_rent") or answers.get("rent")
    try:
        if deposit and rent and float(deposit) > float(rent) * 3:
            flags.append({
                "clause": "security_deposit",
                "level": "warning",
                "message": "Security deposit exceeds 3x monthly rent — check local statutory caps.",
            })
    except (TypeError, ValueError):
        pass
    return flags


def _flag_employment_risks(answers: dict) -> list:
    flags = []
    if answers.get("non_compete") == "yes" and not answers.get("non_compete_duration"):
        flags.append({
            "clause": "non_compete",
            "level": "warning",
            "message": "Non-compete included with no stated duration — unenforceable in most jurisdictions without one.",
        })
    return flags


def _flag_freelance_risks(answers: dict) -> list:
    flags = []
    if not answers.get("payment_terms"):
        flags.append({
            "clause": "payment_terms",
            "level": "info",
            "message": "Payment terms (e.g., Net 30) are not specified. It is recommended to include explicit milestones.",
        })
    return flags
