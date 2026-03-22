#!/usr/bin/env python3
"""Fail when requirements.txt contains unpinned dependencies."""

from pathlib import Path
import sys

REQ = Path(__file__).resolve().parent.parent / "requirements.txt"

unpinned: list[str] = []
for raw in REQ.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith(("-r", "--")):
        unpinned.append(line)
        continue
    if "==" not in line:
        unpinned.append(line)

if unpinned:
    print("Unpinned dependencies detected in requirements.txt:", file=sys.stderr)
    for dep in unpinned:
        print(f" - {dep}", file=sys.stderr)
    sys.exit(1)

print("requirements.txt uses exact pins only")
