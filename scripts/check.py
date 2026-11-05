#!/usr/bin/env python3
"""Run local validation and the real test suite; optionally persist JSON evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest


def run_checks(root: Path) -> dict:
    root = root.resolve()
    started = time.monotonic()
    validation_command = [sys.executable, "-m", "genius", "--root", str(root), "validate"]
    validation = subprocess.run(validation_command, cwd=root, text=True, capture_output=True, timeout=60)
    try:
        data = json.loads(validation.stdout)
    except ValueError:
        data = {"valid": False, "error": "Validation did not return JSON", "stdout": validation.stdout}
    sys.path.insert(0, str(root))
    transcript = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(suite)
    return {
        "schema_version": "1.0", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "root": str(root),
        "passed": validation.returncode == 0 and data.get("valid") is True and result.wasSuccessful(),
        "validation": {"command": validation_command, "returncode": validation.returncode,
                       "report": data, "stderr": validation.stderr},
        "tests": {"command_equivalent": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                  "run": result.testsRun, "failures": [{"test": str(t), "traceback": tb} for t, tb in result.failures],
                  "errors": [{"test": str(t), "traceback": tb} for t, tb in result.errors],
                  "skipped": [{"test": str(t), "reason": reason} for t, reason in result.skipped],
                  "passed": result.wasSuccessful(), "transcript": transcript.getvalue()},
        "elapsed_seconds": time.monotonic() - started,
        "limits": ["Local deterministic software checks; no model/API execution or external scientific review.",
                   "A successful registry check does not evaluate 5000 scientific capabilities."],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = run_checks(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "validation_passed": report["validation"]["report"].get("valid"),
                      "tests_run": report["tests"]["run"], "failures": len(report["tests"]["failures"]),
                      "errors": len(report["tests"]["errors"]), "skipped": len(report["tests"]["skipped"]),
                      "elapsed_seconds": report["elapsed_seconds"],
                      "evidence": str(args.output) if args.output else None}, ensure_ascii=False, indent=2))
    if not report["passed"]:
        print(report["tests"]["transcript"], file=sys.stderr)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
