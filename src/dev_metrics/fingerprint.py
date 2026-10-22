from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from pathlib import Path


def environment_fingerprint(requirements: str | Path = "requirements.txt") -> str:
    requirements_path = Path(requirements)
    dependency_text = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
    git_version = subprocess.run(
        ["git", "--version"], text=True, capture_output=True, check=False,
    ).stdout.strip()
    parts = [sys.version, platform.platform(), git_version, dependency_text]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]
