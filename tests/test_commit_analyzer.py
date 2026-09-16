import pytest
from gitwf.core.commit_analyzer import CommitAnalyzer


@pytest.fixture
def analyzer():
    config = {
        "commit": {
            "enforce_conventional": True,
            "allowed_types": ["feat", "fix", "docs", "refactor", "test", "chore"],
            "max_subject_length": 72,
            "require_scope": False,
        }
    }
    return CommitAnalyzer(config)


def test_parse_conventional_commit(analyzer):
    line = "abc123|John|john@email.com|1700000000|feat(auth): add login endpoint"
    c = analyzer.parse(line)
    assert c.commit_type == "feat"
    assert c.scope == "auth"
    assert c.description == "add login endpoint"
    assert c.hash == "abc123"


def test_parse_no_scope(analyzer):
    line = "def456|Jane|jane@email.com|1700000000|fix: resolve null pointer crash"
    c = analyzer.parse(line)
    assert c.commit_type == "fix"
    assert c.scope == ""
    assert c.description == "resolve null pointer crash"


def test_parse_breaking_change(analyzer):
    line = "aaa111|Dev|dev@co.com|1700000000|feat!: remove deprecated API"
    c = analyzer.parse(line)
    assert c.breaking is True
    assert c.commit_type == "feat"


def test_parse_non_conventional(analyzer):
    line = "bbb222|Dev|dev@co.com|1700000000|Updated the readme file"
    c = analyzer.parse(line)
    assert c.commit_type == ""
    assert c.description == "Updated the readme file"


def test_validate_valid_commit(analyzer):
    line = "ccc333|Dev|dev@co.com|1700000000|fix(db): handle connection timeout"
    c = analyzer.parse_and_validate(line)
    assert c.valid is True
    assert c.errors == []


def test_validate_invalid_type(analyzer):
    line = "ddd444|Dev|dev@co.com|1700000000|yolo(stuff): did things"
    c = analyzer.parse_and_validate(line)
    assert c.valid is False
    assert any("Invalid type" in e for e in c.errors)


def test_validate_subject_too_long(analyzer):
    long_subject = "feat: " + "x" * 70
    line = f"eee555|Dev|dev@co.com|1700000000|{long_subject}"
    c = analyzer.parse_and_validate(line)
    assert c.valid is False
    assert any("too long" in e for e in c.errors)


def test_validate_scope_required():
    config = {"commit": {"enforce_conventional": True, "require_scope": True,
                         "allowed_types": ["feat"], "max_subject_length": 72}}
    analyzer = CommitAnalyzer(config)
    line = "fff666|Dev|dev@co.com|1700000000|feat: no scope here"
    c = analyzer.parse_and_validate(line)
    assert c.valid is False
    assert any("Scope is required" in e for e in c.errors)


def test_analyze_history(analyzer):
    lines = [
        "a1|A|a@co|1700000000|feat: add feature",
        "a2|B|b@co|1700000001|fix: fix bug",
        "a3|C|c@co|1700000002|not conventional at all",
        "a4|D|d@co|1700000003|feat!: breaking change",
    ]
    result = analyzer.analyze_history(lines)
    assert result["total"] == 4
    assert result["valid"] == 2  # feat + fix (breaking feat is also valid)
    assert result["breaking_changes"] == 1
    assert result["type_counts"]["feat"] == 2
