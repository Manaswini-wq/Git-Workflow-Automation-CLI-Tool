# Git Workflow CLI (gitwf)

A Python CLI tool that automates Git workflow operations — branch management (Git Flow), conventional commit validation, PR readiness checks, changelog generation, and repository analytics.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                         CLI Layer                         │
│   gitwf status | feature | pr-check | release | stats    │
└──────────┬──────────────────────────────────┬────────────┘
           │                                  │
    ┌──────▼──────────┐              ┌────────▼──────────┐
    │  Workflow Layer  │              │  Analysis Layer   │
    │  PR Checks       │              │  Repo Stats       │
    │  Release Flow    │              │  Diff Analyzer    │
    │  Hook Manager    │              │  Changelog Gen    │
    └──────┬──────────┘              └────────┬──────────┘
           │                                  │
    ┌──────▼──────────────────────────────────▼──────────┐
    │                    Core Layer                       │
    │   GitOps (subprocess)  |  BranchManager  |  CommitAnalyzer  │
    └────────────────────────────────────────────────────┘
```

## Commands

```
gitwf status              # Repository overview
gitwf feature <name>      # Create feature/name from develop
gitwf bugfix <name>       # Create bugfix/name from develop
gitwf hotfix <name>       # Create hotfix/name from main
gitwf pr-check [src] [tgt]  # Validate branch for merge
gitwf release start|finish  # Semantic version release flow
gitwf changelog           # Generate CHANGELOG.md from commits
gitwf stats               # Contributor & frequency analysis
gitwf diff <base>         # Churn analysis between refs
gitwf cleanup [--dry-run] # Delete merged branches
gitwf hooks install       # Install pre-commit + commit-msg hooks
gitwf validate [count]    # Validate commit message conventions
```

## Quick Start

```bash
pip install -e .

# Check repo health
gitwf status

# Start a feature
gitwf feature user-auth

# Validate before merging
gitwf pr-check feature/user-auth develop

# Generate changelog
gitwf changelog

# Run tests
pytest tests/ -v
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Git Interface | subprocess (git CLI) |
| Config | YAML |
| Testing | pytest + real temp repos + mocks |
| Patterns | Facade (GitOps), Strategy (reporters), Builder (CLI) |
