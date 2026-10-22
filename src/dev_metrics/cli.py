from __future__ import annotations

import argparse
from contextlib import closing
import json
import math
import os
import subprocess
import time
from pathlib import Path

from .dashboard import write_dashboard
from .fingerprint import environment_fingerprint
from .store import connect, upsert_run


def git_value(*args: str, default: str = "unknown") -> str:
    result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dev-metrics")
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect", help="Record one pipeline run")
    collect.add_argument("--db", default="metrics.db")
    collect.add_argument("--commit", default=os.getenv("GITHUB_SHA") or os.getenv("CI_COMMIT_SHA") or "")
    collect.add_argument("--pipeline-id", default=os.getenv("GITHUB_RUN_ID") or os.getenv("CI_PIPELINE_ID") or "")
    collect.add_argument("--branch", default=os.getenv("GITHUB_REF_NAME") or os.getenv("CI_COMMIT_REF_NAME") or "local")
    collect.add_argument("--build-seconds", type=float, default=0)
    collect.add_argument("--test-seconds", type=float, default=0)
    collect.add_argument("--tests-passed", type=int, default=0)
    collect.add_argument("--tests-total", type=int, default=0)
    collect.add_argument("--requirements", default="requirements.txt")
    dashboard = sub.add_parser("dashboard", help="Render the static HTML dashboard")
    dashboard.add_argument("--db", default="metrics.db")
    dashboard.add_argument("--output", default="dashboard.html")
    args = parser.parse_args(argv)

    if args.command == "collect":
        commit = args.commit or git_value("rev-parse", "HEAD")
        pipeline_id = args.pipeline_id or f"local-{int(time.time())}"
        if not math.isfinite(args.build_seconds) or args.build_seconds < 0:
            parser.error("--build-seconds must be a finite non-negative number")
        if not math.isfinite(args.test_seconds) or args.test_seconds < 0:
            parser.error("--test-seconds must be a finite non-negative number")
        if args.tests_passed < 0 or args.tests_total < 0:
            parser.error("test counts must be non-negative")
        if args.tests_total < args.tests_passed:
            parser.error("--tests-total must be greater than or equal to --tests-passed")
        run = {
            "commit_sha": commit, "pipeline_id": pipeline_id, "branch": args.branch,
            "build_seconds": args.build_seconds, "test_seconds": args.test_seconds,
            "tests_passed": args.tests_passed, "tests_total": args.tests_total,
            "environment_fingerprint": environment_fingerprint(args.requirements),
        }
        with closing(connect(args.db)) as connection:
            with connection:
                upsert_run(connection, run)
        print(json.dumps(run, ensure_ascii=False, indent=2))
    elif args.command == "dashboard":
        with closing(connect(args.db)) as connection:
            with connection:
                target = write_dashboard(connection, args.output)
        print(target.resolve())
    return 0
