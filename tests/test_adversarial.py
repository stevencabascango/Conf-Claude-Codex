"""Independent contract checks for research provenance and bounded execution.

Subprocess tests use tiny local fixtures, never an LLM or external service.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from genius.adapters import parse_response
from genius.io import read_json, write_json
from genius.memory import ScientificMemory
from genius.orchestration import Budget, Orchestrator, _process_identity, _subprocess
from genius.planning import ROLES, compare_reports, make_plan, prepare_comparison, validate_plan


def claim(identifier, status="proposal", dependencies=()):
    return {"id": identifier, "statement": "Finite fixture statement", "status": status,
            "hypotheses": ["fixture only"], "sources": ["identified fixture"],
            "artifacts": ["fixture.json"], "dependencies": list(dependencies)}


def plan():
    profiles = [{"id": f"P{i}", "division": "integration", "specialty": role,
                 "selection_tags": [role]} for i, role in enumerate(ROLES)]
    result = make_plan(profiles, "Hodge finite fixture", backend="reference")
    result["reference_case"] = "hodge-r4"
    return result


class ScientificMemoryAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.memory = ScientificMemory(Path(self.temporary.name) / "claims.db")

    def tearDown(self):
        self.memory.close()
        self.temporary.cleanup()

    def test_new_claim_cannot_start_as_theorem_or_formally_verified(self):
        for status in ("proven", "formal"):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.memory.add(claim(status, status))

    def test_refutation_cannot_be_promoted_even_with_audit_id(self):
        self.memory.add(claim("negative", "refuted"))
        with self.assertRaises(ValueError):
            self.memory.promote("negative", "proven", audit_id="invented")

    def test_revision_invalidates_all_descendants_and_retains_refutation(self):
        self.memory.add(claim("root", "established"))
        self.memory.add(claim("middle", "evidence", ["root"]))
        self.memory.add(claim("leaf", "evidence", ["middle"]))
        self.memory.add(claim("negative", "refuted", ["middle"]))
        affected = set(self.memory.revise("root", reason="Changed a convention"))
        self.assertEqual(affected, {"root", "middle", "leaf", "negative"})
        self.assertEqual(self.memory.get("leaf")["status"], "review")
        self.assertEqual(self.memory.get("negative")["status"], "refuted")
        self.assertEqual(self.memory.get("leaf")["revision"], 2)

    def test_confirmation_cannot_reuse_the_producer_execution(self):
        self.memory.add(claim("candidate", "pending_audit"))
        checks = {k: True for k in ("statement", "hypotheses", "logic", "dependencies",
                                    "conventions", "limits", "physical_scope", "tool_scope")}
        with self.assertRaises(ValueError):
            self.memory.audit("candidate", audit_id="audit", verdict="confirmed",
                              producer_execution="same", reviewer_execution="same",
                              checks=checks, artifacts=["fixture.json"])

    def test_rejected_dependency_cannot_support_positive_evidence(self):
        self.memory.add(claim("negative", "refuted"))
        with self.assertRaises(ValueError):
            self.memory.add(claim("dependent", "evidence", ["negative"]))

    def test_failed_atomic_insert_does_not_leave_claim_or_history(self):
        self.memory.add(claim("root", "established"))
        with self.assertRaises(Exception):
            self.memory.add(claim("bad", dependencies=["root", "root"]))
        with self.assertRaises(KeyError):
            self.memory.get("bad")
        exported = self.memory.export(Path(self.temporary.name) / "export.json")
        self.assertEqual([c["id"] for c in exported["claims"]], ["root"])
        self.assertTrue(all(h["claim_id"] != "bad" for h in exported["history"]))

    def test_conflicting_current_audit_prevents_promotion(self):
        root = Path(self.temporary.name)
        artifact = root / "argument.json"
        artifact.write_text('{"unit_test_fixture":true}\n')
        candidate = claim("candidate", "pending_audit")
        candidate["artifacts"] = [str(artifact)]
        self.memory.add(candidate)
        for identifier, role in (("producer", "mathematics"), ("reviewer1", "audit"), ("reviewer2", "audit")):
            path = root / f"{identifier}.json"
            write_json(path, {"execution_id": identifier, "role": role,
                             "backend": "unit-test-fixture", "execution_status": "completed"})
            self.memory.register_execution(path)
        checks = {k: True for k in ("statement", "hypotheses", "logic", "dependencies",
                                    "conventions", "limits", "physical_scope", "tool_scope")}
        self.memory.audit("candidate", audit_id="yes", verdict="confirmed",
                          producer_execution="producer", reviewer_execution="reviewer1",
                          checks=checks, artifacts=[str(artifact)])
        self.memory.audit("candidate", audit_id="no", verdict="rejected",
                          producer_execution="producer", reviewer_execution="reviewer2",
                          checks={**checks, "logic": False}, artifacts=[str(artifact)])
        with self.assertRaises(ValueError):
            self.memory.promote("candidate", "proven", audit_id="yes")


class ComparisonAdversarialTests(unittest.TestCase):
    def test_missing_or_failed_report_never_completes_comparison(self):
        for missing in (None, {}, {"status": "failed"}):
            with self.subTest(missing=missing):
                output = compare_reports({"status": "completed", "claims": []}, missing)
                self.assertEqual(output["status"], "pending")
                self.assertIn("codex", output["missing_reports"])

    def test_matching_reports_still_need_cross_review(self):
        report = {"status": "completed", "claims": [{"id": "C1", "statement": "fixture", "status": "proposal"}]}
        output = compare_reports(report, copy.deepcopy(report))
        self.assertEqual(output["status"], "ready_for_cross_review")
        self.assertEqual(output["cross_reviews"]["claude_reviews_codex"], "pending")

    def test_prepared_briefs_match_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_comparison(root, "fixture", {"signature": "Euclidean"}, ["exact arithmetic"], {"calls": 1})
            self.assertEqual((root / "claude/brief.json").read_bytes(),
                             (root / "codex/brief.json").read_bytes())

    def test_existing_comparison_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_comparison(root, "original", {}, [], {})
            before = (root / "comparison.json").read_bytes()
            with self.assertRaises(ValueError):
                prepare_comparison(root, "replacement", {}, [], {})
            self.assertEqual((root / "comparison.json").read_bytes(), before)

    def test_altered_initial_brief_cannot_be_used_to_seal_report(self):
        from genius.cross_review import seal_report
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_comparison(root, "original problem", {"signature": "Euclidean"}, [], {})
            brief = read_json(root / "claude/brief.json")
            brief["conventions"]["signature"] = "Lorentzian"
            write_json(root / "claude/brief.json", brief)
            report_path = root / "input.json"
            write_json(report_path, {"status": "completed", "claims": [], "execution_id": "fixture",
                                     "tools": ["unit-test-fixture"], "model": None})
            with self.assertRaises(ValueError):
                seal_report(root, "claude", report_path)

    def test_two_cross_reviews_cannot_share_execution_id(self):
        from genius.cross_review import prepare_cross_review, seal_report, seal_review
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_comparison(root, "fixture", {}, [], {})
            for provider in ("claude", "codex"):
                path = root / f"input-{provider}.json"
                write_json(path, {"status": "completed", "execution_id": f"development-{provider}",
                                  "tools": ["unit-test-fixture"], "model": None,
                                  "claims": [{"id": "C1", "statement": "fixture", "status": "proposal"}]})
                seal_report(root, provider, path)
            prepare_cross_review(root)
            review_path = root / "review-input.json"
            write_json(review_path, {"status": "completed", "execution_id": "same-review",
                "model": None, "tools": ["unit-test-fixture"], "disagreements": [], "next_checks": [],
                "reviewed_claims": [{"id": "C1", "verdict": "confirmed", "reconstruction": "fixture only",
                                     "evidence": ["unit-test-fixture"]}]})
            seal_review(root, "claude", review_path)
            with self.assertRaises(ValueError):
                seal_review(root, "codex", review_path)


class SubprocessAdversarialTests(unittest.TestCase):
    def test_captured_output_never_exceeds_byte_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            output = asyncio.run(_subprocess([sys.executable, "-c", "import os; os.write(1,b'x'*100000)"],
                cwd=Path(directory), stdin=b"", seconds=2, max_bytes=1000, env=os.environ.copy()))
            self.assertTrue(output["output_limit_exceeded"])
            self.assertEqual(output["output_bytes"], 1000)
            self.assertLessEqual(len(output["stdout"].encode()) + len(output["stderr"].encode()), 1000)

    def test_timeout_kills_a_real_local_process(self):
        with tempfile.TemporaryDirectory() as directory:
            output = asyncio.run(_subprocess([sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=Path(directory), stdin=b"", seconds=0.15, max_bytes=1000, env=os.environ.copy()))
            self.assertTrue(output["timed_out"])
            self.assertNotEqual(output["returncode"], 0)
            self.assertLess(output["seconds"], 2)

    def test_call_budget_blocks_downstream_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            command = [sys.executable, "-c", "print('{\"reviewed\":true,\"fixture\":true}')"]
            with patch("genius.adapters.command", return_value=command):
                summary = Orchestrator(root).run(plan(), run,
                    Budget(concurrency=2, max_calls=3, max_seconds=10, task_seconds=2, retries=0))
            self.assertLessEqual(summary["calls_started"], 3)
            self.assertLessEqual(summary["processes_executed"], 3)
            self.assertLessEqual(summary["max_concurrency_observed"], 2)
            self.assertEqual(summary["status"], "incomplete")
            self.assertEqual(summary["agents_executed"], 0)
            self.assertTrue(summary["blocked_tasks"])

    def test_resume_rejects_changed_completed_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            specimen = plan()
            budget = Budget(max_calls=1, retries=0, max_seconds=10, task_seconds=2)
            command = [sys.executable, "-c", "print('{\"fixture\":true}')"]
            with patch("genius.adapters.command", return_value=command):
                Orchestrator(root).run(specimen, run, budget)
            state = read_json(run / "checkpoint.json")
            complete = next(t for t in state["tasks"].values() if t["status"] == "completed")
            (run / complete["result_path"]).write_text("{}\n")
            with self.assertRaises(ValueError):
                Orchestrator(root).run(specimen, run, budget, resume=True)

    def test_budget_rejects_nonfinite_time_and_negative_retry(self):
        for budget in (Budget(max_seconds=float("nan")), Budget(task_seconds=float("inf")), Budget(retries=-1)):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                budget.validate()

    def test_uncheckpointed_orphan_is_preserved_and_a_new_attempt_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            orphan = run / "executions/task-001/attempt-1"
            orphan.mkdir(parents=True)
            evidence = orphan / "partial-evidence.txt"
            evidence.write_text("Keep this interrupted artifact")
            command = [sys.executable, "-c", "print('{\"fixture\":true}')"]
            with patch("genius.adapters.command", return_value=command):
                summary = Orchestrator(root).run(plan(), run,
                    Budget(max_calls=1, max_seconds=10, task_seconds=2, retries=0))
            self.assertEqual(summary["completed_executions"], 1)
            self.assertEqual(evidence.read_text(), "Keep this interrupted artifact")
            checkpoint = read_json(run / "checkpoint.json")
            self.assertEqual(checkpoint["tasks"]["task-001"]["attempts"][0]["number"], 2)

    def test_resume_does_not_duplicate_a_prior_worker_still_alive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            specimen = plan()
            budget = Budget(max_calls=1, retries=1, max_seconds=10, task_seconds=2)
            command = [sys.executable, "-c", "print('{\"fixture\":true}')"]
            with patch("genius.adapters.command", return_value=command):
                Orchestrator(root).run(specimen, run, budget)
            prior = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"], start_new_session=True)
            try:
                state = read_json(run / "checkpoint.json")
                task = state["tasks"]["task-001"]
                task["status"] = "running"
                task["attempts"][-1].update(status="running", pid=prior.pid,
                    process_identity=_process_identity(prior.pid), process_started=True)
                write_json(run / "checkpoint.json", state)
                with patch("genius.adapters.command", return_value=command) as launch:
                    with self.assertRaisesRegex(ValueError, "still alive"):
                        Orchestrator(root).run(specimen, run, budget, resume=True)
                    launch.assert_not_called()
            finally:
                prior.terminate()
                prior.wait(timeout=3)


class PlanAndAdapterAdversarialTests(unittest.TestCase):
    def test_plan_rejects_path_escape_and_future_dependency(self):
        specimen = plan()
        specimen["tasks"][0]["id"] = "../outside"
        with self.assertRaises(ValueError):
            validate_plan(specimen)
        specimen = plan()
        specimen["tasks"][0]["dependencies"] = [specimen["tasks"][-1]["id"]]
        with self.assertRaises(ValueError):
            validate_plan(specimen)

    def test_plan_rejects_duplicate_selected_ids(self):
        specimen = plan()
        specimen["selected_profiles"].append(specimen["selected_profiles"][0])
        with self.assertRaises(ValueError):
            validate_plan(specimen)

    def test_empty_claude_json_is_not_a_successful_research_report(self):
        with self.assertRaises(ValueError):
            parse_response("claude", "{}")


class ScientificBenchmarkAdversarialTests(unittest.TestCase):
    def test_all_six_basis_images_match_exterior_pairing(self):
        from genius.benchmark import hodge_matrix
        # Fixed independently from e12∧e34=+vol, e13∧e24=-vol,
        # e14∧e23=+vol and commutativity of the two degree-two factors.
        expected = [
            [0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, -1, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0, 0],
            [0, -1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0],
        ]
        self.assertEqual(hodge_matrix(), expected)

    def test_later_corrupt_producer_is_not_hidden_by_first_good_producer(self):
        from genius.benchmark import execute
        first = execute({"role": "mathematics"})
        later = execute({"role": "computation"})
        later["evidence"]["matrix"][5][0] = -1
        audit = execute({"role": "audit", "inputs": [first, later]})
        self.assertFalse(audit["reviewed"])

    def test_incompatible_signature_cannot_receive_euclidean_confirmation(self):
        from genius.benchmark import execute
        producer = copy.deepcopy(execute({"role": "mathematics"}))
        producer["conventions"]["signature"] = "Lorentzian"
        audit = execute({"role": "audit", "inputs": [producer]})
        self.assertFalse(audit["reviewed"])


if __name__ == "__main__":
    unittest.main()
