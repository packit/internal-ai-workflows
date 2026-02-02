# Internal Packit AI Workflows

AI-powered workflows for Packit project maintenance tasks, integrated with Claude Code.

## Overview

This repository contains Claude Code plugins that automate various Packit project maintenance tasks. Each plugin is self-contained with its own documentation, dependencies, and installation instructions.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code) installed and configured (Follow Red Hat documentation for details)
- Python 3.8 or later

Once you fire up your Claude Code, you can enable this local repository as a marketplace:
```
/plugin marketplace add ./
```

You can then verify in `/plugin` that the plugin is enabled and can be used:
```
/plugin

 Plugins  Discover  [Installed]  Marketplaces  (←/→ or tab to cycle)

 packit-distgit-reviewer @ inline
 Scope: user
 Version: 0.1.0
 Review and merge Fedora dist-git PRs for Packit projects

 Author: Packit team
 Status: Enabled
```

It's honestly unclear to me how exactly this works, alternatively you can tell claude to load the plugin of your choice while launching it:
```
$ claude --plugin-dir ./packit-distgit-reviewer
```

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
