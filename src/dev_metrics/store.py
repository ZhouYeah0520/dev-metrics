from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    commit_sha TEXT NOT NULL,
    pipeline_id TEXT NOT NULL,
    branch TEXT NOT NULL,
    build_seconds REAL NOT NULL,
    test_seconds REAL NOT NULL,
    tests_passed INTEGER NOT NULL,
    tests_total INTEGER NOT NULL,
    environment_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (commit_sha, pipeline_id),
    CHECK (build_seconds >= 0),
    CHECK (test_seconds >= 0),
    CHECK (tests_passed >= 0 AND tests_total >= tests_passed)
)
"""


def connect(path: str | Path = "metrics.db") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(SCHEMA)
    return connection


def upsert_run(connection: sqlite3.Connection, run: dict) -> None:
    connection.execute(
        """INSERT INTO pipeline_runs (
             commit_sha, pipeline_id, branch, build_seconds, test_seconds,
             tests_passed, tests_total, environment_fingerprint
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(commit_sha, pipeline_id) DO UPDATE SET
             branch=excluded.branch, build_seconds=excluded.build_seconds,
             test_seconds=excluded.test_seconds, tests_passed=excluded.tests_passed,
             tests_total=excluded.tests_total,
             environment_fingerprint=excluded.environment_fingerprint,
             created_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now')""",
        (run["commit_sha"], run["pipeline_id"], run["branch"], run["build_seconds"],
         run["test_seconds"], run["tests_passed"], run["tests_total"],
         run["environment_fingerprint"]),
    )
    connection.commit()


def recent_runs(connection: sqlite3.Connection, limit: int = 100) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM pipeline_runs ORDER BY created_at DESC, commit_sha DESC LIMIT ?", (limit,)
    )
    return [dict(row) for row in rows]
