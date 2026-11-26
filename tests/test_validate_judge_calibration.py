import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_judge_calibration import validate_report


def base_report():
    return {
        "schema_version": "0.0.2",
        "report_id": "judge-calibration-smoke-001",
        "created_at": "2026-11-26T00:00:00Z",
        "calibration_kind": "synthetic_smoke",
        "status": "NOT_VALIDATED",
        "dataset": {
            "suite_id": "synthetic-suite",
            "suite_sha256": "a" * 64,
            "case_ids": ["JC01", "JC02", "JC03"],
            "label_source": "synthetic_fixture",
            "independent_gold": False,
            "split_id": None,
            "held_out": False
        },
        "judge": {
            "provider": "example",
            "endpoint_origin": "https://judge.example",
            "model_id": "judge-model",
            "model_revision": None,
            "prompt_sha256": "b" * 64,
            "implementation_sha256": "c" * 64,
            "separate_from_subject": True
        },
        "protocol": {
            "blinded": False,
            "independent_review": False,
            "repeats_per_case": 1,
            "abstention_policy": "Insufficient evidence => UNKNOWN",
            "run_id": None,
            "commit_sha": None
        },
        "results": [
            {"case_id":"JC01","gold_status":"PASS","judge_status":"PASS","evidence_validated":True,"output_sha256":"d"*64,"gold_evidence_ref":"fixture://JC01"},
            {"case_id":"JC02","gold_status":"FAIL","judge_status":"PASS","evidence_validated":False,"output_sha256":"e"*64,"gold_evidence_ref":"fixture://JC02"},
            {"case_id":"JC03","gold_status":"UNKNOWN","judge_status":"UNKNOWN","evidence_validated":False,"output_sha256":"f"*64,"gold_evidence_ref":None}
        ],
        "summary": {
            "case_count": 3,
            "adjudicable_count": 2,
            "exact_matches": 1,
            "false_passes": 1,
            "false_fails": 0,
            "abstentions": 1,
            "accuracy": 0.5
        },
        "limitations": ["Synthetic smoke fixtures do not establish real-world Judge validity."]
    }


class JudgeCalibrationContractTests(unittest.TestCase):
    def test_synthetic_smoke_contract_passes_but_remains_not_validated(self):
        self.assertEqual(validate_report(base_report()), [])

    def test_recomputed_summary_rejects_forged_counts(self):
        report = base_report()
        report["summary"]["false_passes"] = 0
        self.assertTrue(any("summary.false_passes" in e for e in validate_report(report)))

    def test_duplicate_or_missing_case_ids_fail(self):
        report = base_report()
        report["results"][2]["case_id"] = "JC02"
        errors = validate_report(report)
        self.assertTrue(any("duplicate case_id" in e for e in errors))
        self.assertTrue(any("exactly match" in e for e in errors))

    def test_synthetic_fixture_cannot_be_marked_validated(self):
        report = base_report()
        report["status"] = "VALIDATED_FOR_SCOPE"
        self.assertTrue(any("cannot validate Judge validity" in e for e in validate_report(report)))

    def test_judge_must_be_separate_from_subject(self):
        report = base_report()
        report["judge"]["separate_from_subject"] = False
        self.assertTrue(any("independent from the evaluated subject" in e for e in validate_report(report)))

    def test_empirical_validation_requires_independent_heldout_blind_evidence(self):
        report = base_report()
        report["calibration_kind"] = "independent_empirical"
        report["dataset"].update({
            "label_source":"adjudicated_oracle",
            "independent_gold":True,
            "split_id":"heldout-v1",
            "held_out":True
        })
        report["protocol"].update({"blinded":True,"independent_review":True})
        report["judge"]["judge_type"] = "llm"
        for item in report["results"]:
            item["evidence_validated"] = True
            item["gold_evidence_ref"] = "oracle://"+item["case_id"]
            item["judge_evidence_ref"] = "judge-run://"+item["case_id"]
            item["adjudicator_id"] = "arbiter-anon-01"
        report["status"] = "VALIDATED_FOR_SCOPE"
        self.assertEqual(validate_report(report), [])

    def test_empirical_claim_without_case_level_evidence_fails(self):
        report = base_report()
        report["calibration_kind"] = "independent_empirical"
        report["dataset"].update({
            "label_source":"adjudicated_oracle",
            "independent_gold":True,
            "split_id":"heldout-v1",
            "held_out":True
        })
        report["protocol"].update({"blinded":True,"independent_review":True})
        report["judge"]["judge_type"] = "human"
        errors = validate_report(report)
        self.assertTrue(any("lacks Gold evidence reference" in e for e in errors))
        self.assertTrue(any("lacks Judge evidence reference" in e for e in errors))
        self.assertTrue(any("lacks anonymous adjudicator_id" in e for e in errors))

    def test_empirical_claim_without_blinding_and_heldout_split_fails(self):
        report = base_report()
        report["calibration_kind"] = "independent_empirical"
        report["dataset"].update({"label_source":"adjudicated_oracle","independent_gold":True})
        self.assertTrue(any("held-out split" in e for e in validate_report(report)))
        self.assertTrue(any("blinded and independent" in e for e in validate_report(report)))

    def test_suite_hash_and_case_ids_are_verified_when_suite_is_supplied(self):
        report = base_report()
        suite = {"suite_id":"synthetic-suite","cases":[{"id":"JC01"},{"id":"JC02"},{"id":"JC03"}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.json"
            raw = json.dumps(suite, separators=(",", ":")).encode()
            path.write_bytes(raw)
            report["dataset"]["suite_sha256"] = hashlib.sha256(raw).hexdigest()
            self.assertEqual(validate_report(report, path), [])
            report["dataset"]["suite_sha256"] = "0" * 64
            self.assertTrue(any("does not match supplied suite bytes" in e for e in validate_report(report, path)))


if __name__ == "__main__":
    unittest.main()
