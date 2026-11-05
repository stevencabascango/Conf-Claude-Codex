import copy
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from genius.benchmark import BASIS, compute, execute, hodge_matrix, run_reference
from genius.skills import SKILL_NAMES, load_skill, validate_skills

ROOT = Path(__file__).resolve().parents[1]


class HodgeBenchmarkTests(unittest.TestCase):
    def test_known_star_images_and_square(self):
        matrix = hodge_matrix()
        self.assertEqual(BASIS, [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)])
        # *e12=e34, *e13=-e24, *e14=e23 independently fixed by wedge pairing.
        self.assertEqual([row[0] for row in matrix], [0, 0, 0, 0, 0, 1])
        self.assertEqual([row[1] for row in matrix], [0, 0, 0, 0, -1, 0])
        self.assertEqual([row[2] for row in matrix], [0, 0, 0, 1, 0, 0])
        result = compute()
        self.assertTrue(result["square_is_identity"])
        self.assertEqual((result["self_dual_dimension"], result["anti_self_dual_dimension"]), (3, 3))

    def test_auditor_reconstructs_producer(self):
        producer = execute({"role": "mathematics"})
        audited = execute({"role": "audit", "inputs": [producer]})
        self.assertTrue(audited["reviewed"])
        self.assertNotEqual(producer["execution_id"], audited["execution_id"])
        self.assertEqual(audited["evidence"]["producer_execution_ids"], [producer["execution_id"]])

    def test_auditor_rejects_forged_sign(self):
        producer = execute({"role": "mathematics"})
        producer["evidence"]["matrix"][5][0] = -1
        audited = execute({"role": "audit", "inputs": [producer]})
        self.assertFalse(audited["reviewed"])
        self.assertEqual(audited["evidence"]["verdict"], "REJECTED")

    def test_auditor_checks_every_producer_and_records_each_verdict(self):
        correct = execute({"role": "mathematics"})
        corrupt = execute({"role": "computation"})
        corrupt["evidence"]["matrix"][5][0] = -1
        audited = execute({"role": "audit", "inputs": [correct, corrupt]})
        self.assertFalse(audited["reviewed"])
        verdicts = {row["execution_id"]: row["verdict"] for row in audited["evidence"]["producer_verdicts"]}
        self.assertEqual(verdicts[correct["execution_id"]], "CONFIRMED_FINITE_FIXTURE")
        self.assertEqual(verdicts[corrupt["execution_id"]], "REJECTED")
        self.assertEqual(audited["evidence"]["reviewed_execution_ids"], [correct["execution_id"]])

    def test_auditor_rejects_conflicting_snapshots_of_same_execution(self):
        original = execute({"role": "mathematics"})
        corrupt = copy.deepcopy(original)
        corrupt["evidence"]["matrix"][5][0] = -1
        audited = execute({"role": "audit", "inputs": [original, corrupt]})
        self.assertFalse(audited["reviewed"])
        self.assertEqual(audited["evidence"]["reviewed_execution_ids"], [])

    def test_output_mutation_does_not_change_reference_conventions(self):
        producer = execute({"role": "mathematics"})
        producer["conventions"]["signature"] = "Lorentzian"
        audited = execute({"role": "audit", "inputs": producer})
        self.assertFalse(audited["reviewed"])
        self.assertEqual(execute({"role": "mathematics"})["conventions"]["signature"], "Euclidean")

    def test_auditor_checks_attached_claim_evidence(self):
        producer = execute({"role": "mathematics"})
        producer["claims"][0]["evidence"] = copy.deepcopy(producer["evidence"])
        producer["claims"][0]["evidence"]["matrix"][5][0] = -1
        self.assertFalse(execute({"role": "audit", "inputs": producer})["reviewed"])

    def test_auditor_rejects_forged_rank_or_square(self):
        producer = execute({"role": "mathematics"})
        for key, replacement in [("self_dual_dimension", 4), ("square", [[-1]])]:
            tampered = copy.deepcopy(producer)
            tampered["evidence"][key] = replacement
            self.assertFalse(execute({"role": "audit", "inputs": tampered})["reviewed"])

    def test_audit_requires_producer(self):
        with self.assertRaisesRegex(ValueError, "producer artifact"):
            execute({"role": "audit", "inputs": {}})

    def test_false_claim_refuted_and_never_demonstrated(self):
        result = execute({"role": "counterexample"})
        self.assertEqual(result["claims"][0]["status"], "REFUTADO")
        self.assertEqual(result["evidence"]["difference_coefficient"], 2)
        self.assertNotIn("DEMOSTRADO", result["claims"][0]["status"])

    def test_auditor_explicitly_refutes_deliberate_bad_proposal(self):
        producer = execute({"role": "mathematics"})
        false = execute({"role": "counterexample"})
        false["claims"][0]["status"] = "PROPUESTA"
        audited = execute({"role": "audit", "inputs": [producer, false]})
        evidence = audited["evidence"]["false_proposal_audit"]
        self.assertTrue(evidence["rejected"])
        self.assertEqual(evidence["difference"], [2, 0, 0, 0, 0, 0])
        self.assertEqual(audited["claims"][1]["status"], "REFUTADO")

    def test_corrected_statement_is_not_refuted_due_to_reused_identifier(self):
        producer = execute({"role": "mathematics"})
        corrected = execute({"role": "counterexample"})
        corrected["claims"][0]["statement"] = "*^2 = I on real Euclidean two-forms in dimension four"
        audited = execute({"role": "audit", "inputs": [producer, corrected]})
        self.assertFalse(audited["reviewed"])
        self.assertFalse(audited["evidence"]["false_proposal_audit"]["rejected"])
        self.assertEqual(audited["claims"][1]["status"], "EN REVISIÓN")
        self.assertEqual(audited["claims"][1]["statement"], corrected["claims"][0]["statement"])

    def test_reference_persists_real_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run_reference(temporary)
            self.assertTrue(report["passed"])
            saved = json.loads((Path(temporary) / "report.json").read_text())
            self.assertEqual(saved["benchmark"], "hodge-euclidean-4d")
            self.assertEqual(saved["cross_model_comparison"], "pending")
            for role in ("producer", "auditor", "counterexample"):
                self.assertTrue(list((Path(temporary) / role).glob("*.json")))

    def test_integration_does_not_invent_missing_audit(self):
        self.assertFalse(execute({"role": "integration", "inputs": []})["reviewed"])
        producer = execute({"role": "computation"})
        audit = execute({"role": "audit", "inputs": producer})
        self.assertTrue(execute({"role": "integration", "inputs": [producer, audit]})["reviewed"])

    def test_unknown_role_is_not_silently_run(self):
        with self.assertRaises(ValueError):
            execute({"role": "pretend-research"})


class SharedSkillTests(unittest.TestCase):
    def test_all_skills_discoverable_in_both_environments(self):
        report = validate_skills(ROOT)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["count"], 22)
        self.assertEqual(len(set(SKILL_NAMES)), 22)
        for name in SKILL_NAMES:
            self.assertIn(f"name: {name}", load_skill(ROOT, name))

    def test_skill_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            load_skill(ROOT, "../../etc/passwd")

    def test_native_codex_agents_parse_without_model_or_permission_override(self):
        adapters = list((ROOT / ".codex/agents").glob("*.toml"))
        self.assertEqual(len(adapters), 7)
        for adapter in adapters:
            parsed = tomllib.loads(adapter.read_text())
            self.assertTrue(parsed["name"].startswith("genius-"))
            self.assertTrue(parsed["description"])
            self.assertIn("docs/scientific_protocol.md", parsed["developer_instructions"])
            self.assertNotIn("model", parsed)
            self.assertNotIn("sandbox_mode", parsed)
            self.assertNotIn("approval_policy", parsed)


if __name__ == "__main__":
    unittest.main()
