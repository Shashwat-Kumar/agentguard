"""Mock agents. Real agents plug in by implementing `propose(scenario) -> PaymentIntent | None`."""
from __future__ import annotations
import re
from typing import Optional
from .models import PaymentIntent


class NaiveAgent:
    """Does whatever the request text says. Useful as a worst case: shows what the policy catches."""
    name = "naive"

    def propose(self, sc) -> Optional[PaymentIntent]:
        return PaymentIntent(**sc.intent)


class MockAgent:
    """A slightly careful rule-based agent: refuses obvious injections and missing consent itself."""
    name = "mock-careful"

    def propose(self, sc) -> Optional[PaymentIntent]:
        it = PaymentIntent(**sc.intent)
        if re.search(r"ignore (all )?previous instructions", it.source_text, re.I):
            return None
        if not it.consent_token:
            return None
        return it
