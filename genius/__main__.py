"""Local CLI; no dependencies and no external calls unless a live backend is chosen."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from . import __version__
from .io import read_json, write_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m genius", description="GENIUS-5000 reproducible research institute")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("generate")
    sub.add_parser("validate")
    profile = sub.add_parser("profile")
    profile.add_argument("id")
    plan = sub.add_parser("plan")
    plan.add_argument("problem")
    plan.add_argument("--team-size", type=int, default=7)
    plan.add_argument("--backend", choices=["reference", "claude", "codex"], default="reference")
    plan.add_argument("--model")
    plan.add_argument("--reference-case", choices=["hodge-r4"])
    plan.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("plan", type=Path)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--concurrency", type=int, default=2)
    run.add_argument("--max-calls", type=int, default=14)
    run.add_argument("--max-seconds", type=float, default=120)
    run.add_argument("--task-seconds", type=float, default=25)
    run.add_argument("--retries", type=int, default=1)
    run.add_argument("--max-input-bytes", type=int, default=120000)
    run.add_argument("--max-output-bytes", type=int, default=200000)
    run.add_argument("--max-usd", type=float)
    demo = sub.add_parser("demo")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--team-size", type=int, default=7)
    install = sub.add_parser("install")
    install.add_argument("--target", type=Path, required=True)
    install.add_argument("--dry-run", action="store_true")
    compare = sub.add_parser("compare")
    compare.add_argument("--claude", type=Path)
    compare.add_argument("--codex", type=Path)
    compare.add_argument("--output", type=Path)
    pair = sub.add_parser("prepare-pair")
    pair.add_argument("brief", type=Path, help="JSON containing problem, conventions, criteria, budgets, documentary_base")
    pair.add_argument("--output", type=Path, required=True)
    for name in ("seal-report", "seal-review"):
        step = sub.add_parser(name)
        step.add_argument("directory", type=Path)
        step.add_argument("provider", choices=["claude", "codex"])
        step.add_argument("report", type=Path)
    for name in ("prepare-cross-review", "synthesize"):
        step = sub.add_parser(name)
        step.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "doctor":
            from .adapters import available
            tools = {}
            for name in ("codex", "claude", "scipython", "lean", "sage", "Singular", "M2", "pdftxt", "gh", "git"):
                path = shutil.which(name)
                tools[name] = {"available": bool(path), "path": path, "version": "not probed"}
                if path and name in {"codex", "claude", "git"}:
                    result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=10)
                    tools[name]["version"] = result.stdout.strip()
            result = {"genius": __version__, "python": platform.python_version(), "adapters": available(),
                      "tools": tools, "network_and_authentication": "Not tested; availability is not a successful model execution"}
        elif args.command == "generate":
            from .catalogue import write_catalogue
            result = write_catalogue(root)
        elif args.command == "validate":
            from .catalogue import load_profiles, validate_profiles
            from .skills import validate_skills
            from .planning import select_team
            profiles = load_profiles(root / "institute/registry/profiles.jsonl")
            registry = validate_profiles(profiles)
            skills = validate_skills(root)
            initial = select_team(profiles, "Googly twistor gravity research", 30)
            result = {"valid": registry["valid"] and skills["valid"], "registry": registry, "skills": skills,
                      "stage_a": {"initial_selection": len(initial["selected_profiles"]),
                                  "functions": sorted({a["role"] for a in initial["assignments"]}),
                                  "executions": 0, "scope": "selection/coverage only; no scientific ability certified"}}
        elif args.command == "profile":
            from .catalogue import load_profiles
            result = next(p for p in load_profiles(root / "institute/registry/profiles.jsonl") if p["id"] == args.id)
        elif args.command == "plan":
            from .catalogue import load_profiles
            from .planning import make_plan, validate_plan
            result = make_plan(load_profiles(root / "institute/registry/profiles.jsonl"), args.problem,
                               size=args.team_size, backend=args.backend, model=args.model)
            if args.reference_case:
                result["reference_case"] = args.reference_case
            validate_plan(result)
            write_json(args.output, result)
        elif args.command == "run":
            from .orchestration import Budget, Orchestrator
            budget = Budget(**{key: getattr(args, key) for key in asdict(Budget())})
            result = Orchestrator(root).run(read_json(args.plan), args.output, budget, resume=args.resume)
        elif args.command == "demo":
            from .demo import run_demo
            result = run_demo(root, args.output, size=args.team_size)
        elif args.command == "install":
            from .install import install_project
            result = install_project(root, args.target, dry_run=args.dry_run)
        elif args.command == "prepare-pair":
            from .planning import prepare_comparison
            result = prepare_comparison(args.output, **read_json(args.brief))
        elif args.command in {"seal-report", "seal-review", "prepare-cross-review", "synthesize"}:
            from . import cross_review
            action = getattr(cross_review, args.command.replace("-", "_"))
            if args.command in {"seal-report", "seal-review"}:
                result = action(args.directory, args.provider, args.report)
            else:
                result = action(args.directory)
        else:
            from .planning import compare_reports
            result = compare_reports(read_json(args.claude) if args.claude else None,
                                     read_json(args.codex) if args.codex else None)
            if args.output:
                write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("valid") is False or result.get("passed") is False or result.get("status") == "incomplete" or result.get("complete") is False:
            return 1
        return 0
    except (ValueError, OSError, KeyError, StopIteration, subprocess.SubprocessError) as error:
        print(json.dumps({"error": f"{type(error).__name__}: {error}"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
