"""Integrity tests intentionally do not certify scientific competence."""
import copy
import hashlib
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from genius.catalogue import (
    ARCHETYPES, COMMON_CORE, DIVISION_COUNTS, generate_profiles, load_profiles,
    semantic_fingerprint, validate_profiles, write_catalogue,
)


class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = generate_profiles()

    def test_exact_count_and_distribution(self):
        self.assertEqual(len(self.profiles), 5000)
        self.assertEqual(Counter(p["division"] for p in self.profiles), Counter(DIVISION_COUNTS))
        self.assertEqual(len({p["id"] for p in self.profiles}), 5000)
        self.assertTrue(validate_profiles(self.profiles)["valid"])

    def test_obvious_semantic_clone_ignores_new_name(self):
        clone = copy.deepcopy(self.profiles[0])
        clone["id"] = "different-id"
        clone["version"] = "999.0"
        self.assertEqual(semantic_fingerprint(clone), semantic_fingerprint(self.profiles[0]))
        report = validate_profiles([self.profiles[0], clone], {"rg": 2})
        self.assertFalse(report["valid"])
        self.assertEqual(len(report["uniqueness"]["exact_semantic_duplicate_pairs"]), 1)

    def test_missing_field_and_fake_evaluation_are_rejected(self):
        profile = copy.deepcopy(self.profiles[0])
        del profile["competence_limits"]
        profile["evaluated_capabilities"] = [{"capability": "all", "status": "excellent"}]
        report = validate_profiles([profile], {"rg": 1})
        self.assertFalse(report["valid"])
        self.assertTrue(any("missing" in e for e in report["errors"]))
        self.assertTrue(any("lacks evidence" in e for e in report["errors"]))

    def test_design_status_and_common_training_are_honest(self):
        for profile in self.profiles:
            self.assertEqual(profile["evaluated_capabilities"], [])
            self.assertEqual(profile["evaluation_results"], [])
            self.assertTrue(profile["pending_capabilities"])
            self.assertEqual(set(profile["knowledge"]["common_core_target"]), set(COMMON_CORE))
            self.assertIn(profile["archetypes"]["primary"], ARCHETYPES)
            self.assertTrue(all(t["availability"] == "probe_at_runtime" for t in profile["tools"]))

    def test_nested_malformed_values_fail_without_certifying(self):
        profile = copy.deepcopy(self.profiles[0])
        profile["knowledge"]["common_core_target"] = None
        profile["archetypes"]["complementary"] = None
        self.assertFalse(validate_profiles([profile], {"rg": 1})["valid"])

    def test_diversity_is_explicit_and_shared_context_reported(self):
        report = validate_profiles(self.profiles)
        self.assertEqual(report["coverage"]["scientific_lines"], 100)
        self.assertEqual(report["uniqueness"]["semantic_fingerprints"], 5000)
        self.assertEqual(report["proximity"]["shared_context_groups"], 500)
        self.assertEqual(set(report["coverage"]["roles"]), {"conceptual", "mathematics", "physics", "computation", "counterexample", "audit", "integration"})
        for line in report["coverage"]["lines"].values():
            self.assertEqual(line["profiles"], 50)
            self.assertEqual(len(line["modes"]), 5)
            self.assertEqual(len(line["tasks"]), 10)

    def test_roundtrip_and_deterministic_regeneration(self):
        with tempfile.TemporaryDirectory() as location:
            root = Path(location)
            report = write_catalogue(root)
            self.assertEqual(load_profiles(root), self.profiles)
            first_hash = report["artifact"]["sha256"]
            second = write_catalogue(root)
            self.assertEqual(first_hash, second["artifact"]["sha256"])
            content = (root / "institute/registry/profiles.jsonl").read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), first_hash)


if __name__ == "__main__":
    unittest.main()
