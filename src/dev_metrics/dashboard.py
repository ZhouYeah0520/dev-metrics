from __future__ import annotations

import html
import sqlite3
from pathlib import Path

from .store import recent_runs


def render(connection: sqlite3.Connection) -> str:
    rows = recent_runs(connection)
    body = []
    for run in rows:
        rate = (run["tests_passed"] / run["tests_total"] * 100) if run["tests_total"] else None
        rate_text = f"{rate:.1f}%" if rate is not None else "N/A"
        cells = [
            run["commit_sha"][:12], run["pipeline_id"], run["branch"],
            f"{run['build_seconds']:.2f}", f"{run['test_seconds']:.2f}", rate_text,
            run["environment_fingerprint"], run["created_at"],
        ]
        body.append("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in cells) + "</tr>")
    if not body:
        body.append('<tr><td colspan="8">No pipeline runs recorded</td></tr>')
    headers = ["Commit", "Pipeline", "Branch", "Build (s)", "Test (s)", "Pass rate", "Environment", "Recorded at"]
    return """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Development metrics</title>
<style>
body{font:14px system-ui,sans-serif;margin:32px;color:#20252b}h1{font-size:22px}
.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:900px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #d8dde2;white-space:nowrap}
th{background:#f2f5f7;font-weight:600}td:first-child{font-family:monospace}
</style><h1>Development metrics</h1><p>Recent pipeline runs</p><div class="table-wrap"><table>
<thead><tr>""" + "".join(f"<th>{html.escape(name)}</th>" for name in headers) + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div></html>"


def write_dashboard(connection: sqlite3.Connection, output: str | Path) -> Path:
    target = Path(output)
    target.write_text(render(connection), encoding="utf-8")
    return target
