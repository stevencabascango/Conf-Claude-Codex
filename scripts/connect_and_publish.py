#!/usr/bin/env python3
"""One interactive, local workflow: verified portable gh, browser login, publish.

Run in the user's WSL/Linux terminal with Internet, outside a restricted executor.
No sudo, pasted tokens, or global git configuration changes are required.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


def download(url):
    if not url.startswith("https://"):
        raise RuntimeError("Only HTTPS release assets are accepted")
    request = Request(url, headers={"User-Agent": "GENIUS-5000-publication", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def install_gh():
    existing = shutil.which("gh")
    if existing:
        return Path(existing)
    if platform.system() != "Linux":
        raise RuntimeError("Run this command from your Ubuntu/WSL terminal")
    architectures = {"x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
    architecture = architectures.get(platform.machine())
    if not architecture:
        raise RuntimeError("Unsupported Linux architecture; install GitHub CLI using its official instructions")
    release = json.loads(download("https://api.github.com/repos/cli/cli/releases/latest"))
    version = release["tag_name"].removeprefix("v")
    filename = f"gh_{version}_linux_{architecture}.tar.gz"
    checksums = f"gh_{version}_checksums.txt"
    assets = {a["name"]: a["browser_download_url"] for a in release["assets"]}
    if filename not in assets or checksums not in assets:
        raise RuntimeError("Official portable release/checksum asset missing")
    for name in (filename, checksums):
        if not assets[name].startswith("https://github.com/cli/cli/releases/download/"):
            raise RuntimeError("Unexpected release asset source")
    print(f"Descargando GitHub CLI {version} del repositorio oficial...", flush=True)
    expected = next((line.split()[0] for line in download(assets[checksums]).decode().splitlines()
                     if len(line.split()) == 2 and line.split()[1].lstrip("*") == filename), None)
    archive = download(assets[filename])
    if not expected or hashlib.sha256(archive).hexdigest() != expected:
        raise RuntimeError("Portable release checksum did not match; nothing installed")
    member_name = filename.removesuffix(".tar.gz") + "/bin/gh"
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        member = tar.getmember(member_name)
        if not member.isfile():
            raise RuntimeError("Expected CLI executable is not a regular file")
        executable = tar.extractfile(member).read()
    target = Path.home() / ".local/bin/gh"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        raise RuntimeError("An existing ~/.local/bin/gh was preserved; inspect it before retrying")
    descriptor, temporary = tempfile.mkstemp(prefix=".gh-install-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(executable)
        os.chmod(temporary, 0o755)
        # Hard-link creation is atomic and refuses to overwrite a concurrent file.
        os.link(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def main():
    if not sys.stdin.isatty():
        raise RuntimeError("Run interactively in your own Ubuntu/WSL terminal to authorize the browser login")
    gh = install_gh()
    env = {**os.environ, "PATH": str(gh.parent) + os.pathsep + os.environ.get("PATH", "")}
    authenticated = subprocess.run([str(gh), "auth", "status", "--hostname", "github.com"], env=env)
    if authenticated.returncode:
        print("Autoriza tu cuenta en el navegador cuando GitHub lo solicite.", flush=True)
        subprocess.run([str(gh), "auth", "login", "--hostname", "github.com", "--git-protocol", "https",
                        "--web", "--scopes", "workflow"],
                       env=env, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/publish.py")], cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print(f"No publicado: {error}", file=sys.stderr)
        raise SystemExit(1)
