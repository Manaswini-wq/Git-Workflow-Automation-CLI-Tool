"""
YAML configuration loader with defaults.
"""
import os
import yaml


def load_config(path: str = "config/default_config.yaml") -> dict:
    """Load config from YAML file, returning defaults if file not found."""
    defaults = {
        "branching": {
            "main_branch": "main",
            "develop_branch": "develop",
            "feature_prefix": "feature/",
            "bugfix_prefix": "bugfix/",
            "release_prefix": "release/",
            "hotfix_prefix": "hotfix/",
        },
        "commit": {
            "enforce_conventional": True,
            "allowed_types": ["feat", "fix", "docs", "style", "refactor",
                              "test", "chore", "perf", "ci"],
            "max_subject_length": 72,
            "require_scope": False,
        },
        "workflow": {
            "require_branch_up_to_date": True,
            "auto_delete_merged_branches": True,
            "protected_branches": ["main", "develop"],
        },
        "changelog": {
            "output": "CHANGELOG.md",
            "group_by_type": True,
            "include_breaking": True,
        },
    }

    if os.path.exists(path):
        with open(path) as f:
            user_config = yaml.safe_load(f) or {}
        # Merge user config over defaults
        for key, value in user_config.items():
            if isinstance(value, dict) and key in defaults:
                defaults[key].update(value)
            else:
                defaults[key] = value

    return defaults
