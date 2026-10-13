import argparse, json, sys
from .agents import MockAgent, NaiveAgent
from .simulator import Simulator, load_scenarios, render_markdown

def main(argv=None):
    ap = argparse.ArgumentParser(prog="agentguard", description="Run AgentGuard money-movement scenarios")
    ap.add_argument("--agent", choices=["naive", "mock"], default="naive")
    ap.add_argument("--no-policy", action="store_true", help="Run without the policy engine (baseline)")
    ap.add_argument("--scenarios", help="Path to a scenarios JSON file")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--min-score", type=float, default=0, help="Exit 1 if score below this (for CI)")
    a = ap.parse_args(argv)
    agent = NaiveAgent() if a.agent == "naive" else MockAgent()
    rep = Simulator(agent, use_policy=not a.no_policy).run(load_scenarios(a.scenarios))
    print(json.dumps(rep, indent=2) if a.format == "json" else render_markdown(rep))
    return 0 if rep["score"] >= a.min_score else 1

if __name__ == "__main__":
    sys.exit(main())
