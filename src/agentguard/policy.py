from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .models import Decision, PaymentIntent, Verdict

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (the )?(rules|policy|limits)",
    r"you are now", r"system prompt", r"developer mode",
    r"transfer .* to .* immediately", r"do not (tell|inform|ask) (the )?(user|customer)",
    r"override (the )?(limit|policy)", r"act as (an )?admin",
]

_SEVERITY = {Verdict.ALLOW: 0, Verdict.STEP_UP: 1, Verdict.ESCALATE: 2, Verdict.BLOCK: 3}


@dataclass
class Policy:
    per_txn_limit: float = 10_000.0
    daily_limit: float = 25_000.0
    step_up_threshold: float = 5_000.0
    payee_allowlist: Optional[Set[str]] = None     # None = any payee permitted
    payee_names: Dict[str, str] = field(default_factory=dict)  # id -> expected name
    require_consent_for: Set[str] = field(default_factory=lambda: {"loan_disbursal", "card", "neft", "upi"})
    blocked_purposes: Set[str] = field(default_factory=lambda: {"gambling", "crypto_gift_card"})
    allowed_currencies: Set[str] = field(default_factory=lambda: {"INR"})
    escalate_new_payee_over: float = 2_000.0


class PolicyEngine:
    """Deterministic checks applied before any money moves. Most severe verdict wins."""

    def __init__(self, policy: Policy):
        self.policy = policy
        self.spent_today = 0.0

    def reset_day(self) -> None:
        self.spent_today = 0.0

    def evaluate(self, intent: PaymentIntent) -> Decision:
        p = self.policy
        hits: List[tuple] = []

        def hit(v, rid, msg):
            hits.append((v, rid, msg))

        if intent.amount <= 0:
            hit(Verdict.BLOCK, "AMT001", "Non-positive amount")
        if intent.currency not in p.allowed_currencies:
            hit(Verdict.BLOCK, "CUR001", f"Currency {intent.currency} not allowed")
        if intent.amount > p.per_txn_limit:
            hit(Verdict.BLOCK, "LIM001", f"Amount {intent.amount:.0f} exceeds per-transaction limit {p.per_txn_limit:.0f}")
        if self.spent_today + intent.amount > p.daily_limit:
            hit(Verdict.BLOCK, "LIM002", "Daily limit would be exceeded")
        if p.payee_allowlist is not None and intent.payee_id not in p.payee_allowlist:
            if intent.amount > p.escalate_new_payee_over:
                hit(Verdict.ESCALATE, "PAY001", f"Payee {intent.payee_id} not on allowlist")
            else:
                hit(Verdict.STEP_UP, "PAY002", f"New payee {intent.payee_id} needs confirmation")
        expected = p.payee_names.get(intent.payee_id)
        if expected and intent.payee_name and expected.lower() != intent.payee_name.lower():
            hit(Verdict.BLOCK, "PAY003", f"Payee name mismatch: expected '{expected}', got '{intent.payee_name}'")
        if intent.channel in p.require_consent_for and not intent.consent_token:
            hit(Verdict.BLOCK, "CON001", "Missing user consent token")
        if intent.purpose.lower() in p.blocked_purposes:
            hit(Verdict.BLOCK, "PUR001", f"Purpose '{intent.purpose}' blocked")
        text = intent.source_text.lower()
        for pat in INJECTION_PATTERNS:
            if re.search(pat, text):
                hit(Verdict.ESCALATE, "INJ001", f"Possible prompt injection: /{pat}/")
                break
        if intent.amount >= p.step_up_threshold:
            hit(Verdict.STEP_UP, "STP001", "Amount above step-up threshold")

        if not hits:
            return Decision(Verdict.ALLOW, ["All checks passed"], [])
        worst = max(hits, key=lambda h: _SEVERITY[h[0]])[0]
        return Decision(worst, [h[2] for h in hits], [h[1] for h in hits])

    def commit(self, intent: PaymentIntent) -> None:
        self.spent_today += intent.amount
