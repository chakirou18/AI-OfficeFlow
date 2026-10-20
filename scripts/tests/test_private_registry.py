import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import private_registry


class PrivateRegistry(unittest.TestCase):
    def metadata(self, command):
        return json.dumps({"name": command[-1].rsplit("/", 1)[1], "visibility": "private",
                           "repository": {"full_name": "chakirou18/AI-OfficeFlow"}}).encode()

    def test_private_packages_pass_and_public_wrong_owner_or_missing_fail_closed(self):
        with patch.object(private_registry, "output", side_effect=self.metadata) as fetch:
            private_registry.check_private_packages()
            self.assertEqual(fetch.call_count, 2)
        for metadata in ({"name": "ai-officeflow-private-api", "visibility": "public"},
                         {"name": "wrong-package", "visibility": "private"}, {},
                         {"name": "ai-officeflow-private-api", "visibility": "private",
                          "repository": {"full_name": "other/repository"}}):
            with self.subTest(metadata=metadata), patch.object(private_registry, "output", return_value=json.dumps(metadata)):
                with self.assertRaises(ValueError):
                    private_registry.check_private_packages()
        with patch.object(private_registry, "output", side_effect=RuntimeError("Unavailable")):
            with self.assertRaises(RuntimeError):
                private_registry.check_private_packages()

    def test_published_digest_is_selected_by_destination_not_list_order(self):
        expected = private_registry.IMAGE_REPOSITORIES["api"] + "@sha256:" + "b" * 64
        references = ["ghcr.io/chakirou18/ai-officeflow-api@sha256:" + "c" * 64, expected]
        with patch.object(private_registry, "output", return_value=json.dumps(references)):
            self.assertEqual(private_registry.published_reference("api", "a" * 40), expected)
        for references in ([], None, ["ghcr.io/other/api@sha256:" + "b" * 64], [expected, expected]):
            with self.subTest(references=references), patch.object(private_registry, "output", return_value=json.dumps(references)):
                with self.assertRaises(ValueError):
                    private_registry.published_reference("api", "a" * 40)


if __name__ == "__main__":
    unittest.main()
