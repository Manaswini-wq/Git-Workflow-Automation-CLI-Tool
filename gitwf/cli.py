"""
CLI entry point — subcommand routing.
"""
import sys
from gitwf.core.git_ops import GitOps
from gitwf.core.branch_manager import BranchManager
from gitwf.core.commit_analyzer import CommitAnalyzer
from gitwf.workflow.pr_workflow import PRWorkflow
from gitwf.workflow.release_workflow import ReleaseWorkflow
from gitwf.workflow.hooks import HookManager
from gitwf.analysis.repo_stats import RepoStats
from gitwf.analysis.diff_analyzer import DiffAnalyzer
from gitwf.reporting.changelog_generator import ChangelogGenerator
from gitwf.utils.config_loader import load_config
from gitwf.utils.console import print_header, print_table, print_check, print_key_value


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        return

    config = load_config()
    git = GitOps()
    branch_mgr = BranchManager(git, config)
    analyzer = CommitAnalyzer(config)

    command = args[0]

    if command == "status":
        cmd_status(git, analyzer, config)
    elif command == "feature":
        cmd_feature(branch_mgr, args[1:])
    elif command == "bugfix":
        cmd_bugfix(branch_mgr, args[1:])
    elif command == "hotfix":
        cmd_hotfix(branch_mgr, args[1:])
    elif command == "pr-check":
        cmd_pr_check(git, branch_mgr, analyzer, config, args[1:])
    elif command == "release":
        cmd_release(git, branch_mgr, args[1:])
    elif command == "changelog":
        cmd_changelog(git, analyzer, config, args[1:])
    elif command == "stats":
        cmd_stats(git, analyzer)
    elif command == "diff":
        cmd_diff(git, args[1:])
    elif command == "cleanup":
        cmd_cleanup(branch_mgr, args[1:])
    elif command == "hooks":
        cmd_hooks(args[1:])
    elif command == "validate":
        cmd_validate(git, analyzer, args[1:])
    else:
        print(f"Unknown command: {command}")
        print_help()


def cmd_status(git, analyzer, config):
    print_header("Repository Status")
    stats = RepoStats(git, analyzer)
    summary = stats.summary()
    print_key_value(summary)


def cmd_feature(branch_mgr, args):
    if not args:
        print("Usage: gitwf feature <name>")
        return
    name = branch_mgr.create_feature(args[0])
    print(f"Created feature branch: {name}")


def cmd_bugfix(branch_mgr, args):
    if not args:
        print("Usage: gitwf bugfix <name>")
        return
    name = branch_mgr.create_bugfix(args[0])
    print(f"Created bugfix branch: {name}")


def cmd_hotfix(branch_mgr, args):
    if not args:
        print("Usage: gitwf hotfix <name>")
        return
    name = branch_mgr.create_hotfix(args[0])
    print(f"Created hotfix branch: {name}")


def cmd_pr_check(git, branch_mgr, analyzer, config, args):
    source = args[0] if args else git.current_branch()
    target = args[1] if len(args) > 1 else branch_mgr.develop_branch

    print_header(f"PR Check: {source} -> {target}")
    wf = PRWorkflow(git, branch_mgr, analyzer, config)
    report = wf.check_pr_readiness(source, target)

    for check in report.checks:
        print_check(check.name, check.passed, check.message)

    status = "READY" if report.all_passed else "NOT READY"
    print(f"\n  Result: {status} ({report.passed_count}/{len(report.checks)} checks passed)")


def cmd_release(git, branch_mgr, args):
    wf = ReleaseWorkflow(git, branch_mgr)
    if not args:
        version = wf.get_latest_version() or "v0.0.0"
        print(f"Latest version: {version}")
        return
    if args[0] == "start":
        bump = args[1] if len(args) > 1 else "minor"
        result = wf.start_release(bump_type=bump)
        print(f"Release started: {result['version']} on {result['branch']}")
    elif args[0] == "finish":
        version = args[1] if len(args) > 1 else ""
        if not version:
            print("Usage: gitwf release finish <version>")
            return
        result = wf.finish_release(version)
        print(f"Release complete: {result['tag']}")


