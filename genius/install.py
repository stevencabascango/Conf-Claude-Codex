"""Conservative project installation: never replace an existing file or setting."""
from __future__ import annotations

import os
from pathlib import Path
import shutil

COMPONENTS = ("genius", "institute", ".agents", ".claude", ".codex", "docs", "scripts",
              "research", "verification", "collaboration", "memory", "references",
              "AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md", "pyproject.toml")


def install_project(source: str | Path, destination: str | Path, *, dry_run: bool = False) -> dict:
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Use a separate target project, outside the source tree and its parents")
    result = {"copied": [], "unchanged": [], "conflicts_preserved": [], "dry_run": dry_run,
              "global_configuration_modified": False}
    for component in COMPONENTS:
        start = source / component
        if not start.exists():
            continue
        paths = [start] if start.is_file() else sorted(start.rglob("*"))
        for path in paths:
            relative = path.relative_to(source)
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".sqlite", ".db"}:
                continue
            if path.is_dir() and not path.is_symlink():
                continue
            target = destination / relative
            parent = target.parent
            blocked_parent = False
            while parent != destination:
                if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                    blocked_parent = True
                    break
                parent = parent.parent
            if blocked_parent:
                result["conflicts_preserved"].append(str(relative))
                continue
            if target.exists() or target.is_symlink():
                same = path.is_symlink() and target.is_symlink() and os.readlink(path) == os.readlink(target)
                if not path.is_symlink() and target.is_file() and not target.is_symlink():
                    same = path.read_bytes() == target.read_bytes()
                result["unchanged" if same else "conflicts_preserved"].append(str(relative))
                continue
            result["copied"].append(str(relative))
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink():
                    target.symlink_to(os.readlink(path))
                else:
                    shutil.copy2(path, target)
    result["complete"] = not result["conflicts_preserved"]
    return result
