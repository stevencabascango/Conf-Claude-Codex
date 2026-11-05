"""Offline publication checks: local Git fixtures and mocked release downloads."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path(tempfile.gettempdir()) / "genius5000-publication-tests"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


def load_script(name):
    spec = importlib.util.spec_from_file_location("genius_publication_test_" + name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONNECT = load_script("connect_and_publish")
PUBLISH = load_script("publish")


class PortableCliTests(unittest.TestCase):
    version = "9.8.7"
    filename = "gh_9.8.7_linux_amd64.tar.gz"
    executable = b"#!/bin/sh\n# Offline fixture only; never executed.\nexit 0\n"

    def release(self, *, checksum_valid=True, symlink=False):
        archive_stream = io.BytesIO()
        member = tarfile.TarInfo("gh_9.8.7_linux_amd64/bin/gh")
        with tarfile.open(fileobj=archive_stream, mode="w:gz") as archive:
            if symlink:
                member.type = tarfile.SYMTYPE
                member.linkname = "../../outside"
                archive.addfile(member)
            else:
                member.size = len(self.executable)
                member.mode = 0o755
                archive.addfile(member, io.BytesIO(self.executable))
        data = archive_stream.getvalue()
        base = "https://github.com/cli/cli/releases/download/v9.8.7/"
        checksum_name = "gh_9.8.7_checksums.txt"
        release = {"tag_name": "v9.8.7", "assets": [
            {"name": self.filename, "browser_download_url": base + self.filename},
            {"name": checksum_name, "browser_download_url": base + checksum_name},
        ]}
        expected = hashlib.sha256(data).hexdigest() if checksum_valid else "0" * 64
        contents = {
            "https://api.github.com/repos/cli/cli/releases/latest": json.dumps(release).encode(),
            base + checksum_name: (expected + "  " + self.filename + "\n").encode(),
            base + self.filename: data,
        }
        return contents

    @contextmanager
    def installer(self, contents, *, existing=None):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            home = Path(temporary)
            with patch.object(CONNECT.shutil, "which", return_value=existing), \
                 patch.object(CONNECT.platform, "system", return_value="Linux"), \
                 patch.object(CONNECT.platform, "machine", return_value="x86_64"), \
                 patch.object(CONNECT.Path, "home", return_value=home), \
                 patch.object(CONNECT, "download", side_effect=contents.__getitem__) as download, \
                 redirect_stdout(io.StringIO()):
                yield home, download

    def test_noninteractive_input_stops_before_download_or_authentication(self):
        with patch.object(CONNECT.sys, "stdin", io.StringIO()), \
             patch.object(CONNECT, "install_gh") as install, \
             patch.object(CONNECT.subprocess, "run") as execute:
            with self.assertRaisesRegex(RuntimeError, "interactively"):
                CONNECT.main()
            install.assert_not_called()
            execute.assert_not_called()

    def test_existing_cli_is_preserved_without_downloading(self):
        with self.installer({}, existing="/offline/existing/gh") as (_, download):
            self.assertEqual(CONNECT.install_gh(), Path("/offline/existing/gh"))
            download.assert_not_called()

    def test_verified_archive_installs_only_expected_executable(self):
        with self.installer(self.release()) as (home, download):
            installed = CONNECT.install_gh()
            self.assertEqual(installed, home / ".local/bin/gh")
            self.assertEqual(installed.read_bytes(), self.executable)
            self.assertTrue(installed.stat().st_mode & stat.S_IXUSR)
            self.assertEqual([p.name for p in installed.parent.iterdir()], ["gh"])
            self.assertEqual(download.call_count, 3)

    def test_invalid_checksum_never_installs_executable(self):
        with self.installer(self.release(checksum_valid=False)) as (home, _):
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                CONNECT.install_gh()
            self.assertFalse((home / ".local/bin/gh").exists())

    def test_tar_symlink_is_rejected(self):
        with self.installer(self.release(symlink=True)) as (home, _):
            with self.assertRaisesRegex(RuntimeError, "regular file"):
                CONNECT.install_gh()
            self.assertFalse((home / ".local/bin/gh").exists())

    def test_unlisted_existing_target_is_not_overwritten(self):
        with self.installer(self.release()) as (home, _):
            target = home / ".local/bin/gh"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"existing user executable")
            with self.assertRaisesRegex(RuntimeError, "preserved"):
                CONNECT.install_gh()
            self.assertEqual(target.read_bytes(), b"existing user executable")


class RemoteReadmeIntegrationTests(unittest.TestCase):
    remote_readme = b"# Conf-Claude-Codex\nRep para IAS\n"

    def setUp(self):
        self.environment = patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})
        self.environment.start()
        self.temporary = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()
        self.environment.stop()

    @staticmethod
    def git(directory, *arguments):
        return subprocess.run(["git", "-c", "user.name=Offline fixture", "-c", "user.email=fixture@localhost",
                               *arguments], cwd=directory, check=True, capture_output=True)

    def fixture(self, *, remote_readme=None, extra_remote=False):
        bare = self.root / "remote.git"
        remote = self.root / "remote-source"
        local = self.root / "local-source"
        self.git(self.root, "init", "--bare", "--initial-branch=main", str(bare))
        self.git(self.root, "init", "--initial-branch=main", str(remote))
        readme = self.remote_readme if remote_readme is None else remote_readme
        (remote / "README.md").write_bytes(readme)
        if extra_remote:
            (remote / "existing-user-code.txt").write_text("Preserve user code.\n")
        self.git(remote, "add", ".")
        self.git(remote, "commit", "-m", "Remote fixture root")
        remote_sha = self.git(remote, "rev-parse", "HEAD").stdout.decode().strip()
        self.git(remote, "push", str(bare), "HEAD:main")
        self.git(self.root, "init", "--initial-branch=main", str(local))
        (local / "README.md").write_bytes(b"# GENIUS-5000 local fixture\nReviewable local contents.\n")
        (local / "local-payload.txt").write_bytes(b"Local scientific software fixture only.\n")
        self.git(local, "add", ".")
        self.git(local, "commit", "-m", "Local fixture root")
        local_sha = self.git(local, "rev-parse", "HEAD").stdout.decode().strip()
        self.git(local, "remote", "add", "origin", str(bare))
        self.git(local, "fetch", "origin")
        return local, bare, local_sha, remote_sha, readme

    def integrate(self, local):
        with patch.object(PUBLISH, "ROOT", local):
            return PUBLISH.integrate_remote_readme("main", {"login": "offline-fixture", "id": 12345})

    def assert_preserved(self, local, bare, local_sha, remote_sha, readme, merged):
        parents = self.git(local, "show", "--format=%P", "--no-patch", merged).stdout.decode().strip().split()
        self.assertEqual(parents, [local_sha, remote_sha])
        archive = self.git(local, "show", merged + ":docs/README.remote-original.md").stdout
        self.assertEqual(archive, readme)
        local_readme = self.git(local, "show", local_sha + ":README.md").stdout
        self.assertEqual(self.git(local, "show", merged + ":README.md").stdout, local_readme)
        self.assertEqual(self.git(local, "show", merged + ":local-payload.txt").stdout,
                         b"Local scientific software fixture only.\n")
        self.assertEqual(self.git(local, "rev-parse", "HEAD").stdout.decode().strip(), local_sha)
        self.assertEqual(self.git(bare, "rev-parse", "main").stdout.decode().strip(), remote_sha)
        self.assertEqual(self.git(local, "status", "--porcelain").stdout, b"")
        worktrees = self.git(local, "worktree", "list", "--porcelain").stdout.decode()
        self.assertEqual(worktrees.count("worktree "), 1)

    def test_unrelated_roots_merge_without_modifying_source_or_remote(self):
        local, bare, local_sha, remote_sha, readme = self.fixture()
        merged = self.integrate(local)
        self.assert_preserved(local, bare, local_sha, remote_sha, readme, merged)

    def test_remote_readme_archive_preserves_original_bytes(self):
        local, bare, local_sha, remote_sha, readme = self.fixture(remote_readme=b"# Conf-Claude-Codex\r\nRep para IAS\r\n")
        merged = self.integrate(local)
        self.assert_preserved(local, bare, local_sha, remote_sha, readme, merged)

    def test_additional_remote_files_are_rejected_without_changes(self):
        local, bare, local_sha, remote_sha, _ = self.fixture(extra_remote=True)
        with self.assertRaisesRegex(RuntimeError, "additional or changed contents"):
            self.integrate(local)
        self.assertEqual(self.git(local, "rev-parse", "HEAD").stdout.decode().strip(), local_sha)
        self.assertEqual(self.git(bare, "rev-parse", "main").stdout.decode().strip(), remote_sha)
        self.assertEqual(self.git(local, "status", "--porcelain").stdout, b"")

    def test_changed_remote_readme_is_rejected_without_changes(self):
        local, bare, local_sha, remote_sha, _ = self.fixture(remote_readme=b"A user's substantive existing README.\n")
        with self.assertRaisesRegex(RuntimeError, "additional or changed contents"):
            self.integrate(local)
        self.assertEqual(self.git(local, "rev-parse", "HEAD").stdout.decode().strip(), local_sha)
        self.assertEqual(self.git(bare, "rev-parse", "main").stdout.decode().strip(), remote_sha)
        self.assertEqual(self.git(local, "status", "--porcelain").stdout, b"")


if __name__ == "__main__":
    unittest.main()
