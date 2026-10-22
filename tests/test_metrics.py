import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev_metrics.dashboard import render
from dev_metrics.fingerprint import environment_fingerprint
from dev_metrics.store import connect, recent_runs, upsert_run


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "metrics.sqlite"
        self.connection = connect(self.db)

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def run_record(self, **changes):
        record = {
            "commit_sha": "abc123", "pipeline_id": "42", "branch": "main",
            "build_seconds": 3.0, "test_seconds": 1.0, "tests_passed": 4,
            "tests_total": 5, "environment_fingerprint": "deadbeef",
        }
        record.update(changes)
        return record

    def test_upsert_is_idempotent_for_commit_and_pipeline(self):
        upsert_run(self.connection, self.run_record())
        upsert_run(self.connection, self.run_record(build_seconds=9.0))
        rows = recent_runs(self.connection)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["build_seconds"], 9.0)

    def test_dashboard_escapes_untrusted_fields_and_shows_pass_rate(self):
        upsert_run(self.connection, self.run_record(branch="<script>alert(1)</script>"))
        page = render(self.connection)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("80.0%", page)

    def test_fingerprint_is_a_short_hex_digest(self):
        result = environment_fingerprint(self.db.parent / "missing-requirements.txt")
        self.assertEqual(len(result), 16)
        self.assertTrue(all(char in "0123456789abcdef" for char in result))

    def test_fingerprint_survives_missing_git_executable(self):
        with patch("dev_metrics.fingerprint.subprocess.run", side_effect=FileNotFoundError):
            result = environment_fingerprint(self.db.parent / "missing-requirements.txt")
        self.assertEqual(len(result), 16)

    def test_collect_rejects_non_finite_durations(self):
        from dev_metrics.cli import main
        for option in ("--build-seconds", "--test-seconds"):
            with self.subTest(option=option), self.assertRaises(SystemExit):
                main(["collect", option, "inf"])

    def test_collect_rejects_negative_test_counts(self):
        from dev_metrics.cli import main
        with self.assertRaises(SystemExit):
            main(["collect", "--tests-passed", "-1", "--tests-total", "2"])


if __name__ == "__main__":
    unittest.main()
