import copy
import unittest

from scripts.validate_skill import runtime_schema_boundary_errors


class RuntimeSchemaBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.package = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "package-schema",
            "type": "object",
            "required": ["record_version"],
            "properties": {"record_version": {"const": "0.0.2"}},
            "additionalProperties": False,
        }
        self.research = copy.deepcopy(self.package)
        self.research["$id"] = "research-schema"
        self.research["properties"]["trace_sha256"] = {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{64}$",
        }

    def test_allows_only_optional_trace_hash_extension(self):
        self.assertEqual(runtime_schema_boundary_errors(self.package, self.research), [])

    def test_rejects_unrelated_schema_drift(self):
        changed = copy.deepcopy(self.research)
        changed["properties"]["run_id"] = {"type": "string"}
        self.assertTrue(runtime_schema_boundary_errors(self.package, changed))

    def test_rejects_invalid_trace_hash_pattern(self):
        changed = copy.deepcopy(self.research)
        changed["properties"]["trace_sha256"]["pattern"] = "^[a-f0-9]{32}$"
        self.assertTrue(runtime_schema_boundary_errors(self.package, changed))

    def test_rejects_required_trace_hash(self):
        changed = copy.deepcopy(self.research)
        changed["required"].append("trace_sha256")
        self.assertTrue(runtime_schema_boundary_errors(self.package, changed))

    def test_rejects_trace_hash_in_released_contract(self):
        changed_package = copy.deepcopy(self.package)
        changed_package["properties"]["trace_sha256"] = self.research["properties"]["trace_sha256"]
        self.assertTrue(runtime_schema_boundary_errors(changed_package, self.research))


if __name__ == "__main__":
    unittest.main()
