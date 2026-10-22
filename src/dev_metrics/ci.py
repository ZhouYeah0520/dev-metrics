from __future__ import annotations

import argparse
import sys
import time
import unittest

from .cli import main as metrics_main


class MetricsTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed += 1


def run_test_suite(suite: unittest.TestSuite, stream=None) -> tuple[float, MetricsTestResult]:
    runner = unittest.TextTestRunner(
        stream=stream or sys.stderr, verbosity=2, resultclass=MetricsTestResult,
    )
    started = time.perf_counter()
    result = runner.run(suite)
    return time.perf_counter() - started, result


def metrics_arguments(result: MetricsTestResult, elapsed: float, database: str = "metrics.db",
                      requirements: str = "requirements.txt", build_seconds: float = 0) -> list[str]:
    return [
        "collect", "--db", database,
        "--build-seconds", str(build_seconds),
        "--test-seconds", f"{elapsed:.6f}",
        "--tests-passed", str(result.passed),
        "--tests-total", str(result.testsRun),
        "--requirements", requirements,
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tests and record their CI metrics")
    parser.add_argument("--tests-dir", default="tests")
    parser.add_argument("--db", default="metrics.db")
    parser.add_argument("--requirements", default="requirements.txt")
    parser.add_argument("--build-seconds", type=float, default=0)
    args = parser.parse_args(argv)

    suite = unittest.defaultTestLoader.discover(args.tests_dir)
    elapsed, result = run_test_suite(suite)
    collect_status = metrics_main(metrics_arguments(
        result, elapsed, args.db, args.requirements, args.build_seconds,
    ))
    return collect_status or (0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    raise SystemExit(main())
