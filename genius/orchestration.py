"""Bounded, resumable subprocess orchestration with an auditable checkpoint.

Hard budgets cover calls, time, input bytes and captured output bytes. These
are NOT token/cost guarantees for a CLI that does not expose such controls.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import time

from . import adapters
from .io import digest, now, read_json, write_json
from .planning import validate_plan

ROLE_SKILLS = {
    "conceptual": ("first-principles-reasoning", "thought-experiment-design"),
    "mathematics": ("rigorous-proof", "theorem-discovery"),
    "physics": ("mathematical-relativity", "physical-consistency-audit"),
    "computation": ("physical-consistency-audit", "research-memory"),
    "counterexample": ("counterexample-search",),
    "audit": ("independent-proof-audit", "physical-consistency-audit"),
    "integration": ("research-memory", "scientific-paper-writing"),
}


@dataclass(frozen=True)
class Budget:
    concurrency: int = 2
    max_calls: int = 14
    max_seconds: float = 120
    task_seconds: float = 25
    retries: int = 1
    max_input_bytes: int = 120_000
    max_output_bytes: int = 200_000
    max_usd: float | None = None

    def validate(self):
        for name in ("concurrency", "max_calls", "max_input_bytes", "max_output_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("max_seconds", "task_seconds"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if type(self.retries) is not int or not 0 <= self.retries <= 5:
            raise ValueError("Retries must be an integer from 0 to 5")
        if self.max_usd is not None and (not math.isfinite(self.max_usd) or self.max_usd <= 0):
            raise ValueError("USD budget must be positive and finite")


def _redact(text: str) -> str:
    return re.sub(r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,})", "[REDACTED]", text)


def _process_identity(pid: int) -> str | None:
    try:
        # Linux start-time prevents mistaking a reused PID for our old worker.
        stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return stat[19]
    except (OSError, IndexError):
        return None


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _prompt(request: dict) -> str:
    return (
        "GENIUS-5000 research execution. Scope: analyze only the supplied problem and inputs. "
        "Return a reviewable report with explicit hypotheses, sources actually consulted, "
        "artifacts/calculations actually performed, failures, uncertainty and next check. "
        "Do not invent credentials, references, execution results or claim the googly is solved. "
        "Apply Protocol A for physics and B for mathematics as supplied below. "
        "Use available skills; if ~/.claude/arranque-subagentes.md exists, apply it first. "
        "Do not read another provider's phase-one output. Do not modify external services "
        "or unrelated files. The prompt defines no permission to relax the environment sandbox.\n\n"
        + json.dumps(request, ensure_ascii=False, indent=2)
    )


async def _subprocess(args: list[str], *, cwd: Path, stdin: bytes, seconds: float,
                      max_bytes: int, env: dict, on_start=None) -> dict:
    """Drain both pipes; kill the entire process group on timeout/overflow/cancel."""
    started = time.monotonic()
    proc = await asyncio.create_subprocess_exec(*args, cwd=cwd, env=env,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, start_new_session=True)
    if on_start is not None:
        try:
            on_start(proc.pid)
        except BaseException:
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.wait()
            raise
    chunks: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
    captured = 0
    overflow = False

    def kill():
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    async def drain(stream, name):
        nonlocal captured, overflow
        while True:
            data = await stream.read(8192)
            if not data:
                break
            available = max(0, max_bytes - captured)
            chunks[name].append(data[:available])
            captured += min(available, len(data))
            if len(data) > available:
                overflow = True
                kill()

    async def send():
        try:
            proc.stdin.write(stdin)
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            proc.stdin.close()

    readers = [asyncio.create_task(drain(proc.stdout, "stdout")),
               asyncio.create_task(drain(proc.stderr, "stderr")), asyncio.create_task(send())]
    timed_out = False
    try:
        await asyncio.wait_for(asyncio.gather(proc.wait(), *readers), timeout=seconds)
    except asyncio.TimeoutError:
        timed_out = True
        kill()
        await proc.wait()
        await asyncio.gather(*readers, return_exceptions=True)
    except BaseException:
        kill()
        await proc.wait()
        await asyncio.gather(*readers, return_exceptions=True)
        raise
    return {"returncode": proc.returncode, "seconds": time.monotonic() - started,
            "stdout": _redact(b"".join(chunks["stdout"]).decode("utf-8", errors="replace")),
            "stderr": _redact(b"".join(chunks["stderr"]).decode("utf-8", errors="replace")),
            "output_bytes": captured, "timed_out": timed_out, "output_limit_exceeded": overflow}


class Orchestrator:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def run(self, plan: dict, output: str | Path, budget: Budget | None = None,
            *, resume: bool = False) -> dict:
        validate_plan(plan)
        budget = budget or Budget()
        budget.validate()
        if budget.max_usd is not None and plan["backend"] != "claude":
            raise ValueError("A hard USD budget is supported only by the verified Claude CLI flag")
        if plan["backend"] == "reference" and plan.get("reference_case") != "hodge-r4":
            raise ValueError("Select the explicit hodge-r4 reference case; arbitrary problems require a live backend")
        output = Path(output).resolve()
        output.mkdir(parents=True, exist_ok=True)
        with (output / ".lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("Another process is already running this checkpoint") from error
            return asyncio.run(self._run(plan, output, budget, resume))

    async def _run(self, plan: dict, output: Path, budget: Budget, resume: bool) -> dict:
        checkpoint = output / "checkpoint.json"
        fingerprint = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
        if checkpoint.exists():
            if not resume:
                raise ValueError("Run already exists; use --resume to avoid overwriting evidence")
            state = read_json(checkpoint)
            if state["plan_sha256"] != fingerprint or state["budget"] != asdict(budget):
                raise ValueError("Resume requires the identical plan and budget")
            interrupted_charge = 0.0
            for key, task in state["tasks"].items():
                if task["status"] == "running":
                    for attempt in task["attempts"]:
                        if attempt["status"] != "running":
                            continue
                        pid = attempt.get("pid")
                        if pid and _process_alive(pid):
                            identity = _process_identity(pid)
                            if not attempt.get("process_identity") or identity == attempt["process_identity"]:
                                raise ValueError("Prior worker is still alive; resume will not duplicate it. Inspect the recorded PID and wait/stop that execution first.")
                        if not pid:
                            raise ValueError("Interrupted launch has no confirmed PID; its outcome is indeterminate. Inspect and reconcile manually before retry.")
                        interrupted_charge = max(interrupted_charge, budget.task_seconds)
                    task["status"] = "failed"
                    task["error"] = "Interrupted execution; outcome indeterminate"
                    for attempt in task["attempts"]:
                        if attempt["status"] == "running":
                            attempt["status"] = "indeterminate"
                if task["status"] == "completed":
                    for file_key, hash_key in (("result_path", "result_sha256"), ("request_path", "request_sha256")):
                        file_path = output / task[file_key]
                        if not file_path.is_file() or digest(file_path) != task[hash_key]:
                            raise ValueError(f"Completed artifact changed: {key}; create a new run")
            state["seconds_consumed"] += interrupted_charge
        else:
            if resume:
                raise ValueError("No checkpoint exists to resume")
            write_json(output / "plan.json", plan)
            state = {"schema_version": "1.0", "created": now(), "plan_sha256": fingerprint,
                     "backend": plan["backend"], "budget": asdict(budget), "calls_started": 0,
                     "seconds_consumed": 0.0, "max_concurrency_observed": 0,
                     "tasks": {t["id"]: {"status": "pending", "attempts": []} for t in plan["tasks"]}}
        started = time.monotonic()
        previous_seconds = state["seconds_consumed"]
        running: dict[str, asyncio.Task] = {}
        protocol_path = self.root / "docs/scientific_protocol.md"
        protocol = protocol_path.read_text() if protocol_path.exists() else "Protocols A/B: premises, explicit argument, assumptions, dimensions, limits, audit."

        def save():
            state["seconds_consumed"] = previous_seconds + time.monotonic() - started
            write_json(checkpoint, state)

        async def execute(task: dict):
            record = state["tasks"][task["id"]]
            attempt_number = len(record["attempts"]) + 1
            workspace = output / "executions" / task["id"] / f"attempt-{attempt_number}"
            # Preserve any uncheckpointed orphan from an interrupted filesystem write.
            while workspace.exists():
                attempt_number += 1
                workspace = workspace.parent / f"attempt-{attempt_number}"
            record["status"] = "running"
            attempt = {"number": attempt_number, "execution_id": str(workspace.relative_to(output)),
                       "started": now(), "status": "running", "process_started": False}
            record["attempts"].append(attempt)
            save()
            try:
                workspace.mkdir(parents=True, exist_ok=False)
                dependencies = {key: read_json(output / state["tasks"][key]["result_path"]) for key in task["dependencies"]}
                registry = self.root / "institute/registry/profiles.jsonl"
                profile = None
                if registry.exists():
                    with registry.open() as stream:
                        for line in stream:
                            candidate = json.loads(line)
                            if candidate["id"] == task["profile_id"]:
                                profile = candidate
                                break
                if profile is None and plan["backend"] != "reference":
                    raise ValueError("Selected profile is absent from the actual registry")
                request = {**task, "problem": plan["problem"], "reference_case": plan.get("reference_case"),
                           "profile": profile, "inputs": dependencies, "workspace": str(workspace),
                           "protocol": protocol, "requested_model": plan.get("requested_model"),
                           "budget": {"seconds": budget.task_seconds, "max_output_bytes": budget.max_output_bytes}}
                from .skills import load_skill
                request["skills_supplied"] = {
                    name: load_skill(self.root, name) for name in ROLE_SKILLS[task["role"]]
                    if (self.root / ".agents/skills" / name / "SKILL.md").is_file()
                }
                request_path = workspace / "request.json"
                write_json(request_path, request)
                prompt = _prompt(request).encode()
                if len(prompt) > budget.max_input_bytes:
                    raise ValueError("Input byte budget exceeded before starting the process")
                args = adapters.command(plan["backend"], workspace, request_path,
                           plan.get("requested_model"), budget.max_usd / budget.max_calls if budget.max_usd else None)
                attempt["command"] = args
                attempt["process_started"] = False
                env = {**os.environ, "PYTHONPATH": str(self.root)}
                remaining = budget.max_seconds - previous_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    raise ValueError("Wall-time budget exhausted before launching")
                def record_start(pid):
                    attempt.update(process_started=True, pid=pid, process_identity=_process_identity(pid))
                    save()
                # A launch attempt can still fail at OS level; confirmed below by a return record.
                result = await _subprocess(args, cwd=workspace,
                            stdin=b"" if plan["backend"] == "reference" else prompt,
                            seconds=min(budget.task_seconds, remaining), max_bytes=budget.max_output_bytes,
                            env=env, on_start=record_start)
                attempt.update({k: v for k, v in result.items() if k not in {"stdout", "stderr"}})
                (workspace / "stdout.log").write_text(result["stdout"])
                (workspace / "stderr.log").write_text(result["stderr"])
                if result["timed_out"] or result["output_limit_exceeded"] or result["returncode"] != 0:
                    raise RuntimeError("timeout" if result["timed_out"] else
                        "output byte limit" if result["output_limit_exceeded"] else f"process exit {result['returncode']}")
                response = adapters.parse_response(plan["backend"], result["stdout"])
                response.update(execution_id=attempt["execution_id"], profile_id=task["profile_id"],
                                role=task["role"], execution_status="completed")
                result_path = workspace / "result.json"
                write_json(result_path, response)
                record.update(status="completed", result_path=str(result_path.relative_to(output)),
                              result_sha256=digest(result_path), request_path=str(request_path.relative_to(output)),
                              request_sha256=digest(request_path))
                record.pop("error", None)
                attempt["status"] = "completed"
            except asyncio.CancelledError:
                record.update(status="failed", error="Cancelled; inspect partial artifacts before retry")
                attempt["status"] = "indeterminate"
                raise
            except Exception as error:
                record.update(status="failed", error=f"{type(error).__name__}: {_redact(str(error))}")
                attempt.update(status="failed", error=record["error"])
            finally:
                attempt["finished"] = now()
                save()

        try:
            while True:
                elapsed = previous_seconds + time.monotonic() - started
                remaining_calls = budget.max_calls - state["calls_started"]
                if elapsed < budget.max_seconds and remaining_calls > 0:
                    for task in plan["tasks"]:
                        rec = state["tasks"][task["id"]]
                        if len(running) >= budget.concurrency or remaining_calls <= 0:
                            break
                        if task["id"] in running or rec["status"] == "completed" or len(rec["attempts"]) >= budget.retries + 1:
                            continue
                        if all(state["tasks"][d]["status"] == "completed" for d in task["dependencies"]):
                            state["calls_started"] += 1
                            running[task["id"]] = asyncio.create_task(execute(task))
                            remaining_calls -= 1
                state["max_concurrency_observed"] = max(state["max_concurrency_observed"], len(running))
                if not running:
                    break
                done, _ = await asyncio.wait(list(running.values()), return_when=asyncio.FIRST_COMPLETED)
                for key, future in list(running.items()):
                    if future in done:
                        await future
                        del running[key]
        finally:
            for future in running.values():
                future.cancel()
            if running:
                await asyncio.gather(*running.values(), return_exceptions=True)
            save()
        complete = [t for t in plan["tasks"] if state["tasks"][t["id"]]["status"] == "completed"]
        attempts = [a for r in state["tasks"].values() for a in r["attempts"]]
        actual_processes = sum(a.get("process_started", False) for a in attempts)
        audit_count = sum(t["role"] == "audit" for t in complete)
        reviewed = sum(t["role"] == "audit" and read_json(output / state["tasks"][t["id"]]["result_path"]).get("reviewed") is True for t in complete)
        summary = {"status": "completed" if len(complete) == len(plan["tasks"]) else "incomplete",
                   "backend": plan["backend"], "registered_profiles": plan["registered_profiles"],
                   "selected_profiles": len(plan["selected_profiles"]), "processes_executed": actual_processes,
                   "agents_executed": len(complete) if plan["backend"] != "reference" else 0,
                   "llm_executions_unconfirmed": actual_processes - len(complete) if plan["backend"] != "reference" else 0,
                   "completed_executions": len(complete), "review_executions_completed": audit_count,
                   "reviewed_results": reviewed,
                   "calls_started": state["calls_started"], "seconds_consumed": state["seconds_consumed"],
                   "max_concurrency_observed": state["max_concurrency_observed"], "budget": asdict(budget),
                   "failed_tasks": {k: r.get("error") for k, r in state["tasks"].items() if r["status"] == "failed"},
                   "blocked_tasks": [k for k, r in state["tasks"].items() if r["status"] == "pending"],
                   "token_accounting": "Provider-reported usage in result artifacts; no invented token or USD guarantee",
                   "scientific_capabilities_evaluated": 0,
                   "limitations": ["Reference workers are deterministic processes, not LLM researchers.",
                       "A completed review execution is not automatically a confirmed theorem.",
                       "Different executions may share the same algorithm/model and systematic errors."]}
        write_json(output / "summary.json", summary)
        return summary