def cmd_changelog(git, analyzer, config, args):
    gen = ChangelogGenerator(git, analyzer, config)
    if len(args) >= 2:
        content = gen.generate(args[0], args[1],
                               args[2] if len(args) > 2 else "Unreleased")
    else:
        content = gen.generate_full()

    output = config.get("changelog", {}).get("output", "CHANGELOG.md")
    with open(output, "w") as f:
        f.write(content)
    print(f"Changelog written to {output}")


def cmd_stats(git, analyzer):
    print_header("Repository Statistics")
    stats = RepoStats(git, analyzer)

    contributors = stats.contributor_stats()
    if contributors:
        print("\nTop Contributors:")
        rows = [[c["author"], str(c["commits"]),
                 ", ".join(f"{t}:{n}" for t, n in list(c["top_types"].items())[:3])]
                for c in contributors[:10]]
        print_table(["Author", "Commits", "Top Types"], rows)

    freq = stats.commit_frequency()
    print(f"\nMost active day:  {freq['most_active_day']}")
    print(f"Most active hour: {freq['most_active_hour']}:00")


def cmd_diff(git, args):
    if not args:
        print("Usage: gitwf diff <base> [head]")
        return
    da = DiffAnalyzer(git)
    summary = da.summary(args[0], args[1] if len(args) > 1 else "HEAD")
    print_header("Diff Summary")
    print(f"  Files changed: {summary['files_changed']}")
    print(f"  Lines added:   +{summary['total_added']}")
    print(f"  Lines removed: -{summary['total_removed']}")
    print(f"  Net change:    {summary['net_change']}")

    if summary["top_churned"]:
        print("\n  Top changed files:")
        for f in summary["top_churned"]:
            print(f"    {f['file']}: +{f['added']} -{f['removed']}")


def cmd_cleanup(branch_mgr, args):
    dry_run = "--dry-run" in args
    deleted = branch_mgr.cleanup_merged(dry_run=dry_run)
    action = "Would delete" if dry_run else "Deleted"
    if deleted:
        for b in deleted:
            print(f"  {action}: {b}")
    else:
        print("  No stale branches found")


def cmd_hooks(args):
    hm = HookManager()
    if not args or args[0] == "install":
        paths = hm.install_all()
        for p in paths:
            print(f"  Installed: {p}")
    elif args[0] == "list":
        hooks = hm.list_installed()
        print(f"  Installed hooks: {', '.join(hooks) if hooks else 'none'}")


def cmd_validate(git, analyzer, args):
    count = int(args[0]) if args else 20
    print_header(f"Validating last {count} commits")
    log_lines = git.log(count=count)
    analysis = analyzer.analyze_history(log_lines)

    print(f"  Total:      {analysis['total']}")
    print(f"  Valid:      {analysis['valid']}")
    print(f"  Invalid:    {analysis['invalid']}")
    print(f"  Compliance: {analysis['compliance_pct']}%")

    if analysis["invalid_commits"]:
        print("\n  Invalid commits:")
        for c in analysis["invalid_commits"]:
            print(f"    {c['hash']} — {c['subject']}")
            for err in c["errors"]:
                print(f"      -> {err}")


def print_help():
    print("""
Git Workflow CLI (gitwf)

Usage: gitwf <command> [options]

Commands:
  status              Show repository status
  feature <name>      Create a feature branch
  bugfix <name>       Create a bugfix branch
  hotfix <name>       Create a hotfix branch
  pr-check [src] [tgt]  Validate PR readiness
  release start|finish  Manage releases
  changelog [from] [to] Generate CHANGELOG.md
  stats               Contributor and frequency stats
  diff <base> [head]  Diff summary with churn analysis
  cleanup [--dry-run] Delete merged branches
  hooks install|list  Manage git hooks
  validate [count]    Validate commit message conventions
""")


if __name__ == "__main__":
    main()
