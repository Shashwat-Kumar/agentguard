"""AgentGuard: guardrails and tests for AI agents that move money."""
from .models import PaymentIntent, Decision, Verdict
from .policy import Policy, PolicyEngine
from .simulator import Simulator, Scenario, load_scenarios
from .agents import MockAgent, NaiveAgent

__all__ = ["PaymentIntent", "Decision", "Verdict", "Policy", "PolicyEngine",
           "Simulator", "Scenario", "load_scenarios", "MockAgent", "NaiveAgent"]
__version__ = "0.1.0"
