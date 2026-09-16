"""
Release workflow — manages version tagging and release branch lifecycle.
"""
import re
from typing import Optional
from gitwf.core.git_ops import GitOps
from gitwf.core.branch_manager import BranchManager


class ReleaseWorkflow:
    def __init__(self, git: GitOps, branch_mgr: BranchManager):
        self.git = git
        self.branch_mgr = branch_mgr

    def get_latest_version(self) -> Optional[str]:
        """Get the latest semantic version tag."""
        tags = self.git.list_tags("v*")
        for tag in tags:
            if re.match(r'^v\d+\.\d+\.\d+$', tag):
                return tag
        return None

    def bump_version(self, current: str, bump_type: str = "patch") -> str:
        """Calculate next version from current tag."""
        match = re.match(r'^v?(\d+)\.(\d+)\.(\d+)$', current)
        if not match:
            raise ValueError(f"Invalid version format: {current}")

        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        return f"v{major}.{minor}.{patch}"

    def start_release(self, version: Optional[str] = None,
                      bump_type: str = "minor") -> dict:
        """Create a release branch from develop."""
        if not version:
            current = self.get_latest_version() or "v0.0.0"
            version = self.bump_version(current, bump_type)

        branch_name = self.branch_mgr.create_release(version.lstrip("v"))

        return {
            "version": version,
            "branch": branch_name,
            "base": self.branch_mgr.develop_branch,
        }

    def finish_release(self, version: str, tag_message: str = "") -> dict:
        """Merge release branch into main and develop, create tag."""
        release_branch = f"{self.branch_mgr.config.get('release_prefix', 'release/')}{version.lstrip('v')}"

        # Merge into main
        self.git.switch_branch(self.branch_mgr.main_branch)
        self.git.merge(release_branch)

        # Tag
        tag_name = version if version.startswith("v") else f"v{version}"
        self.git.create_tag(tag_name, tag_message or f"Release {tag_name}")

        # Merge back into develop
        self.git.switch_branch(self.branch_mgr.develop_branch)
        self.git.merge(release_branch)

        # Cleanup
        self.git.delete_branch(release_branch)

        return {
            "version": tag_name,
            "merged_into": [self.branch_mgr.main_branch, self.branch_mgr.develop_branch],
            "tag": tag_name,
            "deleted_branch": release_branch,
        }
