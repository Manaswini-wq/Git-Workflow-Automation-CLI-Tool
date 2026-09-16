"""
Repository statistics — contributor analysis, commit frequency, code churn.
"""
from collections import defaultdict
from datetime import datetime
from gitwf.core.git_ops import GitOps
from gitwf.core.commit_analyzer import CommitAnalyzer


class RepoStats:
    def __init__(self, git: GitOps, analyzer: CommitAnalyzer):
        self.git = git
        self.analyzer = analyzer

    def contributor_stats(self, count: int = 200) -> list[dict]:
        """Analyze contributions by author."""
        log_lines = self.git.log(count=count)
        authors = defaultdict(lambda: {"commits": 0, "types": defaultdict(int)})

        for line in log_lines:
            commit = self.analyzer.parse(line)
            key = commit.author
            authors[key]["commits"] += 1
            authors[key]["email"] = commit.email
            if commit.commit_type:
                authors[key]["types"][commit.commit_type] += 1

        result = []
        for name, data in sorted(authors.items(), key=lambda x: x[1]["commits"], reverse=True):
            result.append({
                "author": name,
                "email": data.get("email", ""),
                "commits": data["commits"],
                "top_types": dict(sorted(data["types"].items(),
                                         key=lambda x: x[1], reverse=True)[:3]),
            })
        return result

    def commit_frequency(self, count: int = 200) -> dict:
        """Analyze commit frequency by day of week and hour."""
        log_lines = self.git.log(count=count)
        by_day = defaultdict(int)
        by_hour = defaultdict(int)

        for line in log_lines:
            commit = self.analyzer.parse(line)
            if commit.timestamp > 0:
                dt = datetime.fromtimestamp(commit.timestamp)
                by_day[dt.strftime("%A")] += 1
                by_hour[dt.hour] += 1

        return {
            "by_day": dict(by_day),
            "by_hour": dict(sorted(by_hour.items())),
            "most_active_day": max(by_day, key=by_day.get) if by_day else "N/A",
            "most_active_hour": max(by_hour, key=by_hour.get) if by_hour else "N/A",
        }

    def summary(self) -> dict:
        """Quick repo summary."""
        branches = self.git.list_branches()
        tags = self.git.list_tags()
        current = self.git.current_branch()

        return {
            "current_branch": current,
            "total_branches": len(branches),
            "total_tags": len(tags),
            "latest_tag": tags[0] if tags else "none",
            "remote": self.git.get_remote_url(),
        }
