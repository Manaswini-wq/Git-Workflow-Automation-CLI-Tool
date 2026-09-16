"""
Conventional commit parser and validator.
Format: <type>(<scope>): <subject>
Example: feat(auth): add OAuth2 login flow
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCommit:
    hash: str
    author: str
    email: str
    timestamp: int
    subject: str
    commit_type: str = ""
    scope: str = ""
    description: str = ""
    breaking: bool = False
    valid: bool = True
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


CONVENTIONAL_PATTERN = re.compile(
    r'^(?P<type>\w+)'
    r'(?:\((?P<scope>[^)]+)\))?'
    r'(?P<breaking>!)?'
    r':\s*'
    r'(?P<description>.+)$'
)


class CommitAnalyzer:
    def __init__(self, config: dict):
        commit_cfg = config.get("commit", {})
        self.allowed_types = set(commit_cfg.get("allowed_types", [
            "feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "ci"
        ]))
        self.max_subject_length = commit_cfg.get("max_subject_length", 72)
        self.require_scope = commit_cfg.get("require_scope", False)
        self.enforce = commit_cfg.get("enforce_conventional", True)

    def parse(self, commit_line: str) -> ParsedCommit:
        """Parse a git log line (format: hash|author|email|timestamp|subject)."""
        parts = commit_line.split("|", 4)
        if len(parts) < 5:
            return ParsedCommit(
                hash="", author="", email="", timestamp=0,
                subject=commit_line, valid=False,
                errors=["Invalid log format"]
            )

        commit = ParsedCommit(
            hash=parts[0],
            author=parts[1],
            email=parts[2],
            timestamp=int(parts[3]) if parts[3].isdigit() else 0,
            subject=parts[4],
        )

        match = CONVENTIONAL_PATTERN.match(commit.subject)
        if match:
            commit.commit_type = match.group("type")
            commit.scope = match.group("scope") or ""
            commit.breaking = match.group("breaking") == "!"
            commit.description = match.group("description")
        else:
            commit.commit_type = ""
            commit.description = commit.subject

        return commit

    def validate(self, commit: ParsedCommit) -> ParsedCommit:
        """Validate a parsed commit against configured rules."""
        if not self.enforce:
            return commit

        # Check conventional format
        if not commit.commit_type:
            commit.valid = False
            commit.errors.append("Not a conventional commit (missing type)")
            return commit

        # Check allowed types
        if commit.commit_type not in self.allowed_types:
            commit.valid = False
            commit.errors.append(
                f"Invalid type '{commit.commit_type}'. "
                f"Allowed: {sorted(self.allowed_types)}"
            )

        # Check scope requirement
        if self.require_scope and not commit.scope:
            commit.valid = False
            commit.errors.append("Scope is required but missing")

        # Check subject length
        if len(commit.subject) > self.max_subject_length:
            commit.valid = False
            commit.errors.append(
                f"Subject too long ({len(commit.subject)}/{self.max_subject_length})"
            )

        # Check description not empty
        if not commit.description.strip():
            commit.valid = False
            commit.errors.append("Empty description after type/scope")

        return commit

    def parse_and_validate(self, commit_line: str) -> ParsedCommit:
        commit = self.parse(commit_line)
        return self.validate(commit)

    def analyze_history(self, log_lines: list[str]) -> dict:
        """Analyze a batch of commits — returns summary stats."""
        commits = [self.parse_and_validate(line) for line in log_lines]
        total = len(commits)
        valid = sum(1 for c in commits if c.valid)
        type_counts = {}
        for c in commits:
            if c.commit_type:
                type_counts[c.commit_type] = type_counts.get(c.commit_type, 0) + 1

        breaking = [c for c in commits if c.breaking]
        invalid = [c for c in commits if not c.valid]

        return {
            "total": total,
            "valid": valid,
            "invalid": len(invalid),
            "compliance_pct": round(valid / total * 100, 1) if total > 0 else 0,
            "type_counts": type_counts,
            "breaking_changes": len(breaking),
            "invalid_commits": [
                {"hash": c.hash[:8], "subject": c.subject, "errors": c.errors}
                for c in invalid
            ],
        }
