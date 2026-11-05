"""Exercise the workflow's actual push commands against a local Git remote."""

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / "workflows" / "update-commiter.yml"
BRANCH = "automation/commiter-v3.0.1"


class UpdateBranchTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        self.run_git("init", "--bare", "--initial-branch=main", str(self.remote), cwd=self.root)
        self.run_git("init", "--initial-branch=main", str(self.work), cwd=self.root)
        self.run_git("config", "user.name", "Branch Test")
        self.run_git("config", "user.email", "branch-test@example.invalid")
        self.run_git("remote", "add", "origin", str(self.remote))
        self.commit_file("base.txt")
        self.run_git("push", "origin", "main")
        self.base = self.run_git("rev-parse", "HEAD")

    def run_git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.work, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def commit_file(self, name):
        (self.work / name).write_text(name, encoding="utf-8")
        self.run_git("add", "--", name)
        self.run_git("commit", "-m", name)
        return self.run_git("rev-parse", "HEAD")

    def publish(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        start = workflow.index("          git fetch origin")
        commands = textwrap.dedent(workflow[start:].split("\n\n", 1)[0])
        return subprocess.run(
            ["bash", "-eu", "-c", commands], cwd=self.work,
            env={**os.environ, "branch": BRANCH}, capture_output=True, text=True,
        )

    def remote_head(self):
        return self.run_git("--git-dir", str(self.remote), "rev-parse", f"refs/heads/{BRANCH}")

    def test_creates_new_branch(self):
        head = self.commit_file("update.txt")
        self.assertEqual(self.publish().returncode, 0)
        self.assertEqual(self.remote_head(), head)

    def test_fast_forward_preserves_existing_commit(self):
        previous = self.commit_file("manual-fix.txt")
        self.run_git("push", "origin", f"HEAD:{BRANCH}")
        head = self.commit_file("update.txt")
        self.assertEqual(self.publish().returncode, 0)
        self.assertEqual(self.remote_head(), head)
        self.run_git("merge-base", "--is-ancestor", previous, head)

    def test_rejects_divergent_update_after_fetch(self):
        previous = self.commit_file("manual-fix.txt")
        self.run_git("push", "origin", f"HEAD:{BRANCH}")
        self.run_git("switch", "-c", "regenerated-update", self.base)
        self.commit_file("regenerated.txt")
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_head(), previous)

    def test_fetch_error_stops_publication(self):
        self.run_git("remote", "set-url", "origin", str(self.root / "missing.git"))
        self.assertNotEqual(self.publish().returncode, 0)


if __name__ == "__main__":
    unittest.main()
