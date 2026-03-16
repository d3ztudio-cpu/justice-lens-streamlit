from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class GroqClient:
    api_key: str

    def chat(self, *, model: str, prompt: str, timeout_s: int) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
        r = requests.post(url, headers=headers, json=data, timeout=timeout_s)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


LEGAL_ANCHOR = """
INTERNAL REFERENCE (ABSOLUTE TRUTH):
- Section 70: Protected Systems. Definition: Unauthorized access to systems declared as critical infrastructure by the Government. Punishment = Up to 10 years.
- Section 67A: Sexually Explicit Content. Definition: Publishing or transmitting material containing sexually explicit acts in electronic form. Punishment = 5-7 years + 10 Lakh fine.
- Section 66F: Cyber Terrorism. Definition: Acts done with intent to threaten unity, integrity, or security of India via computer. Punishment = LIFE IMPRISONMENT.
- Section 66E: Violation of Privacy. Definition: Intentionally capturing or publishing private images of any person without consent. Punishment = 3 years / 2 Lakh fine.
- Section 43A: Corporate Data Negligence. Definition: Failure by a body corporate to implement reasonable security practices for sensitive data. Punishment = Compensation ONLY.
- Section 66B: Stolen Computer Resource. Punishment = 3 years / 5 Lakh fine.
"""

CASE_HISTORY = """
HISTORICAL PRECEDENTS (USE FOR SCENARIOS):
- Hacking/Unauthorized Access: State of Tamil Nadu vs. Suhas Katti (2004).
- Data Negligence: Shreya Singhal vs. Union of India (2015).
- Financial Fraud: CBI vs. Arif Azim (Sony Sambandh Case).
"""


def _normalize_intent_category(raw_category: str) -> str:
    upper = str(raw_category or "").strip().upper()
    for known in ("PHYSICAL", "CYBER_SCENARIO", "CYBER_EXPLAIN", "NON_LEGAL"):
        if known in upper:
            return known
    return "NON_LEGAL"


def classify_intent(groq: GroqClient, user_input: str) -> str:
    classifier_prompt = f"""
Analyze the user input: "{user_input}"
Categories:
1. PHYSICAL: Related to physical crimes (theft, assault).
2. CYBER_SCENARIO: A real-life cyber problem/victim situation.
3. CYBER_EXPLAIN: A direct request for legal definitions (e.g. "Explain 70").
4. NON_LEGAL: General/site/developer questions not asking cyber legal help.
Respond with ONLY the category name.
"""
    try:
        raw = groq.chat(model="llama-3.1-8b-instant", prompt=classifier_prompt, timeout_s=10)
        return _normalize_intent_category(raw)
    except Exception:
        return "PHYSICAL"


def _validate_ai_answer(category: str, answer: str) -> bool:
    if not answer or not isinstance(answer, str):
        return False

    upper = answer.upper()

    if "EXPLAIN" in str(category).upper():
        banned = ("WIN PROBABILITY", "ACTION PLAN", "CASE HISTORY")
        if any(x in upper for x in banned):
            return False
        required = ("OFFICIAL TITLE", "DEFINITION", "PUNISHMENT")
        return all(x in upper for x in required)

    required = ("RELEVANT SECTIONS", "PUNISHMENTS", "CASE HISTORY", "WIN PROBABILITY", "ACTION PLAN")
    return all(x in upper for x in required)


def ask_groq_lawyer(groq: GroqClient, user_input: str, law_evidence: str, category: str) -> str:
    if "EXPLAIN" in str(category).upper():
        system_prompt = f"""
{LEGAL_ANCHOR}
You are a Precise Legal Reference Tool.
- Provide: OFFICIAL TITLE, DEFINITION, and EXACT PUNISHMENT.
- STRICT RULE: DO NOT provide 'Win Probability', 'Action Plan', or 'Case History'.
- Use the definitions exactly as provided in the INTERNAL REFERENCE.
"""
    else:
        system_prompt = f"""
{LEGAL_ANCHOR}
{CASE_HISTORY}
You are an Expert Cyber Law Consultant. Use this EXACT format:
⚖️ RELEVANT SECTIONS: [Cite sections]
⚖️ PUNISHMENTS: [List jail/compensation]
📚 CASE HISTORY: [Cite landmark case]
📊 WIN PROBABILITY: [Percentage] - [Reasoning]
🚀 ACTION PLAN:
1. Notify CERT-In (www.cert-in.org.in) within 6 hours.
2. File complaint at www.cybercrime.gov.in.
3. Appoint a Cyber Forensic Auditor.
"""

    full_prompt = f"{system_prompt}\nUSER QUERY: {user_input}\nDATABASE EVIDENCE: {law_evidence}"
    try:
        return groq.chat(model="llama-3.1-8b-instant", prompt=full_prompt, timeout_s=18)
    except Exception:
        return "⚠️ AI Engine Error."


def _repair_ai_answer(
    groq: GroqClient, *, user_input: str, law_evidence: str, category: str, bad_answer: str
) -> str:
    if "EXPLAIN" in str(category).upper():
        repair_prompt = f"""
{LEGAL_ANCHOR}
Rewrite the following draft to STRICTLY follow this exact format (include all headings):
1) OFFICIAL TITLE:
2) DEFINITION:
3) EXACT PUNISHMENT:
- Do NOT include: Win Probability, Action Plan, Case History, steps, URLs, or extra sections.
- Use definitions and punishments exactly as provided in INTERNAL REFERENCE.

USER QUERY: {user_input}
DATABASE EVIDENCE: {law_evidence}
DRAFT (FIX THIS): {bad_answer}
"""
    else:
        repair_prompt = f"""
{LEGAL_ANCHOR}
{CASE_HISTORY}
Rewrite the following draft to STRICTLY follow this exact format (include all headings):
⚖️ RELEVANT SECTIONS: ...
⚖️ PUNISHMENTS: ...
📚 CASE HISTORY: ...
📊 WIN PROBABILITY: ...
🚀 ACTION PLAN:
1. ...
2. ...
3. ...

USER QUERY: {user_input}
DATABASE EVIDENCE: {law_evidence}
DRAFT (FIX THIS): {bad_answer}
"""
    try:
        return groq.chat(model="llama-3.1-8b-instant", prompt=repair_prompt, timeout_s=18)
    except Exception:
        return bad_answer


def ask_groq_lawyer_validated(groq: GroqClient, user_input: str, law_evidence: str, category: str) -> str:
    answer = ask_groq_lawyer(groq, user_input, law_evidence, category)
    if _validate_ai_answer(category, answer):
        return answer
    repaired = _repair_ai_answer(groq, user_input=user_input, law_evidence=law_evidence, category=category, bad_answer=answer)
    return repaired if _validate_ai_answer(category, repaired) else answer


@dataclass(frozen=True)
class ChatResult:
    category: str
    answer: str
    evidence: Optional[str] = None
