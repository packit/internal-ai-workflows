# Packit PR Review Plugin

Review all open pull requests across the `packit` GitHub organisation.

## Overview

This plugin categorises all open PRs by their review status and generates concrete action items for PR triage.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth login`)

## Usage

```
/packit-pr-review:review-open-prs
```

### What it does

1. Fetches all open PRs across the `packit` GitHub org
2. Fetches review status using batched GraphQL
3. Separates bot/automated PRs and test/playground repos
4. Categorises remaining human PRs into:
   - **Approved - Ready to Merge**
   - **Approved - Blocked** (blocking labels or `discuss`)
   - **Waiting for Author** (changes requested or review comments to address)
   - **Waiting for Review**
   - **Draft / WIP / Blocked**
5. Flags stale PRs (>30 days without activity)
6. Generates a prioritised action items checklist

This command is **read-only** — it does not merge, close, or modify any PRs.

## Helper Script

The plugin uses `scripts/pr-tools.py` for data fetching. You can also use it directly:

```bash
# Full pipeline: fetch PRs, members, reviews, enrich (JSON)
./scripts/pr-tools.py run

# Fetch all open PRs (JSON)
./scripts/pr-tools.py fetch-prs > prs.json

# Fetch org member logins (one per line)
./scripts/pr-tools.py fetch-members > members.txt

# Fetch review status for specific PRs (from args or file)
./scripts/pr-tools.py fetch-reviews packit/ogr#981 packit/packit-service#3039
./scripts/pr-tools.py fetch-reviews --from-file refs.txt > reviews.json
```

## Directory Structure

```
packit-pr-review/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── review-open-prs.md    # Claude Code command definition
├── scripts/
│   └── pr-tools.py           # Data fetching CLI
└── README.md
```
