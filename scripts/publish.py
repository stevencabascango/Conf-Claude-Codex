#!/usr/bin/env python3
"""Publish only with verified access and compatible history; never force push."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "stevencabascango/Conf-Claude-Codex"
URL = f"https://github.com/{REPOSITORY}.git"


def run(*args, check=True):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=60)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {args[0]}")
    return result


def main():
    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI (gh) is unavailable; install/authenticate it when connectivity is available")
    run("gh", "auth", "status")
    if run("git", "status", "--porcelain").stdout.strip():
        raise RuntimeError("Review and commit local changes before publishing")
    run("git", "rev-parse", "HEAD")
    if run("git", "remote", "get-url", "origin").stdout.strip() != URL:
        raise RuntimeError("Unexpected origin URL; inspect it before publishing")
    view = run("gh", "repo", "view", REPOSITORY, "--json", "nameWithOwner,defaultBranchRef", check=False)
    if view.returncode:
        probe = run("gh", "api", "--include", f"repos/{REPOSITORY}", check=False)
        if "HTTP 404" not in probe.stderr and "404 Not Found" not in probe.stdout:
            raise RuntimeError("Cannot verify whether the remote repository exists; no creation attempted")
        identity = run("gh", "api", "user", "--jq", ".login").stdout.strip()
        if identity.casefold() != REPOSITORY.split("/")[0].casefold():
            raise RuntimeError("Authenticated account does not own the requested repository")
        run("gh", "repo", "create", REPOSITORY, "--private", "--description", "GENIUS-5000 reproducible scientific research institute")
    refs = run("git", "ls-remote", "--heads", "origin").stdout.strip()
    if refs:
        run("git", "fetch", "origin")
        metadata = json.loads(run("gh", "repo", "view", REPOSITORY, "--json", "defaultBranchRef").stdout)
        branch = (metadata.get("defaultBranchRef") or {}).get("name")
        if not branch or run("git", "merge-base", "--is-ancestor", f"origin/{branch}", "HEAD", check=False).returncode:
            raise RuntimeError("Remote contains history not integrated locally. Review and integrate it before publishing; nothing was overwritten")
        destination = "genius5000/implementation"
    else:
        destination = "main"
    run("git", "push", "origin", f"HEAD:refs/heads/{destination}")
    local = run("git", "rev-parse", "HEAD").stdout.strip()
    remote = run("git", "ls-remote", "origin", f"refs/heads/{destination}").stdout.split()[0]
    if local != remote:
        raise RuntimeError("Remote SHA did not confirm the publication")
    print(json.dumps({"published": True, "repository": REPOSITORY, "branch": destination, "commit": local}))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
