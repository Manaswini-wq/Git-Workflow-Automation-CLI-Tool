"""
CLI integration tests — verifies command routing.
"""
import pytest
from unittest.mock import patch, MagicMock
from gitwf.cli import main


@patch("gitwf.cli.GitOps")
@patch("gitwf.cli.load_config")
def test_help_command(mock_config, mock_git, capsys):
    mock_config.return_value = {}
    with patch("sys.argv", ["gitwf", "help"]):
        main()
    output = capsys.readouterr().out
    assert "Usage" in output


@patch("gitwf.cli.GitOps")
@patch("gitwf.cli.load_config")
def test_unknown_command(mock_config, mock_git, capsys):
    mock_config.return_value = {}
    with patch("sys.argv", ["gitwf", "nonexistent"]):
        main()
    output = capsys.readouterr().out
    assert "Unknown command" in output
