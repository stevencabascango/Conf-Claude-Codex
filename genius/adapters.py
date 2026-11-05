"""Real CLI adapters and a deterministic, explicitly non-LLM reference worker."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def available() -> dict:
    return {"reference": {"available": True, "kind": "deterministic-worker"},
            **{p: {"available": shutil.which(p) is not None, "kind": "llm-cli",
                   "authentication": "not tested", "executable": shutil.which(p)}
               for p in ("claude", "codex")}}


def command(backend: str, workspace: Path, request_path: Path,
            model: str | None = None, max_usd: float | None = None) -> list[str]:
    if backend == "reference":
        return [sys.executable, "-m", "genius.worker", str(request_path)]
    if not shutil.which(backend):
        raise FileNotFoundError(f"{backend} CLI is not installed")
    if backend == "codex":
        if max_usd is not None:
            raise ValueError("This Codex CLI has no verified hard USD cap; use call/time/byte budgets")
        args = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-C", str(workspace), "-"]
        if model:
            args.extend(["--model", model])
        return args
    if backend == "claude":
        args = ["claude", "--print", "--output-format", "json", "--no-session-persistence"]
        if model:
            args.extend(["--model", model])
        if max_usd is not None:
            args.extend(["--max-budget-usd", str(max_usd)])
        return args
    raise ValueError(f"Unknown backend: {backend}")


def parse_response(backend: str, stdout: str) -> dict:
    if backend == "reference":
        value = json.loads(stdout)
        if not isinstance(value, dict):
            raise ValueError("Worker response must be an object")
        return value
    if backend == "claude":
        value = json.loads(stdout)
        if not isinstance(value, dict) or value.get("type") != "result" or not isinstance(value.get("result"), str) or not value["result"].strip():
            raise ValueError("Claude did not return a nonempty completed result")
        if value.get("is_error"):
            raise ValueError(f"Claude reported an error: {value.get('subtype', 'unknown')}")
        models = list(value.get("modelUsage", {}))
        return {"backend": backend, "report": value.get("result", ""), "usage": value.get("usage"),
                "reported_models": models, "cost_usd": value.get("total_cost_usd"),
                "claims": [], "classification": "pending_human_ingestion",
                "limitations": ["Free-text reports do not automatically create or promote scientific claims."]}
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    if any(e.get("type") in {"error", "turn.failed"} for e in events):
        raise ValueError("Codex reported a failed turn; inspect the retained log")
    if not any(e.get("type") == "turn.completed" for e in events):
        raise ValueError("No completed Codex turn was reported")
    text = [e.get("item", {}).get("text", "") for e in events
            if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
    usage = [e.get("usage") for e in events if e.get("type") == "turn.completed"]
    models = sorted({e["model"] for e in events if isinstance(e.get("model"), str)})
    return {"backend": backend, "report": "\n".join(text), "usage": usage,
            "reported_models": models, "claims": [], "classification": "pending_human_ingestion",
            "limitations": ["Model identity may not be reported by this CLI; requested model is recorded separately."]}
