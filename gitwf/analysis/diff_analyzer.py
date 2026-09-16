"""
Diff analysis — file change statistics, hotspot detection.
"""
from collections import defaultdict
from gitwf.core.git_ops import GitOps


class DiffAnalyzer:
    def __init__(self, git: GitOps):
        self.git = git

    def file_changes(self, base: str, head: str = "HEAD") -> list[dict]:
        """Get per-file change statistics (lines added/removed)."""
        lines = self.git.diff_numstat(base, head)
        changes = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 3:
                added = int(parts[0]) if parts[0] != "-" else 0
                removed = int(parts[1]) if parts[1] != "-" else 0
                changes.append({
                    "file": parts[2],
                    "added": added,
                    "removed": removed,
                    "churn": added + removed,
                })
        return sorted(changes, key=lambda x: x["churn"], reverse=True)

    def hotspots(self, count: int = 100) -> list[dict]:
        """Find files that change most frequently across recent commits."""
        freq = defaultdict(int)
        log_lines = self.git.log(format_str="%H", count=count)

        for i in range(len(log_lines) - 1):
            try:
                files = self.git.changed_files(log_lines[i + 1], log_lines[i])
                for f in files:
                    freq[f] += 1
            except Exception:
                continue

        result = [{"file": f, "change_count": c}
                  for f, c in sorted(freq.items(), key=lambda x: x[1], reverse=True)]
        return result[:20]

    def summary(self, base: str, head: str = "HEAD") -> dict:
        """Summarize changes between two refs."""
        changes = self.file_changes(base, head)
        total_added = sum(c["added"] for c in changes)
        total_removed = sum(c["removed"] for c in changes)

        # Group by file extension
        by_ext = defaultdict(lambda: {"files": 0, "added": 0, "removed": 0})
        for c in changes:
            ext = c["file"].rsplit(".", 1)[-1] if "." in c["file"] else "other"
            by_ext[ext]["files"] += 1
            by_ext[ext]["added"] += c["added"]
            by_ext[ext]["removed"] += c["removed"]

        return {
            "files_changed": len(changes),
            "total_added": total_added,
            "total_removed": total_removed,
            "net_change": total_added - total_removed,
            "by_extension": dict(by_ext),
            "top_churned": changes[:5],
        }
