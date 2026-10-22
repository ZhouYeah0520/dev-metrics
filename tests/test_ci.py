import io
import unittest

from dev_metrics.ci import MetricsTestResult, run_test_suite


class CiMetricsTests(unittest.TestCase):
    def test_runner_counts_passed_tests_and_reports_failures(self):
        class PassingTest(unittest.TestCase):
            def runTest(self):
                pass

        class FailingTest(unittest.TestCase):
            def runTest(self):
                self.fail("expected failure")

        suite = unittest.TestSuite([PassingTest(), FailingTest()])
        elapsed, result = run_test_suite(suite, stream=io.StringIO())

        self.assertIsInstance(result, MetricsTestResult)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(result.passed, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertGreaterEqual(elapsed, 0)

    def test_ci_metric_command_uses_actual_result_counts(self):
        from dev_metrics.ci import metrics_arguments
        result = MetricsTestResult(io.StringIO(), True, 0)
        result.testsRun = 5
        result.passed = 4
        args = metrics_arguments(result, 1.25, database="ci.sqlite")
        self.assertIn("--tests-passed", args)
        self.assertEqual(args[args.index("--tests-passed") + 1], "4")
        self.assertEqual(args[args.index("--tests-total") + 1], "5")
        self.assertEqual(args[args.index("--test-seconds") + 1], "1.250000")

    def test_ci_records_failed_run_and_preserves_failure_exit(self):
        from unittest.mock import patch
        from dev_metrics.ci import main

        result = MetricsTestResult(io.StringIO(), True, 0)
        result.testsRun = 1
        result.failures.append((object(), "expected failure"))
        with patch("dev_metrics.ci.run_test_suite", return_value=(0.25, result)), \
             patch("dev_metrics.ci.metrics_main", return_value=0) as collect:
            status = main(["--db", "ci.sqlite"])

        self.assertEqual(status, 1)
        args = collect.call_args.args[0]
        self.assertEqual(args[args.index("--tests-passed") + 1], "0")
        self.assertEqual(args[args.index("--tests-total") + 1], "1")


if __name__ == "__main__":
    unittest.main()
