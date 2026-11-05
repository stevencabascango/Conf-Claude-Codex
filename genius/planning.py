"""Transparent team selection; a catalogue entry is never an executed agent."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .io import now, write_json

ROLES = ("conceptual", "mathematics", "physics", "computation", "counterexample", "audit", "integration")
PROGRAM_TERMS = {
    "googly": ("googly", "twistor", "helicity", "helicidad", "penrose", "newman"),
    "quantum_gravity": ("gravity", "gravedad", "lqg", "spin", "hodge", "einstein"),
    "unified_field_theory": ("unification", "unificación", "gauge", "unified", "yang", "matter"),
}
ROLE_DIVISIONS = {
    "conceptual": {"rg", "twistors", "integration"},
    "mathematics": {"topology", "algebraic_geometry", "categories", "twistors"},
    "physics": {"rg", "qft", "lqg", "strings"},
    "computation": {"computation"}, "counterexample": {"topology", "integration", "computation"},
    "audit": {"integration", "computation"}, "integration": {"integration"},
}


def select_team(profiles: list[dict], problem: str, size: int = 7) -> dict:
    if not 3 <= size <= 50 or len(profiles) < size:
        raise ValueError("Team size must be 3–50 and fit the registry")
    if not problem.strip():
        raise ValueError("Problem cannot be empty")
    terms = set(re.findall(r"[\w-]+", problem.casefold()))
    programmes = [p for p, words in PROGRAM_TERMS.items() if any(word in problem.casefold() for word in words)]
    chosen: list[dict] = []
    assignments = []
    for index in range(max(size, len(ROLES))):
        role = ROLES[index % len(ROLES)]
        # Small teams combine functions, but every function gets its own execution.
        reuse = size < len(ROLES) and len(chosen) >= size
        candidates = chosen if reuse else [p for p in profiles if p["id"] not in {c["id"] for c in chosen}]
        if role == "audit":
            producer = next(a["profile_id"] for a in assignments if a["role"] == "mathematics")
            candidates = [p for p in candidates if p["id"] != producer]
        def score(p):
            tags = set(p.get("selection_tags", []))
            searchable = set(re.findall(r"[\w-]+", str(p.get("specialty", "")).casefold()))
            value = 15 * (role in tags) + 8 * (p["division"] in ROLE_DIVISIONS[role])
            value += 7 * len(set(programmes) & tags) + len(terms & searchable)
            tie = hashlib.sha256((problem + role + p["id"]).encode()).hexdigest()
            return value, tie
        profile = max(candidates, key=score)
        if not reuse:
            chosen.append(profile)
        assignments.append({"role": role, "profile_id": profile["id"], "selection_score": score(profile)[0]})
    return {"registered_profiles": len(profiles), "selected_profiles": [p["id"] for p in chosen],
            "assignments": assignments, "programmes": programmes,
            "selection_method": "Deterministic tag/specialty coverage; not an estimate of scientific ability"}


def make_plan(profiles: list[dict], problem: str, *, size: int = 7,
              backend: str = "reference", model: str | None = None) -> dict:
    if backend not in {"reference", "claude", "codex"}:
        raise ValueError("Unknown backend")
    selected = select_team(profiles, problem, size)
    tasks = []
    for i, assignment in enumerate(selected["assignments"], 1):
        role = assignment["role"]
        if role == "conceptual":
            previous = []
        elif role in {"mathematics", "physics", "computation"}:
            previous = [t["id"] for t in tasks if t["role"] == "conceptual"]
        elif role == "counterexample":
            previous = [t["id"] for t in tasks if t["role"] in {"mathematics", "physics", "computation"}]
        elif role == "audit":
            previous = [t["id"] for t in tasks if t["role"] in {"mathematics", "physics", "computation", "counterexample"}]
        else:
            previous = [t["id"] for t in tasks if t["role"] == "audit"]
        tasks.append({"id": f"task-{i:03d}", **assignment, "dependencies": previous})
    return {"schema_version": "1.0", "created": now(), "problem": problem,
            "backend": backend, "requested_model": model, **selected, "tasks": tasks,
            "reference_scope": "reference backend only accepts the built-in Euclidean R4 Hodge benchmark",
            "counters": {"agents_executed": 0, "completed_executions": 0, "reviewed_results": 0}}


def validate_plan(plan: dict) -> None:
    if not isinstance(plan.get("problem"), str) or not plan["problem"].strip():
        raise ValueError("Missing problem")
    known = set()
    selected = plan.get("selected_profiles", [])
    if len(selected) != len(set(selected)) or not 3 <= len(selected) <= 50:
        raise ValueError("Selected profiles must be unique (3–50 entries)")
    if plan.get("registered_profiles", 0) < len(selected):
        raise ValueError("Selected profiles cannot exceed the registry")
    for task in plan["tasks"]:
        if task["id"] in known or not re.fullmatch(r"[a-zA-Z0-9_-]+", task["id"]):
            raise ValueError("Task IDs must be unique and path-safe")
        if task["role"] not in ROLES or not set(task["dependencies"]).issubset(known):
            raise ValueError("Tasks must be a topologically ordered acyclic graph with known roles")
        if task["profile_id"] not in plan["selected_profiles"]:
            raise ValueError("Task profile was not selected")
        known.add(task["id"])
    if not plan["tasks"] or not set(ROLES).issubset({t["role"] for t in plan["tasks"]}):
        raise ValueError("Every research function must be covered")
    for audit in (t for t in plan["tasks"] if t["role"] == "audit"):
        if not any(t["role"] == "mathematics" and t["id"] in audit["dependencies"]
                   and t["profile_id"] != audit["profile_id"] for t in plan["tasks"]):
            raise ValueError("Auditor needs another profile's mathematical execution as input")


def prepare_comparison(root: str | Path, problem: str, conventions: dict,
                       criteria: list[str], budgets: dict, documentary_base: list | None = None) -> dict:
    """Write identical briefs into separate phase-one workspaces, without results."""
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise ValueError("Comparison directory is not empty; preserve existing briefs and seals")
    brief = {"problem": problem, "conventions": conventions, "criteria": criteria,
             "budgets": budgets, "documentary_base": documentary_base or [],
             "protocol": "Develop separately. Seal both reports before cross-review."}
    import json
    fingerprint = hashlib.sha256(json.dumps(brief, sort_keys=True).encode()).hexdigest()
    for provider in ("claude", "codex"):
        write_json(root / provider / "brief.json", brief)
    manifest = {"brief_sha256": fingerprint, "phase": "independent-development",
                "reports": {}, "status": "pending", "limitations":
                "Different folders/contexts are administrative separation, not a security boundary or independent training."}
    write_json(root / "comparison.json", manifest)
    return manifest


def compare_reports(claude: dict | None, codex: dict | None) -> dict:
    """Compare reported claims, never promote on consensus or missing evidence."""
    absent = [name for name, report in (("claude", claude), ("codex", codex)) if not report or report.get("status") != "completed"]
    if absent:
        return {"status": "pending", "missing_reports": absent, "agreements": [], "disagreements": [],
                "next_step": "Complete and seal both reports; failures are not scientific reports."}
    by_provider = [{c["id"]: c for c in report.get("claims", [])} for report in (claude, codex)]
    agreements, disagreements = [], []
    for key in sorted(set(by_provider[0]) | set(by_provider[1])):
        a, b = by_provider[0].get(key), by_provider[1].get(key)
        target = agreements if a and b and a.get("statement") == b.get("statement") and a.get("status") == b.get("status") else disagreements
        target.append({"id": key, "claude": a, "codex": b})
    return {"status": "ready_for_cross_review", "agreements": agreements, "disagreements": disagreements,
            "cross_reviews": {"claude_reviews_codex": "pending", "codex_reviews_claude": "pending"},
            "next_step": "Reconstruct central arguments in two new executions; retain unresolved disagreements."}
