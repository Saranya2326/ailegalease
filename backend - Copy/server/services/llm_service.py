"""
LLM Service with intelligent Anthropic integration and deterministic fallback engine.

The LLM is used to phrase clauses and produce plain-English explanations.
If no ANTHROPIC_API_KEY is configured or the API is unavailable,
a high-fidelity fallback legal engine generates valid, structured clauses
and clear explanations so the application works seamlessly in all environments.
"""
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

TEMPLATE_SYSTEM_PROMPTS = {
    "nda": (
        "You are a legal drafting assistant. Given structured answers about "
        "an NDA, draft numbered clauses in plain, standard contract language. "
        "Do not add clauses the user did not ask for. Do not give legal advice "
        "or opinions on enforceability — that is handled separately. "
        "Return ONLY the drafted clause text, no preamble."
    ),
    "lease": (
        "You are a legal drafting assistant. Given structured answers about "
        "a residential lease, draft numbered clauses in plain, standard "
        "contract language. Return ONLY the drafted clause text, no preamble."
    ),
    "employment": (
        "You are a legal drafting assistant. Given structured answers about "
        "an employment agreement, draft numbered clauses in plain, standard "
        "contract language. Return ONLY the drafted clause text, no preamble."
    ),
    "freelance": (
        "You are a legal drafting assistant. Given structured answers about "
        "a freelance/independent contractor agreement, draft numbered clauses in "
        "plain, standard contract language. Return ONLY the drafted clause text, no preamble."
    ),
    "will": (
        "You are a legal drafting assistant. Given structured answers about "
        "a last will and testament, draft numbered clauses in plain, standard "
        "legal language. Return ONLY the drafted clause text, no preamble."
    ),
    "poa": (
        "You are a legal drafting assistant. Given structured answers about "
        "a power of attorney, draft numbered clauses in plain, standard "
        "legal language. Return ONLY the drafted clause text, no preamble."
    ),
}


def _get_anthropic_client():
    api_key = current_app.config.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.warning(f"Could not initialize Anthropic client: {e}")
        return None


def draft_document(template_type: str, answers: dict) -> str:
    """Call the LLM to draft clause text from structured wizard answers with fallback."""
    client = _get_anthropic_client()
    
    if client:
        try:
            system_prompt = TEMPLATE_SYSTEM_PROMPTS.get(
                template_type, TEMPLATE_SYSTEM_PROMPTS.get("nda")
            )
            response = client.messages.create(
                model=current_app.config.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Document type: {template_type}\n"
                            f"Answers (JSON): {json.dumps(answers)}\n\n"
                            "Draft the numbered contract clauses now."
                        ),
                    }
                ],
            )
            text = "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Anthropic drafting failed ({e}); using template generator.")

    return _generate_fallback_document(template_type, answers)


def explain_clause(clause_text: str) -> str:
    """Return a short plain-English explanation of a single clause with fallback."""
    client = _get_anthropic_client()
    
    if client:
        try:
            response = client.messages.create(
                model=current_app.config.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                max_tokens=250,
                system=(
                    "Explain the following contract clause in 1-3 plain-English "
                    "sentences for someone with no legal background. Do not give "
                    "legal advice or an opinion on whether they should sign."
                ),
                messages=[{"role": "user", "content": clause_text}],
            )
            text = "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Anthropic clause explanation failed ({e}); using fallback explanation.")

    return _generate_fallback_explanation(clause_text)


