"""
Pull request readiness checks — validates branch before merge.
"""
from gitwf.core.git_ops import GitOps
from gitwf.core.branch_manager import BranchManager
from gitwf.core.commit_analyzer import CommitAnalyzer
from dataclasses import dataclass, field


@dataclass
class PRCheck:
    name: str
    passed: bool
    message: str


@dataclass
class PRReport:
    branch: str
    target: str
    checks: list[PRCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)


class PRWorkflow:
    def __init__(self, git: GitOps, branch_mgr: BranchManager,
                 commit_analyzer: CommitAnalyzer, config: dict):
        self.git = git
        self.branch_mgr = branch_mgr
        self.analyzer = commit_analyzer
        self.config = config.get("workflow", {})

    def check_pr_readiness(self, source: str, target: str) -> PRReport:
        """Run all pre-merge checks on a branch."""
        report = PRReport(branch=source, target=target)

        # Check 1: Branch exists
        exists = self.git.branch_exists(source)
        report.checks.append(PRCheck(
            "Branch exists", exists,
            f"Branch '{source}' {'found' if exists else 'not found'}"
        ))
        if not exists:
            return report

        # Check 2: Not merging into itself
        not_same = source != target
        report.checks.append(PRCheck(
            "Different branches", not_same,
            "Source and target must be different"
        ))

        # Check 3: Working tree clean
        clean = self.git.is_clean()
        report.checks.append(PRCheck(
            "Clean working tree", clean,
            "Working tree is clean" if clean else "Uncommitted changes detected"
        ))

        # Check 4: Branch is up to date with target
        if self.config.get("require_branch_up_to_date", True):
            up_to_date = self.git.is_ancestor(target, source)
            report.checks.append(PRCheck(
                "Up to date", up_to_date,
                f"Branch is {'up to date' if up_to_date else 'behind'} with {target}"
            ))

        # Check 5: Validate commits
        log_lines = self.git.log(count=50, branch=f"{target}..{source}")
        if log_lines:
            analysis = self.analyzer.analyze_history(log_lines)
            all_valid = analysis["invalid"] == 0
            report.checks.append(PRCheck(
                "Commit messages", all_valid,
                f"{analysis['valid']}/{analysis['total']} commits follow conventions"
                + (f" — {analysis['invalid']} invalid" if not all_valid else "")
            ))

        # Check 6: Has changes
        changed = self.git.changed_files(target, source)
        has_changes = len(changed) > 0
        report.checks.append(PRCheck(
            "Has changes", has_changes,
            f"{len(changed)} files changed" if has_changes else "No changes detected"
        ))

        return report
