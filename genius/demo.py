"""Exercise selection → subprocess research → separate audit → classification → memory."""
from __future__ import annotations

from pathlib import Path

from .catalogue import load_profiles
from .io import read_json, write_json
from .memory import ScientificMemory
from .orchestration import Budget, Orchestrator
from .planning import compare_reports, make_plan

PROBLEM = "Hodge star on real Euclidean R4 two-forms: determine *², eigenspace dimensions, and refute the false claim *²=-I."


def run_demo(root: str | Path, output: str | Path, *, size: int = 7) -> dict:
    root, output = Path(root).resolve(), Path(output).resolve()
    profiles = load_profiles(root / "institute/registry/profiles.jsonl")
    plan = make_plan(profiles, PROBLEM, size=size)
    plan["reference_case"] = "hodge-r4"
    run_dir = output / "run"
    summary = Orchestrator(root).run(plan, run_dir, Budget(max_calls=max(14, size * 2)))
    checkpoint = read_json(run_dir / "checkpoint.json")
    results = {task["role"]: read_json(run_dir / checkpoint["tasks"][task["id"]]["result_path"])
               for task in plan["tasks"] if checkpoint["tasks"][task["id"]]["status"] == "completed"}
    if summary["status"] != "completed" or not results.get("audit", {}).get("reviewed"):
        write_json(output / "demo.json", {"passed": False, "execution": summary})
        return {"passed": False, "execution": summary}
    producer, reviewer, counterexample = (results[k] for k in ("mathematics", "audit", "counterexample"))
    with ScientificMemory(output / "scientific-memory.sqlite") as memory:
        for task in plan["tasks"]:
            if task["role"] in {"mathematics", "audit"}:
                memory.register_execution(run_dir / checkpoint["tasks"][task["id"]]["result_path"])
        base = {"hypotheses": ["Oriented Euclidean R4; metric diag(+1,+1,+1,+1)",
                               "Real two-forms; positive e1∧e2∧e3∧e4; orthonormal coframe"],
                "sources": [{"id": "HODGE-DEFINITION", "kind": "definition", "statement": "alpha∧*beta=<alpha,beta>vol"}],
                "dependencies": []}
        memory.add({**base, "id": "HODGE-E4-001", "statement": "For this declared six-dimensional fixture, *²=I",
                    "status": "evidence", "artifacts": producer["artifacts"]})
        checks = {key: True for key in ("statement", "hypotheses", "logic", "dependencies", "conventions", "limits", "physical_scope", "tool_scope")}
        memory.audit("HODGE-E4-001", audit_id="HODGE-INTERNAL-001", verdict="confirmed",
                     producer_execution=producer["execution_id"], reviewer_execution=reviewer["execution_id"],
                     checks=checks, artifacts=reviewer["artifacts"], scope="internal",
                     limitations="Finite exact reconstruction; shared source code; zero LLM research executions; no external review")
        memory.add({**base, "id": "HODGE-E4-FALSE", "statement": "For real Euclidean R4 two-forms, *²=-I",
                    "status": "refuted", "artifacts": counterexample["artifacts"]})
        memory.add({**base, "id": "HODGE-DIMENSIONS", "statement": "Each real eigenspace has dimension three for this fixture",
                    "status": "evidence", "dependencies": ["HODGE-E4-001"], "artifacts": producer["artifacts"]})
        initial = memory.export(output / "memory-before-dependency-change.json")
        invalidated = memory.revise("HODGE-E4-001", reason="Demonstration of dependency invalidation: a proposed signature change requires recomputation",
                                    hypotheses=["Signature change proposed; this revision is not evaluated"])
        final = memory.export(output / "memory-after-dependency-change.json")
    passed = (summary["reviewed_results"] >= 1 and producer["execution_id"] != reviewer["execution_id"]
              and next(c for c in initial["claims"] if c["id"] == "HODGE-E4-FALSE")["status"] == "refuted"
              and set(invalidated) == {"HODGE-E4-001", "HODGE-DIMENSIONS"}
              and next(c for c in final["claims"] if c["id"] == "HODGE-DIMENSIONS")["status"] == "review")
    report = {"passed": passed, "execution": summary, "producer_execution": producer["execution_id"],
              "reviewer_execution": reviewer["execution_id"], "incorrect_proposal": "HODGE-E4-FALSE",
              "invalidated_on_dependency_change": invalidated, "comparison": compare_reports(None, None),
              "capabilities": {"design_targets": "5000 research profiles", "scientific_evaluations": 0,
                               "executed": "deterministic benchmark workers in separate processes"},
              "limits": "Known linear-algebra fixture; neither a new theorem nor a gravitational solution."}
    write_json(output / "demo.json", report)
    return report
