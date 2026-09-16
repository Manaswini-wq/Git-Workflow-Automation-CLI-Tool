import pytest
from unittest.mock import MagicMock
from gitwf.analysis.diff_analyzer import DiffAnalyzer


@pytest.fixture
def diff_analyzer():
    git = MagicMock()
    return DiffAnalyzer(git)


def test_file_changes(diff_analyzer):
    diff_analyzer.git.diff_numstat.return_value = [
        "50\t10\tsrc/main.py",
        "20\t5\tsrc/utils.py",
        "3\t0\tREADME.md",
    ]
    changes = diff_analyzer.file_changes("v1.0", "HEAD")
    assert len(changes) == 3
    assert changes[0]["file"] == "src/main.py"  # highest churn first
    assert changes[0]["added"] == 50
    assert changes[0]["removed"] == 10
    assert changes[0]["churn"] == 60


def test_summary(diff_analyzer):
    diff_analyzer.git.diff_numstat.return_value = [
        "100\t20\tsrc/app.py",
        "10\t5\ttests/test_app.py",
    ]
    summary = diff_analyzer.summary("v1.0")
    assert summary["files_changed"] == 2
    assert summary["total_added"] == 110
    assert summary["total_removed"] == 25
    assert summary["net_change"] == 85
    assert "py" in summary["by_extension"]


def test_empty_diff(diff_analyzer):
    diff_analyzer.git.diff_numstat.return_value = []
    changes = diff_analyzer.file_changes("v1.0")
    assert changes == []
