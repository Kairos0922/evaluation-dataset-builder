import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_target_runtime_report import load_report, _non_finite_number_paths


class TargetRuntimeStrictJsonTests(unittest.TestCase):
    def test_rejects_non_standard_json_constants_in_report_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text('{"score":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "非标准 JSON 数值常量"):
                load_report(path)

    def test_detects_nested_non_finite_numeric_values(self):
        report = {"hosts": [{"metrics": {"score": float("inf")}}]}
        self.assertEqual(
            list(_non_finite_number_paths(report)),
            ["$.hosts[0].metrics.score"],
        )


if __name__ == "__main__":
    unittest.main()
