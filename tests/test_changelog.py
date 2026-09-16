import pytest
from unittest.mock import MagicMock
from gitwf.reporting.changelog_generator import ChangelogGenerator
from gitwf.core.commit_analyzer import CommitAnalyzer


@pytest.fixture
def changelog_gen():
    git = MagicMock()
    config = {
        "commit": {"enforce_conventional": False, "allowed_types": ["feat", "fix"]},
        "changelog": {"group_by_type": True, "include_breaking": True},
    }
    analyzer = CommitAnalyzer(config)
    return ChangelogGenerator(git, analyzer, config)


def test_grouped_changelog(changelog_gen):
    changelog_gen.git.log.return_value = [
        "a1|Dev|d@co|1700000000|feat(api): add user endpoint",
        "a2|Dev|d@co|1700000001|fix(db): connection pool leak",
        "a3|Dev|d@co|1700000002|feat: new dashboard",
        "a4|Dev|d@co|1700000003|docs: update readme",
    ]
    result = changelog_gen.generate("v1.0", "HEAD", "v1.1")
    assert "v1.1" in result
    assert "Features" in result
    assert "Bug Fixes" in result
    assert "add user endpoint" in result


def test_breaking_changes(changelog_gen):
    changelog_gen.git.log.return_value = [
        "b1|Dev|d@co|1700000000|feat!: remove old API",
    ]
    result = changelog_gen.generate("v1.0", "HEAD", "v2.0")
    assert "BREAKING" in result


def test_empty_log(changelog_gen):
    changelog_gen.git.log.return_value = []
    result = changelog_gen.generate("v1.0", "HEAD", "v1.1")
    assert "v1.1" in result
