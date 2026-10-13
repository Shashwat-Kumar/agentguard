from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Verdict(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    STEP_UP = "step_up"        # needs additional approval (OTP / human)
    ESCALATE = "escalate"      # hand to a human operator


@dataclass
class PaymentIntent:
    """A money movement an agent proposes to execute."""
    payee_id: str
    amount: float
    currency: str = "INR"
    purpose: str = ""
    channel: str = "upi"            # upi | card | neft | loan_disbursal
    consent_token: Optional[str] = None
    source_text: str = ""           # text that caused the intent (for injection checks)
    payee_name: str = ""


@dataclass
class Decision:
    verdict: Verdict
    reasons: List[str] = field(default_factory=list)
    rule_ids: List[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.verdict == Verdict.ALLOW
