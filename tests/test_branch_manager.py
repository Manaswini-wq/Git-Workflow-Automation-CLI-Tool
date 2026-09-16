import pytest
from unittest.mock import MagicMock
from gitwf.core.branch_manager import BranchManager


@pytest.fixture
def branch_mgr():
    git = MagicMock()
    config = {
        "branching": {
            "main_branch": "main",
            "develop_branch": "develop",
            "feature_prefix": "feature/",
            "bugfix_prefix": "bugfix/",
            "release_prefix": "release/",
            "hotfix_prefix": "hotfix/",
        },
        "workflow": {
            "protected_branches": ["main", "develop"],
        },
    }
    return BranchManager(git, config)


def test_create_feature(branch_mgr):
    name = branch_mgr.create_feature("login-page")
    assert name == "feature/login-page"
    branch_mgr.git.create_branch.assert_called_with("feature/login-page", "develop")


def test_create_bugfix(branch_mgr):
    name = branch_mgr.create_bugfix("null-pointer")
    assert name == "bugfix/null-pointer"
    branch_mgr.git.create_branch.assert_called_with("bugfix/null-pointer", "develop")


def test_create_hotfix(branch_mgr):
    name = branch_mgr.create_hotfix("security-patch")
    assert name == "hotfix/security-patch"
    branch_mgr.git.create_branch.assert_called_with("hotfix/security-patch", "main")


def test_create_release(branch_mgr):
    name = branch_mgr.create_release("1.2.0")
    assert name == "release/1.2.0"


def test_branch_type_detection(branch_mgr):
    assert branch_mgr.get_branch_type("feature/login") == "feature"
    assert branch_mgr.get_branch_type("bugfix/crash") == "bugfix"
    assert branch_mgr.get_branch_type("release/1.0") == "release"
    assert branch_mgr.get_branch_type("hotfix/urgent") == "hotfix"
    assert branch_mgr.get_branch_type("main") == "main"
    assert branch_mgr.get_branch_type("develop") == "develop"
    assert branch_mgr.get_branch_type("random") == "unknown"


def test_protected_branches(branch_mgr):
    assert branch_mgr.is_protected("main") is True
    assert branch_mgr.is_protected("develop") is True
    assert branch_mgr.is_protected("feature/foo") is False
