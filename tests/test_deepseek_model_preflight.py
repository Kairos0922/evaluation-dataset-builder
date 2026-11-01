import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deepseek_model_preflight import (  # noqa: E402
    calculate_budget,
    fetch_model_metadata,
    parse_model_metadata,
)


MODEL = {
    "id": "deepseek-flash",
    "name": "DeepSeek-V4.1-Flash-1017",
    "context_window": 1_048_576,
    "max_output_tokens": 393_216,
    "input_modalities": ["text", "image"],
    "output_modalities": ["text"],
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class ModelMetadataTests(unittest.TestCase):
    def test_parse_live_model_metadata(self):
        result = parse_model_metadata({"data": [MODEL]})
        self.assertEqual(result["id"], "deepseek-flash")
        self.assertEqual(result["context_window"], 1_048_576)
        self.assertEqual(result["max_output_tokens"], 393_216)

    def test_unknown_model_fails_before_generation(self):
        with self.assertRaisesRegex(ValueError, "not listed"):
            parse_model_metadata({"data": [MODEL]}, model_id="deepseek-v4.1-flash")

    def test_missing_limits_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "context_window"):
            parse_model_metadata({"data": [{"id": "deepseek-flash"}]})

    def test_fetch_uses_metadata_get_endpoint(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResponse({"data": [MODEL]})) as mocked:
            result = fetch_model_metadata("not-a-real-secret", timeout=2)
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.deepseek.com/models")
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.get_header("Authorization"), "Bearer not-a-real-secret")
        self.assertEqual(result["id"], "deepseek-flash")


class BudgetTests(unittest.TestCase):
    def test_large_task_fits_without_small_fixed_input_cap(self):
        result = calculate_budget(
            MODEL,
            estimated_input_tokens=700_000,
            estimated_output_tokens=100_000,
        )
        self.assertEqual(result["suggested_max_output_tokens"], 115_000)
        self.assertGreater(result["available_output_tokens"], 100_000)
        self.assertFalse(result["generation_call_made"])

    def test_output_budget_uses_live_hard_limits(self):
        result = calculate_budget(
            MODEL,
            estimated_input_tokens=20_000,
            estimated_output_tokens=300_000,
        )
        self.assertEqual(result["suggested_max_output_tokens"], 345_000)

    def test_does_not_silently_shrink_an_over_budget_request(self):
        with self.assertRaisesRegex(ValueError, "Do not silently truncate"):
            calculate_budget(
                MODEL,
                estimated_input_tokens=930_000,
                estimated_output_tokens=100_000,
            )

    def test_max_output_is_not_added_to_context_window(self):
        with self.assertRaisesRegex(ValueError, "Do not silently truncate"):
            calculate_budget(
                MODEL,
                estimated_input_tokens=900_000,
                estimated_output_tokens=130_000,
            )

    def test_operator_can_use_empirically_accurate_no_headroom_estimate(self):
        result = calculate_budget(
            MODEL,
            estimated_input_tokens=20_000,
            estimated_output_tokens=350_000,
            headroom=1.0,
        )
        self.assertEqual(result["suggested_max_output_tokens"], 350_000)

    def test_invalid_budget_parameters_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "headroom"):
            calculate_budget(MODEL, 10_000, 10_000, headroom=0.9)


if __name__ == "__main__":
    unittest.main()
