"""Positive and negative provenance contracts; all records here are test fixtures."""
from pathlib import Path
import tempfile
import unittest

from genius.cross_review import prepare_cross_review, seal_report, seal_review, synthesize
from genius.install import install_project
from genius.io import read_json, write_json
from genius.memory import ScientificMemory
from genius.planning import prepare_comparison


class ProvenanceTests(unittest.TestCase):
    def test_promotion_requires_unchanged_real_completion_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            argument = root / "argument.txt"
            argument.write_text("Unit-test fixture only: 1=1.\n")
            with ScientificMemory(root / "memory.sqlite") as memory:
                memory.add({"id": "FIXTURE", "statement": "Unit-test fixture only",
                            "hypotheses": ["unit test"], "sources": [], "artifacts": [str(argument)],
                            "dependencies": [], "status": "pending_audit"})
                checks = {k: True for k in ("statement", "hypotheses", "logic", "dependencies", "conventions", "limits", "physical_scope", "tool_scope")}
                with self.assertRaises(ValueError):
                    memory.audit("FIXTURE", audit_id="missing", verdict="confirmed", producer_execution="p",
                                 reviewer_execution="r", checks=checks, artifacts=[str(argument)])
                for name, role in (("p", "mathematics"), ("r", "audit")):
                    path = root / f"{name}.json"
                    write_json(path, {"execution_id": name, "role": role, "backend": "unit-test-fixture",
                                      "execution_status": "completed"})
                    memory.register_execution(path)
                memory.audit("FIXTURE", audit_id="real-artifacts", verdict="confirmed", producer_execution="p",
                             reviewer_execution="r", checks=checks, artifacts=[str(argument)])
                self.assertEqual(memory.promote("FIXTURE", "proven", audit_id="real-artifacts")["status"], "proven")
                memory.revise("FIXTURE", reason="New argument revision requires a new audit")
                memory.resubmit("FIXTURE", reason="Submit corrected fixture")
                with self.assertRaises(ValueError):
                    memory.promote("FIXTURE", "proven", audit_id="real-artifacts")

    def test_two_sealed_cross_reviews_preserve_disagreement_without_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_comparison(root, "Unit-test fixture", {}, ["test only"], {"calls": 1})
            for provider in ("claude", "codex"):
                path = root / f"input-{provider}.json"
                write_json(path, {"status": "completed", "execution_id": f"test-{provider}",
                                  "model": None, "tools": ["unit-test-fixture"],
                                  "claims": [{"id": "FIXTURE", "statement": "fixture", "status": "proposal"}]})
                seal_report(root, provider, path)
            prepare_cross_review(root)
            for provider in ("claude", "codex"):
                path = root / f"review-{provider}.json"
                write_json(path, {"status": "completed", "execution_id": f"test-review-{provider}",
                                  "model": None, "tools": ["unit-test-fixture"],
                                  "reviewed_claims": [{"id": "FIXTURE", "verdict": "incomplete",
                                                       "reconstruction": "Unit-test fixture", "evidence": ["test-only"]}],
                                  "disagreements": ["Fixture assumption is open"], "next_checks": ["test only"]})
                seal_review(root, provider, path)
            result = synthesize(root)
            self.assertEqual(result["status"], "cross_reviewed_with_open_disagreements")
            self.assertEqual(result["scientific_promotion"], "none")
            self.assertTrue(result["disagreements"])
            self.assertEqual(read_json(root / "synthesis.json"), result)

    def test_install_does_not_follow_target_configuration_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target, outside = (root / p for p in ("source", "target", "outside"))
            (source / ".codex/agents").mkdir(parents=True)
            (source / ".codex/agents/genius.toml").write_text("fixture only")
            target.mkdir()
            outside.mkdir()
            (target / ".codex").symlink_to(outside, target_is_directory=True)
            result = install_project(source, target)
            self.assertFalse(result["complete"])
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
