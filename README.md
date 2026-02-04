# Internal Packit AI Workflows

AI-powered workflows for Packit project maintenance tasks, integrated with Claude Code.

## Overview

This repository contains Claude Code plugins that automate various Packit project maintenance tasks. Each plugin is self-contained with its own documentation, dependencies, and installation instructions.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code) installed and configured (Follow Red Hat documentation for details)
- Python 3.8 or later

## Usage

> **Note:** If you plan to develop or modify plugins, follow the [Development](#development) instructions instead.

Add this repository as a marketplace and install plugins:

```
/plugin marketplace add https://github.com/packit/internal-ai-workflows
/plugin install packit-log-finder@packit-internal-ai-workflows
/plugin install packit-distgit-reviewer@packit-internal-ai-workflows
```

Use `/plugin` to verify installed plugins.

## Development

If you intend to develop a plugin, install the marketplace from a local repository:

```
git clone https://github.com/packit/internal-ai-workflows.git
claude
# Run in Claude Code
/plugin marketplace add ./internal-ai-workflows
/plugin install <PLUGIN_NAME>@packit-internal-ai-workflows
```

> **Note:** If you previously added the remote marketplace, remove it first with `/plugin marketplace remove packit-internal-ai-workflows`.

## Available Plugins

### packit-distgit-reviewer

Review and merge Fedora dist-git pull requests created by Packit automation.

**Command:** `/review-fedora-distgit-prs`

**Quick Start:**

```bash
# Install plugin dependencies
cd packit-distgit-reviewer
pip install -r requirements.txt
```

**Usage:**

```
/packit-distgit-reviewer:review-fedora-distgit-prs packit 1.11.1 f42
```

**What it does:**
- Fetches and analyzes 4 PRs created by Packit automation
- Reviews spec file changes, sources, and checksums
- Monitors CI test results
- Provides structured review and recommendations
- Guides you through merging/closing PRs

**Documentation:** See [packit-distgit-reviewer/README.md](packit-distgit-reviewer/README.md) for detailed documentation.

### packit-log-finder

Analyze Packit service logs to debug user-reported issues by tracing Celery task UUIDs and building event timelines.

**Usage:**

```
/packit-log-finder:find-packit-logs ./worker-logs.csv Status is pending for https://github.com/org/repo/pull/123
```

**Documentation:** See [packit-log-finder/README.md](packit-log-finder/README.md) for details.
