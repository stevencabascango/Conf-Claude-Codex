"""Acceptance checks across the actual catalogue, installer, CLI and workflow.

All executions here are local deterministic processes. No test calls Claude,
Codex, GitHub or a paid API, and no test modifies a user's configuration.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from genius.catalogue import load_profiles
from genius.demo import run_demo
from genius.install import install_project
from genius.io import read_json
from genius.orchestration import Budget, Orchestrator
from genius.planning import (
    ROLES, compare_reports, make_plan, prepare_comparison, select_team, validate_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class SelectionAndWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles(ROOT / "institute/registry/profiles.jsonl")

    def test_stage_a_selects_thirty_from_full_registry_without_execution(self):
        selected = select_team(self.profiles, "Googly: reconstruct two gravitational helicities from twistor data", 30)
        self.assertEqual(selected["registered_profiles"], 5000)
        self.assertEqual(len(selected["selected_profiles"]), 30)
        self.assertEqual(len(set(selected["selected_profiles"])), 30)
        self.assertEqual({a["role"] for a in selected["assignments"]}, set(ROLES))
        self.assertIn("googly", selected["programmes"])

    def test_small_and_transversal_teams_cover_all_roles(self):
        for size in (3, 21):
            with self.subTest(size=size):
                plan = make_plan(self.profiles, "Compare gravity and gauge structures", size=size)
                validate_plan(plan)
                self.assertEqual(len(plan["selected_profiles"]), size)
                self.assertEqual({t["role"] for t in plan["tasks"]}, set(ROLES))
                self.assertEqual(plan["counters"]["agents_executed"], 0)
                self.assertEqual(plan["counters"]["reviewed_results"], 0)
                for audit in (t for t in plan["tasks"] if t["role"] == "audit"):
                    producers = [t for t in plan["tasks"] if t["role"] == "mathematics" and t["id"] in audit["dependencies"]]
                    self.assertTrue(producers)
                    self.assertTrue(any(t["profile_id"] != audit["profile_id"] for t in producers))

    def test_known_problem_runs_separate_audit_classification_and_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = run_demo(ROOT, output, size=3)
            self.assertTrue(report["passed"], report)
            execution = report["execution"]
            self.assertEqual(execution["registered_profiles"], 5000)
            self.assertEqual(execution["selected_profiles"], 3)
            self.assertEqual(execution["processes_executed"], 7)
            self.assertEqual(execution["completed_executions"], 7)
            self.assertEqual(execution["agents_executed"], 0)
            self.assertEqual(execution["scientific_capabilities_evaluated"], 0)
            self.assertEqual(execution["reviewed_results"], 1)
            self.assertNotEqual(report["producer_execution"], report["reviewer_execution"])
            self.assertTrue((output / "run" / report["producer_execution"]).is_dir())
            self.assertTrue((output / "run" / report["reviewer_execution"]).is_dir())
            before = read_json(output / "memory-before-dependency-change.json")
            after = read_json(output / "memory-after-dependency-change.json")
            before_by_id = {claim["id"]: claim for claim in before["claims"]}
            after_by_id = {claim["id"]: claim for claim in after["claims"]}
            self.assertEqual(before_by_id["HODGE-E4-FALSE"]["status"], "refuted")
            self.assertEqual(after_by_id["HODGE-E4-FALSE"]["status"], "refuted")
            self.assertEqual(after_by_id["HODGE-DIMENSIONS"]["status"], "review")
            self.assertEqual(report["comparison"]["status"], "pending")
            checkpoint = read_json(output / "run/checkpoint.json")
            failed_audits = [t for t in checkpoint["tasks"].values() if t["status"] != "completed"]
            self.assertEqual(failed_audits, [])

    def test_real_failure_is_logged_and_bounded_retry_recovers(self):
        from genius import adapters
        original_command = adapters.command
        invocations = 0

        def fail_once(*args, **kwargs):
            nonlocal invocations
            invocations += 1
            if invocations == 1:
                return [sys.executable, "-c", "import sys; print('injected fixture failure',file=sys.stderr); sys.exit(9)"]
            return original_command(*args, **kwargs)

        plan = make_plan(self.profiles, "Hodge exact Euclidean two-form fixture", size=3)
        plan["reference_case"] = "hodge-r4"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch("genius.adapters.command", side_effect=fail_once):
                summary = Orchestrator(ROOT).run(plan, output,
                    Budget(concurrency=2, max_calls=8, max_seconds=30, task_seconds=5, retries=1))
            self.assertEqual(summary["status"], "completed", summary)
            self.assertEqual(summary["calls_started"], 8)
            self.assertLessEqual(summary["max_concurrency_observed"], 2)
            state = read_json(output / "checkpoint.json")
            first = state["tasks"][plan["tasks"][0]["id"]]
            self.assertEqual([a["status"] for a in first["attempts"]], ["failed", "completed"])
            self.assertEqual(first["attempts"][0]["returncode"], 9)
            failed_folder = output / first["attempts"][0]["execution_id"]
            self.assertIn("injected fixture failure", (failed_folder / "stderr.log").read_text())
            self.assertEqual(sum(len(t["attempts"]) for t in state["tasks"].values()), 8)

    def test_validate_cli_distinguishes_targets_from_execution_evidence(self):
        completed = subprocess.run([sys.executable, "-m", "genius", "--root", str(ROOT), "validate"],
                                   cwd=ROOT, text=True, capture_output=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["valid"])
        self.assertEqual(report["registry"]["profile_count"], 5000)
        self.assertEqual(report["registry"]["capability_status"]["scientific_evaluation"], "pending_individual_runs")
        self.assertEqual(report["stage_a"]["initial_selection"], 30)
        self.assertEqual(report["stage_a"]["executions"], 0)
        self.assertEqual(report["skills"]["count"], 22)

    def test_interrupted_run_resumes_without_repeating_completed_work(self):
        from genius import adapters
        original_command = adapters.command
        calls = 0

        def interrupt_second_launch(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise asyncio.CancelledError("fixture coordinator interruption before launch")
            return original_command(*args, **kwargs)

        plan = make_plan(self.profiles, "Hodge exact Euclidean fixture", size=3)
        plan["reference_case"] = "hodge-r4"
        budget = Budget(concurrency=1, max_calls=14, max_seconds=30, task_seconds=5, retries=1)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch("genius.adapters.command", side_effect=interrupt_second_launch):
                with self.assertRaises(asyncio.CancelledError):
                    Orchestrator(ROOT).run(plan, output, budget)
            interrupted = read_json(output / "checkpoint.json")
            first_id, second_id = [task["id"] for task in plan["tasks"][:2]]
            self.assertEqual(interrupted["tasks"][first_id]["status"], "completed")
            self.assertEqual(interrupted["tasks"][second_id]["status"], "failed")
            completed_hash = interrupted["tasks"][first_id]["result_sha256"]
            resumed = Orchestrator(ROOT).run(plan, output, budget, resume=True)
            self.assertEqual(resumed["status"], "completed", resumed)
            final = read_json(output / "checkpoint.json")
            self.assertEqual(len(final["tasks"][first_id]["attempts"]), 1)
            self.assertEqual(final["tasks"][first_id]["result_sha256"], completed_hash)
            self.assertEqual(len(final["tasks"][second_id]["attempts"]), 2)
            self.assertEqual(resumed["calls_started"], 8)


class InstallationAndComparisonTests(unittest.TestCase):
    def fixture(self, root):
        source, target = root / "source", root / "target"
        for folder in (source / ".codex", source / ".claude", source / ".agents/skills/fixture"):
            folder.mkdir(parents=True, exist_ok=True)
        (source / "AGENTS.md").write_text("new institute instructions\n")
        (source / ".codex/config.toml").write_text("[agents]\nenabled = true\n")
        (source / ".claude/settings.json").write_text('{"example": "source"}\n')
        (source / ".agents/skills/fixture/SKILL.md").write_text("---\nname: fixture\ndescription: fixture\n---\n")
        return source, target

    def test_installation_preserves_existing_configuration_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = self.fixture(Path(directory))
            (target / ".codex").mkdir(parents=True)
            (target / ".claude").mkdir(parents=True)
            existing = {
                "AGENTS.md": "custom user project rules\n",
                ".codex/config.toml": 'model = "user-choice"\n',
                ".claude/settings.json": '{"permissions": "existing"}\n',
            }
            for name, content in existing.items():
                (target / name).write_text(content)
            before = {name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in existing}
            first = install_project(source, target)
            self.assertEqual(set(first["conflicts_preserved"]), set(existing))
            self.assertFalse(first["global_configuration_modified"])
            self.assertFalse(first["complete"])
            self.assertTrue((target / ".agents/skills/fixture/SKILL.md").is_file())
            second = install_project(source, target)
            self.assertEqual(second["copied"], [])
            self.assertEqual(set(second["conflicts_preserved"]), set(existing))
            self.assertEqual({name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in existing}, before)

    def test_fresh_install_and_dry_run_do_not_touch_global_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = self.fixture(Path(directory))
            preview = install_project(source, target, dry_run=True)
            self.assertTrue(preview["copied"])
            self.assertFalse(target.exists())
            first = install_project(source, target)
            self.assertTrue(first["complete"])
            self.assertTrue(first["copied"])
            again = install_project(source, target)
            self.assertTrue(again["complete"])
            self.assertFalse(again["copied"])
            self.assertEqual(set(again["unchanged"]), set(first["copied"]))

    def test_shared_brief_is_identical_in_distinct_workspaces(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = prepare_comparison(root, "Fix the Euclidean Hodge sign", {"signature": "+,+,+,+"},
                                          ["exact arithmetic", "independent reconstruction"],
                                          {"max_calls": 4}, [{"id": "fixture", "status": "consulted"}])
            claude, codex = root / "claude/brief.json", root / "codex/brief.json"
            self.assertNotEqual(claude.parent.resolve(), codex.parent.resolve())
            self.assertEqual(claude.read_bytes(), codex.read_bytes())
            self.assertEqual(manifest["status"], "pending")
            self.assertEqual(manifest["reports"], {})

    def test_missing_comparison_and_disagreements_remain_visible(self):
        report = {"status": "completed", "claims": [{"id": "C1", "statement": "I", "status": "evidence"}]}
        pending = compare_reports(report, None)
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["missing_reports"], ["codex"])
        opposing = {"status": "completed", "claims": [{"id": "C1", "statement": "-I", "status": "proposal"}]}
        compared = compare_reports(report, opposing)
        self.assertEqual(len(compared["disagreements"]), 1)
        self.assertEqual(compared["agreements"], [])
        self.assertEqual(compared["cross_reviews"]["claude_reviews_codex"], "pending")
        self.assertEqual(compared["cross_reviews"]["codex_reviews_claude"], "pending")


if __name__ == "__main__":
    unittest.main()
