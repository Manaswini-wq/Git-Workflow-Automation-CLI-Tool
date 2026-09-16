"""
Tests for GitOps — uses a real temporary git repo.
"""
import os
import pytest
import tempfile
import subprocess
from gitwf.core.git_ops import GitOps, GitError


@pytest.fixture
def temp_repo():
    """Create a temporary git repo with initial commit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init", tmpdir], capture_output=True)
        subprocess.run(["git", "-C", tmpdir, "config", "user.email", "test@test.com"],
                       capture_output=True)
        subprocess.run(["git", "-C", tmpdir, "config", "user.name", "Test"],
                       capture_output=True)

        # Create initial commit
        filepath = os.path.join(tmpdir, "README.md")
        with open(filepath, "w") as f:
            f.write("# Test Repo\n")
        subprocess.run(["git", "-C", tmpdir, "add", "."], capture_output=True)
        subprocess.run(["git", "-C", tmpdir, "commit", "-m", "feat: initial commit"],
                       capture_output=True)

        yield tmpdir


def test_current_branch(temp_repo):
    git = GitOps(temp_repo)
    branch = git.current_branch()
    assert branch in ("main", "master")


def test_is_clean(temp_repo):
    git = GitOps(temp_repo)
    assert git.is_clean() is True

    with open(os.path.join(temp_repo, "dirty.txt"), "w") as f:
        f.write("dirty")
    assert git.is_clean() is False


def test_branch_operations(temp_repo):
    git = GitOps(temp_repo)
    git.create_branch("feature/test")
    assert git.current_branch() == "feature/test"
    assert git.branch_exists("feature/test")

    git.switch_branch("main") if git.branch_exists("main") else git.switch_branch("master")


def test_commit_count(temp_repo):
    git = GitOps(temp_repo)
    assert git.commit_count() >= 1


def test_list_branches(temp_repo):
    git = GitOps(temp_repo)
    branches = git.list_branches()
    assert len(branches) >= 1
