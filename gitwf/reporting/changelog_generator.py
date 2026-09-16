"""
Auto-generate CHANGELOG.md from conventional commits between two tags/refs.
"""
from collections import defaultdict
from datetime import datetime
from gitwf.core.git_ops import GitOps
from gitwf.core.commit_analyzer import CommitAnalyzer, ParsedCommit


TYPE_HEADERS = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "style": "Styles",
    "refactor": "Refactoring",
    "test": "Tests",
    "chore": "Chores",
    "perf": "Performance",
    "ci": "CI/CD",
}


class ChangelogGenerator:
    def __init__(self, git: GitOps, analyzer: CommitAnalyzer, config: dict):
        self.git = git
        self.analyzer = analyzer
        self.config = config.get("changelog", {})

    def generate(self, from_ref: str, to_ref: str = "HEAD",
                 version: str = "Unreleased") -> str:
        """Generate changelog markdown between two refs."""
        log_lines = self.git.log(count=500, branch=f"{from_ref}..{to_ref}")
        commits = [self.analyzer.parse(line) for line in log_lines]

        if self.config.get("group_by_type", True):
            return self._grouped_changelog(commits, version)
        return self._flat_changelog(commits, version)

    def _grouped_changelog(self, commits: list[ParsedCommit], version: str) -> str:
        groups = defaultdict(list)
        breaking = []

        for c in commits:
            if c.breaking:
                breaking.append(c)
            key = c.commit_type or "other"
            groups[key].append(c)

        lines = [f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n"]

        if breaking and self.config.get("include_breaking", True):
            lines.append("### BREAKING CHANGES\n")
            for c in breaking:
                lines.append(f"- {self._format_commit(c)}")
            lines.append("")

        for ctype in ["feat", "fix", "perf", "refactor", "docs", "test", "chore", "style", "ci"]:
            if ctype in groups:
                header = TYPE_HEADERS.get(ctype, ctype.capitalize())
                lines.append(f"### {header}\n")
                for c in groups[ctype]:
                    lines.append(f"- {self._format_commit(c)}")
                lines.append("")

        return "\n".join(lines)

    def _flat_changelog(self, commits: list[ParsedCommit], version: str) -> str:
        lines = [f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n"]
        for c in commits:
            lines.append(f"- {self._format_commit(c)}")
        return "\n".join(lines)

    def _format_commit(self, commit: ParsedCommit) -> str:
        scope = f"**{commit.scope}**: " if commit.scope else ""
        breaking = " **[BREAKING]**" if commit.breaking else ""
        return f"{scope}{commit.description}{breaking} ({commit.hash[:8]})"

    def generate_full(self) -> str:
        """Generate changelog for all tagged versions."""
        tags = self.git.list_tags("v*")
        if not tags:
            return self.generate("HEAD~50", "HEAD", "Unreleased")

        sections = []

        # Unreleased section
        unreleased = self.generate(tags[0], "HEAD", "Unreleased")
        if unreleased.count("\n") > 3:
            sections.append(unreleased)

        # Per-tag sections
        for i in range(len(tags) - 1):
            section = self.generate(tags[i + 1], tags[i], tags[i])
            sections.append(section)

        header = "# Changelog\n\nAll notable changes documented automatically from conventional commits.\n\n"
        return header + "\n".join(sections)
