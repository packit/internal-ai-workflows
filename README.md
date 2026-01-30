# Internal Packit AI workflows

AI-powered workflows for Packit project maintenance tasks, integrated with Claude Code.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code) installed and configured
- Python 3.8 or later
- Fedora Account System (FAS) account with dist-git access
- Fedora dist-git API token

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Authentication

The tool supports two methods for providing your Fedora dist-git API token:

**Option 1: Use existing Packit configuration (Recommended)**

If you already have a `~/.config/packit.yaml` file with a Pagure token configured, the tool will automatically use it:

```yaml
authentication:
  pagure:
    token: YOUR_TOKEN_HERE
    instance_url: https://src.fedoraproject.org
```

**Option 2: Environment variable**

Alternatively, you can set the token as an environment variable:

```bash
export FEDORA_DISTGIT_TOKEN="your-token-here"
```

**Creating a new token:**

If you need to create a new Fedora dist-git API token:
1. Visit https://src.fedoraproject.org/settings/token/new
2. Create a new token with appropriate permissions
3. Use either Option 1 or Option 2 above to configure it

### 3. Verify Installation

```bash
# Test the helper script
./packit-distgit-updater.py --help
```

## Available Workflows

### `/review-fedora-distgit-prs` - Review Downstream Fedora PRs

Review and merge Fedora dist-git pull requests created by Packit automation for releases of our packages.

**Usage:**

```bash
$ claude
```

In the Claude Code session:

```
/review-fedora-distgit-prs <PACKAGE> <VERSION> <DIST_GIT_BRANCH>
```

**Example:**

```
/review-fedora-distgit-prs packit 1.11.1 f44
```

**What it does:**

1. Fetches 4 PRs created by Packit automation (prod/staging × propose_downstream/pull_from_upstream)
2. Analyzes spec file changes, sources, checksums, and CI results
3. Compares all PRs for consistency
4. Provides structured review with findings and recommendations
5. Guides you through merging the correct PR (staging pull_from_upstream) and closing others

**Supported packages:**
- `packit`
- `python-ogr`
- `python-specfile`

The command uses `packit-distgit-updater.py` script internally.
