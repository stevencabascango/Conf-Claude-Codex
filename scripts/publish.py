#!/usr/bin/env python3
"""Publish only with verified access and compatible history; never force push."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "stevencabascango/Conf-Claude-Codex"
URL = f"https://github.com/{REPOSITORY}.git"
GIT_AUTH = ("-c", "credential.helper=", "-c", "credential.https://github.com.helper=!gh auth git-credential")


def run(*args, check=True):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=60)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {args[0]}")
    return result


def integrate_remote_readme(branch, identity):
    """Merge the inspected README-only remote in an isolated worktree.

    Arbitrary remote contents/conflicts require a separate review. Both local
    and remote histories remain parents of the merge, and the remote README is
    kept byte-for-byte as a document.
    """
    remote_ref = f"origin/{branch}"
    paths = run("git", "ls-tree", "-r", "--name-only", remote_ref).stdout.splitlines()
    remote_readme = subprocess.run(["git", "show", f"{remote_ref}:README.md"], cwd=ROOT,
                                  capture_output=True, timeout=60, check=True).stdout
    if paths != ["README.md"] or remote_readme.decode("utf-8").replace("\r\n", "\n").strip() != "# Conf-Claude-Codex\nRep para IAS":
        raise RuntimeError("Remote has additional or changed contents; a review is required before merging")
    if not identity.get("login") or not isinstance(identity.get("id"), int):
        raise RuntimeError("GitHub identity must be verified before creating a merge commit")
    with tempfile.TemporaryDirectory(prefix="genius5000-publish-") as temporary:
        worktree = Path(temporary) / "worktree"
        run("git", "worktree", "add", "--detach", str(worktree), "HEAD")
        def within(*args, check=True):
            result = subprocess.run(args, cwd=worktree, capture_output=True, text=True, timeout=60)
            if check and result.returncode:
                raise RuntimeError(result.stderr.strip() or "Integration command failed")
            return result
        try:
            local_readme = (worktree / "README.md").read_bytes()
            identity_args = ["-c", f"user.name={identity['login']}", "-c",
                             f"user.email={identity['id']}+{identity['login']}@users.noreply.github.com"]
            merge = within("git", *identity_args, "merge", "--no-commit", "--no-ff",
                           "--allow-unrelated-histories", remote_ref, check=False)
            conflicts = within("git", "diff", "--name-only", "--diff-filter=U").stdout.splitlines()
            if merge.returncode not in {0, 1} or any(p != "README.md" for p in conflicts):
                raise RuntimeError("Unexpected merge conflict; no remote changes made")
            (worktree / "README.md").write_bytes(local_readme)
            original = worktree / "docs/README.remote-original.md"
            original.parent.mkdir(parents=True, exist_ok=True)
            if original.exists() and original.read_bytes() != remote_readme:
                raise RuntimeError("Existing README archive differs; preserve it for review")
            original.write_bytes(remote_readme)
            within("git", "add", "README.md", "docs/README.remote-original.md")
            within("git", *identity_args, "commit", "-m",
                   "Integrate existing GitHub README and preserve both project histories")
            merged = within("git", "rev-parse", "HEAD").stdout.strip()
        finally:
            run("git", "worktree", "remove", "--force", str(worktree))
    return merged


def main():
    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI (gh) is unavailable; install/authenticate it when connectivity is available")
    run("gh", "auth", "status")
    identity = json.loads(run("gh", "api", "user").stdout)
    if identity.get("login", "").casefold() != REPOSITORY.split("/")[0].casefold():
        raise RuntimeError("Authorize the requested repository owner's account before publishing")
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
        if identity["login"].casefold() != REPOSITORY.split("/")[0].casefold():
            raise RuntimeError("Authenticated account does not own the requested repository")
        run("gh", "repo", "create", REPOSITORY, "--private", "--description", "GENIUS-5000 reproducible scientific research institute")
    refs = run("git", *GIT_AUTH, "ls-remote", "--heads", "origin").stdout.strip()
    publish_sha = run("git", "rev-parse", "HEAD").stdout.strip()
    if refs:
        run("git", *GIT_AUTH, "fetch", "origin")
        metadata = json.loads(run("gh", "repo", "view", REPOSITORY, "--json", "defaultBranchRef").stdout)
        branch = (metadata.get("defaultBranchRef") or {}).get("name")
        if not branch:
            raise RuntimeError("Cannot identify the remote default branch")
        if run("git", "merge-base", "--is-ancestor", f"origin/{branch}", "HEAD", check=False).returncode:
            publish_sha = integrate_remote_readme(branch, identity)
        destination = branch
    else:
        destination = "main"
    # Credential helper applies to this invocation only; preserve global git config.
    run("git", *GIT_AUTH, "push",
        "origin", f"{publish_sha}:refs/heads/{destination}")
    local = publish_sha
    remote = run("git", *GIT_AUTH, "ls-remote", "origin", f"refs/heads/{destination}").stdout.split()[0]
    if local != remote:
        raise RuntimeError("Remote SHA did not confirm the publication")
    run("git", "merge", "--ff-only", "--no-edit", publish_sha)
    print(json.dumps({"published": True, "repository": REPOSITORY, "branch": destination, "commit": local}))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