def _generate_fallback_document(template_type: str, answers: dict) -> str:
    """Deterministic, high-quality legal clause drafting engine."""
    party_a = answers.get("party_a") or answers.get("partyA") or "[Disclosing Party / Company]"
    party_b = answers.get("party_b") or answers.get("partyB") or "[Receiving Party / Contractor]"
    effective_date = answers.get("effective_date") or answers.get("effDate") or "[Effective Date]"
    jurisdiction = answers.get("jurisdiction") or "[State / Jurisdiction]"
    term = answers.get("term", "2")
    term_unit = "year" if str(term) == "1" else "years"
    is_mutual = answers.get("mutual") != "oneway"
    penalty = answers.get("penalty")
    penalty_amount = answers.get("penalty_amount") or answers.get("penaltyAmount") or "0"

    if template_type == "nda":
        direction_text = (
            "Each party agrees to hold all Confidential Information in strict confidence and use it solely for evaluating or engaging in a business relationship."
            if is_mutual else
            f"{party_b} agrees to hold all Confidential Information disclosed by {party_a} in strict confidence and solely for the intended business purpose."
        )

        clauses = [
            f"1. Parties. This Non-Disclosure Agreement (\"Agreement\") is entered into and made effective as of {effective_date}, by and between {party_a} and {party_b} (collectively, the \"Parties\").",
            f"2. Confidential Information. For purposes of this Agreement, \"Confidential Information\" shall include all proprietary information, trade secrets, business plans, technical data, source code, and customer records disclosed by one party to the other. {direction_text}",
            f"3. Non-Disclosure & Standard of Care. The receiving party shall maintain the confidentiality of the disclosed information using at least the same degree of care it uses for its own confidential materials, but in no event less than reasonable care.",
            f"4. Term & Duration. The confidentiality obligations set forth in this Agreement shall remain in full force and effect for a period of {term} {term_unit} from the effective date.",
        ]

        clause_num = 5
        if penalty == "fixed":
            try:
                amt_str = f"${float(penalty_amount):,.2f}"
            except (ValueError, TypeError):
                amt_str = f"${penalty_amount}"
            clauses.append(
                f"{clause_num}. Liquidated Damages. In the event of a material breach of confidentiality obligations under this Agreement, the breaching party agrees to pay the non-breaching party the sum of {amt_str} as pre-estimated liquidated damages."
            )
            clause_num += 1

        clauses.append(
            f"{clause_num}. Governing Law. This Agreement shall be construed, interpreted, and governed in accordance with the substantive laws of the State of {jurisdiction}, without regard to its conflict of law principles."
        )
        clause_num += 1
        clauses.append(
            f"{clause_num}. Entire Agreement. This Agreement constitutes the complete understanding between the Parties with respect to the subject matter hereof and supersedes all prior agreements."
        )
        return "\n\n".join(clauses)

    elif template_type == "lease":
        rent = answers.get("monthly_rent") or answers.get("rent") or "$2,000"
        deposit = answers.get("security_deposit") or answers.get("deposit") or "$2,000"
        address = answers.get("property_address") or "[Property Address]"
        return "\n\n".join([
            f"1. Parties and Premises. This Residential Lease Agreement is between {party_a} (\"Landlord\") and {party_b} (\"Tenant\") for the premises located at {address}, effective {effective_date}.",
            f"2. Term. The lease term shall be for {term} {term_unit} commencing on {effective_date}.",
            f"3. Rent and Security Deposit. Monthly rent shall be {rent}, payable on the 1st of each calendar month. Tenant agrees to provide a security deposit of {deposit} upon signing.",
            f"4. Governing Law. This Agreement is governed by the laws of the State of {jurisdiction}."
        ])

    elif template_type == "employment":
        position = answers.get("position_title") or "Professional"
        salary = answers.get("salary") or "$80,000"
        return "\n\n".join([
            f"1. Employment Relationship. {party_a} (\"Employer\") agrees to employ {party_b} (\"Employee\") in the role of {position}, effective {effective_date}.",
            f"2. Compensation. Employer shall pay Employee a base compensation of {salary} subject to applicable tax withholdings.",
            f"3. Confidentiality and Inventions. Employee agrees to protect Employer's proprietary information and assign work product created in the course of employment.",
            f"4. Governing Law. This Agreement is governed by the laws of the State of {jurisdiction}."
        ])

    elif template_type == "freelance":
        services = answers.get("services_description") or "Consulting and development services"
        fee = answers.get("fee") or "$5,000"
        return "\n\n".join([
            f"1. Engagement. {party_a} (\"Client\") engages {party_b} (\"Contractor\") to perform the following services: {services}.",
            f"2. Compensation. Client agrees to pay Contractor the sum of {fee} according to the agreed milestone schedule.",
            f"3. Independent Contractor Status. Contractor is an independent contractor and not an employee or agent of Client.",
            f"4. Governing Law. This Agreement is governed by the laws of the State of {jurisdiction}."
        ])

    else:
        return "\n\n".join([
            f"1. Parties. This document is entered into by {party_a} and {party_b}, effective {effective_date}.",
            f"2. Obligations. The parties agree to perform the mutual responsibilities outlined in this draft.",
            f"3. Governing Law. This Agreement shall be governed by the laws of the State of {jurisdiction}."
        ])


def _generate_fallback_explanation(clause_text: str) -> str:
    """Provide helpful plain-English explanation when LLM is offline."""
    lower = clause_text.lower()
    if "parties" in lower or "entered into" in lower:
        return "Identifies who is legally bound by the agreement. Both parties must be accurately named with their legal identities."
    elif "confidential" in lower or "proprietary" in lower:
        return "Defines what information counts as protected and sets the duty for the receiving party to prevent unauthorized leaks."
    elif "term" in lower or "duration" in lower or "period" in lower:
        return "Specifies how long the agreement or confidentiality obligation stays in force after signing."
    elif "liquidated damages" in lower or "penalty" in lower or "breach" in lower:
        return "Pre-determines a specific dollar amount to be paid if a breach occurs, avoiding complex damage calculations in court."
    elif "governing law" in lower or "jurisdiction" in lower:
        return "Determines which state's legal rules and court system apply if any dispute arises between the parties."
    elif "entire agreement" in lower or "supersedes" in lower:
        return "Confirms that this document contains the final and full agreement, replacing any prior spoken or written promises."
    else:
        return "This standard legal clause defines rights and duties of the signing parties in plain contractual terms."
