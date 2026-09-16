"""
Low-level Git operations — wraps git CLI commands with error handling.
All git interaction goes through this module (single point of change for testing).
"""
import subprocess
import os
from typing import Optional


class GitError(Exception):
    """Raised when a git command fails."""
    def __init__(self, command: str, returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"git {command} failed (rc={returncode}): {stderr.strip()}")


class GitOps:
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)

    def _run(self, args: list[str], check: bool = True) -> str:
        """Execute a git command and return stdout."""
        cmd = ["git", "-C", self.repo_path] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise GitError(args[0], result.returncode, result.stderr)
        return result.stdout.strip()

    # --- Branch operations ---

    def current_branch(self) -> str:
        return self._run(["rev-parse", "--abbrev-ref", "HEAD"])

    def list_branches(self, remote: bool = False) -> list[str]:
        args = ["branch", "--format=%(refname:short)"]
        if remote:
            args.append("-r")
        output = self._run(args)
        return [b.strip() for b in output.splitlines() if b.strip()]

    def branch_exists(self, name: str) -> bool:
        try:
            self._run(["rev-parse", "--verify", name])
            return True
        except GitError:
            return False

    def create_branch(self, name: str, base: Optional[str] = None):
        args = ["checkout", "-b", name]
        if base:
            args.append(base)
        self._run(args)

    def switch_branch(self, name: str):
        self._run(["checkout", name])

    def delete_branch(self, name: str, force: bool = False):
        flag = "-D" if force else "-d"
        self._run(["branch", flag, name])

    def merge(self, branch: str, no_ff: bool = True) -> str:
        args = ["merge", branch]
        if no_ff:
            args.append("--no-ff")
        return self._run(args)

    # --- Commit operations ---

    def log(self, format_str: str = "%H|%an|%ae|%at|%s",
            count: int = 50, branch: Optional[str] = None,
            since: Optional[str] = None) -> list[str]:
        args = ["log", f"--format={format_str}", f"-{count}"]
        if since:
            args.append(f"--since={since}")
        if branch:
            args.append(branch)
        output = self._run(args)
        return [line for line in output.splitlines() if line.strip()]

    def commit_count(self, branch: Optional[str] = None) -> int:
        args = ["rev-list", "--count"]
        args.append(branch or "HEAD")
        return int(self._run(args))

    # --- Diff operations ---

    def diff_stat(self, base: str, head: str = "HEAD") -> str:
        return self._run(["diff", "--stat", f"{base}..{head}"])

    def diff_numstat(self, base: str, head: str = "HEAD") -> list[str]:
        output = self._run(["diff", "--numstat", f"{base}..{head}"])
        return output.splitlines()

    def changed_files(self, base: str, head: str = "HEAD") -> list[str]:
        output = self._run(["diff", "--name-only", f"{base}..{head}"])
        return [f for f in output.splitlines() if f.strip()]

    # --- Status ---

    def status(self) -> str:
        return self._run(["status", "--porcelain"])

    def is_clean(self) -> bool:
        return self.status() == ""

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        try:
            self._run(["merge-base", "--is-ancestor", ancestor, descendant])
            return True
        except GitError:
            return False

    # --- Tags ---

    def list_tags(self, pattern: str = "") -> list[str]:
        args = ["tag", "--sort=-version:refname"]
        if pattern:
            args.extend(["-l", pattern])
        output = self._run(args)
        return [t for t in output.splitlines() if t.strip()]

    def create_tag(self, name: str, message: str = ""):
        args = ["tag"]
        if message:
            args.extend(["-a", name, "-m", message])
        else:
            args.append(name)
        self._run(args)

    # --- Remote ---

    def fetch(self, prune: bool = True):
        args = ["fetch"]
        if prune:
            args.append("--prune")
        self._run(args)

    def get_remote_url(self) -> str:
        return self._run(["remote", "get-url", "origin"], check=False)
