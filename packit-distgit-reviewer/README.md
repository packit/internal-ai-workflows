# Packit Dist-Git Reviewer Plugin

Claude Code plugin for reviewing and merging Fedora dist-git pull requests created by Packit automation.

## Overview

This plugin helps Packit maintainers review downstream Fedora dist-git PRs created during the release process. For each Fedora dist-git branch, Packit creates 4 pull requests:
1. Production Packit using `propose_downstream` job
2. Production Packit using `pull_from_upstream` job
3. Staging Packit using `propose_downstream` job
4. Staging Packit using `pull_from_upstream` job

The plugin analyzes all 4 PRs, compares them for consistency, reviews spec file changes, validates CI test results, and guides you through merging the correct PR (typically staging `pull_from_upstream`) and closing the others.

## Installation

### 1. Install Dependencies

From the plugin directory:

```bash
cd packit-distgit-reviewer
pip install -r requirements.txt
```

### 2. Set Up Authentication

The plugin requires a Fedora dist-git API token. Two configuration methods are supported:

**Option 1: Use existing Packit configuration (Recommended)**

If you have `~/.config/packit.yaml` with a Pagure token, it will be automatically used:

```yaml
authentication:
  pagure:
    token: YOUR_TOKEN_HERE
    instance_url: https://src.fedoraproject.org
```

**Option 2: Environment variable**

```bash
export FEDORA_DISTGIT_TOKEN="your-token-here"
```

**Creating a new token:**

1. Visit https://src.fedoraproject.org/settings/token/new
2. Create a token with appropriate permissions
3. Configure using Option 1 or Option 2 above

### 3. Enable the Plugin

The plugin is automatically available in Claude Code once the symlink is created in the root `.claude/commands/` directory.

## Usage

### Command: `/review-fedora-distgit-prs`

Review and merge Fedora dist-git PRs for a specific package, version, and branch.

**Syntax:**

```
/packit-distgit-reviewer:review-fedora-distgit-prs <PACKAGE> <VERSION> <DIST_GIT_BRANCH>
```

**Example:**

```
/packit-distgit-reviewer:review-fedora-distgit-prs packit 1.11.1 f42
```

**Supported packages:**
- `packit`
- `python-ogr`
- `python-specfile`

### What the Command Does

1. **Fetches PR information** - Retrieves all 4 PRs created for the specified version and branch
2. **Analyzes changes** - Reviews spec file updates, source checksums, changelog entries
3. **Monitors CI tests** - Waits for all CI tests to complete and analyzes results
4. **Compares PRs** - Validates consistency across all 4 PRs
5. **Provides recommendations** - Suggests which PR to merge and which to close
6. **Executes actions** - Merges and closes PRs after user confirmation

### Review Checklist

The plugin performs comprehensive checks including:

- Version and release number updates
- Changelog format and content
- Source file checksums
- Testing plan updates
- Upstream reference validation
- Fedora packaging guidelines compliance
- CI test status and results
- PR consistency across all 4 PRs

## Helper Script

The plugin uses `scripts/packit-distgit-updater.py` to interact with Fedora dist-git. You can also use it directly:

**Print PR information:**
```bash
./scripts/packit-distgit-updater.py print-pr <PACKAGE> <VERSION> <DIST_GIT_BRANCH>
```

**Merge a PR:**
```bash
./scripts/packit-distgit-updater.py merge <PACKAGE> <PR_ID>
```

**Close a PR:**
```bash
./scripts/packit-distgit-updater.py close <PACKAGE> <PR_ID>
```

## Known Issues

The workflow waits for all CI checks to complete. Currently, some Fedora CI checks (rpmlint, rpminspect) may show as pending even when finished due to a status sync issue.

**Workaround:** Inspect the checks manually and tell Claude to proceed:

```
Ignore the pending CI results, they are complete and passed but statuses were not properly synced. Proceed with rest of the steps.
```

## Directory Structure

```
packit-distgit-reviewer/
├── .claude/
│   └── commands/
│       └── review-fedora-distgit-prs.md   # Claude Code command definition
├── scripts/
│   └── packit-distgit-updater.py          # Python helper script
├── requirements.txt                       # Plugin dependencies
├── plugin.yaml                            # Plugin metadata
└── README.md                              # This file
```

## Contributing

This plugin is part of the Packit internal AI workflows repository. For issues or contributions, please refer to the main repository documentation.

## License

See the main repository for license information.
