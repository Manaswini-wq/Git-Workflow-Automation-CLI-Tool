"""
Branch lifecycle management — create, validate, cleanup branches
following Git Flow conventions.
"""
from typing import Optional
from gitwf.core.git_ops import GitOps


class BranchManager:
    def __init__(self, git: GitOps, config: dict):
        self.git = git
        self.config = config.get("branching", {})
        self.protected = config.get("workflow", {}).get("protected_branches", ["main"])

    @property
    def main_branch(self) -> str:
        return self.config.get("main_branch", "main")

    @property
    def develop_branch(self) -> str:
        return self.config.get("develop_branch", "develop")

    def create_feature(self, name: str, base: Optional[str] = None) -> str:
        prefix = self.config.get("feature_prefix", "feature/")
        branch_name = f"{prefix}{name}"
        base_branch = base or self.develop_branch
        self.git.create_branch(branch_name, base_branch)
        return branch_name

    def create_bugfix(self, name: str, base: Optional[str] = None) -> str:
        prefix = self.config.get("bugfix_prefix", "bugfix/")
        branch_name = f"{prefix}{name}"
        base_branch = base or self.develop_branch
        self.git.create_branch(branch_name, base_branch)
        return branch_name

    def create_release(self, version: str) -> str:
        prefix = self.config.get("release_prefix", "release/")
        branch_name = f"{prefix}{version}"
        self.git.create_branch(branch_name, self.develop_branch)
        return branch_name

    def create_hotfix(self, name: str) -> str:
        prefix = self.config.get("hotfix_prefix", "hotfix/")
        branch_name = f"{prefix}{name}"
        self.git.create_branch(branch_name, self.main_branch)
        return branch_name

    def get_branch_type(self, branch_name: str) -> str:
        """Classify a branch by its prefix."""
        prefixes = {
            self.config.get("feature_prefix", "feature/"): "feature",
            self.config.get("bugfix_prefix", "bugfix/"): "bugfix",
            self.config.get("release_prefix", "release/"): "release",
            self.config.get("hotfix_prefix", "hotfix/"): "hotfix",
        }
        for prefix, btype in prefixes.items():
            if branch_name.startswith(prefix):
                return btype
        if branch_name == self.main_branch:
            return "main"
        if branch_name == self.develop_branch:
            return "develop"
        return "unknown"

    def is_protected(self, branch_name: str) -> bool:
        return branch_name in self.protected

    def get_stale_branches(self, merged_into: str = "main") -> list[str]:
        """Find branches already merged into the target that can be cleaned up."""
        all_branches = self.git.list_branches()
        stale = []
        for b in all_branches:
            if b in self.protected:
                continue
            if self.git.is_ancestor(b, merged_into):
                stale.append(b)
        return stale

    def cleanup_merged(self, target: str = "main", dry_run: bool = True) -> list[str]:
        """Delete branches already merged into target."""
        stale = self.get_stale_branches(target)
        deleted = []
        for b in stale:
            if not dry_run:
                self.git.delete_branch(b)
            deleted.append(b)
        return deleted
