---
description: Review downstream Fedora dist-git PRs created by Packit for its own projects.
---

## User Input

```text
$PACKAGE $VERSION $DIST_GIT_BRANCH
```

## Purpose

Packit project releases frequently its software into Fedora Linux. For every Fedora dist-git branch, 4 pull requests are being created:
1. Production packit using propose_downstream job.
2. Production packit using pull_from_upstream job.
3. Staging packit using propose_downstream job.
4. Staging packit using pull_from_upstream job.

We intend to merge the one from Staging Packit pull_from_upstream and close the other.

Review and analyze Fedora dist-git pull requests created by Packit automation. This command helps maintainers:
- Verify spec file changes are correct
- Check source archives and checksums
- Validate changelog entries
- Review automated updates from upstream
- Make informed merge/close decisions
- Ensure compliance with Fedora packaging guidelines

## Process

### 1. **Identify an update to Review**

Run the following command to see the details of 4 pull requests created by Packit and Packit Staging. The output includes title, description, file diff, and logs for all failed CI checks.
```bash
./packit-distgit-updater.py print-pr <PACKAGE> <VERSION> <DIST_GIT_BRANCH>
```
This command can take up to a minute to complete, be patient and wait at least one minute for it to complete.

### 2. **Review Spec File Changes**

#### Version and Release
- Version updated correctly (old → new)?
- Release set to `1%{?dist}` for new upstream version?
- Release bumped appropriately for rebuilds (if applicable)?

#### Changelog Entry
- Date format correct: `* DDD MMM DD YYYY`?
- Author/email correct: `Packit <hello@packit.dev>` or maintainer?
- Version-release matches spec header: `- X.Y.Z-R`?
- Changelog describes the actual changes accurately?
- **Bugzilla reference included** (for pull_from_upstream jobs): `Resolves: rhbz#NNNNNN`?
- Pull request reference included (if applicable): `(#NNNN)`?
- No typos or formatting issues?

#### Source and Patch Sections
- New sources or patches listed accurately in `%prep`, `%source`, and `%patch` sections?
- Source URLs correct and accessible?
- Patch numbers sequential and correct?
- Obsolete sources/patches removed if needed?
- Patch context makes sense for the update?

### 3. **Verify Sources File**

- Sources file updated with new tarball name?
- SHA512 checksum present and valid (non-zero)?
- Checksum format correct: `SHA512 (filename) = <hash>`?
- Old source entries removed (if applicable)?
- New source files match the intended upstream release?

### 4. **Check Build Dependencies**

- Review `BuildRequires` changes (if any):
  - New dependencies justified by upstream changes?
  - Removed dependencies no longer needed?
  - Version constraints appropriate?
- Review `Requires` changes (if any):
  - Runtime dependencies match new functionality?
  - No broken dependencies?
- `%check` or test sections adapted as needed for the new upstream?

### 5. **Verify Testing Plan Updates**

- `plans/main.fmf` (or similar) updated if present?
- Git ref matches upstream commit?
- Test URL points to correct repository?
- Test plan path correct?

### 6. **Verify Upstream References**

- Upstream tag/commit reference correct?
- Upstream tag exists at the referenced URL?
- Upstream commit hash matches the tag?
- Release monitoring project ID valid (if provided)?
- Packit created update from correct upstream repo/tag?
- Check for security advisories for this version

### 7. **Review CI Check Results**

- Review failed CI job logs (if accessible)
- Distinguish infrastructure failures from real packaging issues:
  - **Infrastructure failures** (usually OK to ignore):
    - Read-only filesystem errors (Koji)
    - Network timeouts
    - Service unavailability (Zuul, Testing Farm, Packit Service)
    - HTML error pages instead of logs
  - **Real issues** (must investigate):
    - Test failures
    - Build failures
    - Dependency resolution errors
    - Installation problems

### 8. **Fedora Packaging Guidelines Compliance**

- No hardcoded paths that should use macros?
- File permissions preserved unless intentionally changed?
- License field unchanged (or updated appropriately)?
- Summary and description still accurate?
- No commented-out code or merge conflict markers?
- Macros used correctly (`%{version}`, `%{name}`, etc.)?
- Paths, installation locations, and ownership correct and compliant?
- All new files tracked and unused files removed?

### 9. **Review Diff Quality**

- Diff minimal and focused only on version update?
- No unintended changes (odd context lines, spacing)?
- No unrelated "while we're here" changes?
- File permissions or modes unchanged unless needed?
- `.gitignore` updated with new tarball?
- `README.packit` or similar metadata files updated appropriately?

### 10. **Check All Related Pull Requests for Consistency** ⚠️ CRITICAL

**4 PRs should be created:**
- 1 from `packit` using `pull_from_upstream` workflow
- 1 from `packit-stg` using `pull_from_upstream` workflow
- 1 from `packit` using `propose_downstream` workflow
- 1 from `packit-stg` using `propose_downstream` workflow

**Verify PRs are identical in:**
- `packit.spec` content (especially changelog)
- `sources` file checksums
- `.gitignore` changes
- Test plan changes

**Common inconsistencies to report:**
- **Bugzilla resolution**: Some PRs may have `Resolves: rhbz#NNN` in changelog, others may not
- **PR descriptions**: Different workflows may have different descriptions
- **Generated files**: `README.packit` may show different Packit versions (minor, acceptable)

### 11. **Final Review Output**

Provide a structured review with:

#### ✅ Positive Findings
List all correct aspects of the update

#### ⚠️ Issues Found
List any problems, inconsistencies, or concerns with severity

#### 🚨 Red Flags (Stop and Investigate)
- Changelog missing or incorrect
- Multiple PRs with different spec file content
- Missing Bugzilla resolution when expected
- Source checksum missing or invalid
- BuildRequires/Requires changes without explanation
- Test failures in CI (not infrastructure issues)
- License changes without justification
- Security advisories for new version
- Suspicious file additions or code patterns

#### Next Steps
Propose a plan for which pull requests should be closed and the one that should be merged. You should select pull request created by packit-stg using the `pull_from_upstream` workflow to be merged.

### 12. **Merge and close pull requests**
Get confirmation from the user about your plan and then execute it.

Once the user approves your plan, you should merge the select pull request using the command below:
```bash
./packit-distgit-updater.py merge <PACKAGE> <PR_ID>
```
After the PR is merged, close the other pull requests with this command:
```bash
./packit-distgit-updater.py close <PACKAGE> <PR_ID>
```