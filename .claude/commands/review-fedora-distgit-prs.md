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

Run the following command to see the details of 4 pull requests created by Packit and Packit Staging. The output includes title, description, CI test status, file diff, and logs for all failed CI checks.
```bash
./packit-distgit-updater.py print-pr <PACKAGE> <VERSION> <DIST_GIT_BRANCH>
```
This command can take up to a minute to complete, be patient and wait at least one minute for it to complete.

**CI Test Status Indicators:**
- ✅ = Test PASSED
- ❌ = Test FAILED or ERROR
- ⏳ = Test PENDING
- 🔄 = Test RUNNING
- ⚠️ = Test WARNING
- ❓ = Unknown status

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

### 7. **Fedora Packaging Guidelines Compliance**

- No hardcoded paths that should use macros?
- File permissions preserved unless intentionally changed?
- License field unchanged (or updated appropriately)?
- Summary and description still accurate?
- No commented-out code or merge conflict markers?
- Macros used correctly (`%{version}`, `%{name}`, etc.)?
- Paths, installation locations, and ownership correct and compliant?
- All new files tracked and unused files removed?

### 8. **Review Diff Quality**

- Diff minimal and focused only on version update?
- No unintended changes (odd context lines, spacing)?
- No unrelated "while we're here" changes?
- File permissions or modes unchanged unless needed?
- `.gitignore` updated with new tarball?
- `README.packit` or similar metadata files updated appropriately?

### 9. **Check All Related Pull Requests for Consistency** ⚠️ CRITICAL

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

### 10. **Monitor CI Tests and Review Results**

**CRITICAL**: Do NOT proceed with final review recommendations (step 11) until ALL required CI tests are complete.

#### Step 10.1: Identify Required CI Tests

Analyze the "CI Test Status" section from the PR output in step 1. Each PR will show tests with status indicators:
- ✅ = Test PASSED
- ❌ = Test FAILED or ERROR
- ⏳ = Test PENDING (not yet started)
- 🔄 = Test RUNNING (in progress)
- ⚠️ = Test WARNING

**Common required tests for Fedora dist-git PRs:**
- Koji build test
- fedora-ci tests (various architectures and Fedora versions like f40, f41, rawhide)
- Packit build tests
- RPM build validation
- Testing Farm tests

Count all tests shown for each PR and track their completion status.

#### Step 10.2: Check CI Test Completion Status

Parse the "CI Test Status" section from the print-pr output for each of the 4 PRs and categorize tests:

**Completed tests** (can proceed with review):
- ✅ PASSED tests
- ❌ FAILED/ERROR tests (completed, but failed)

**Incomplete tests** (must wait):
- ⏳ PENDING tests (not yet started)
- 🔄 RUNNING tests (in progress)

If the "CI Test Status" section shows "No tests found or not yet started", all tests are incomplete.

#### Step 10.3: Wait for Tests if Incomplete

**If ANY required CI tests are incomplete** (pending, running, or not yet started):

1. **Inform the user** with a detailed status report:
   ```
   CI tests are not complete yet. Waiting for tests to finish before proceeding with final review...

   Current status for PR #XXX (packit-stg/pull_from_upstream):
   - ✅ Koji build: PASSED
   - ⏳ fedora-ci (f40-x86_64): RUNNING
   - ⏳ fedora-ci (f41-x86_64): PENDING
   - ❌ fedora-ci (rawhide-x86_64): Not started

   Current status for PR #YYY (packit/pull_from_upstream):
   - ✅ Koji build: PASSED
   - ⏳ fedora-ci (f40-x86_64): RUNNING
   ...

   Will check again in 60 seconds...
   ```

2. **Enter monitoring loop**:
   - Wait 60 seconds
   - Re-run `./packit-distgit-updater.py print-pr <PACKAGE> <VERSION> <DIST_GIT_BRANCH>`
   - Parse the new output for updated test status
   - Provide updated status to user showing:
     - Which tests completed since last check
     - Which tests are still pending/running
     - Current timestamp
   - Repeat until ALL required tests are complete (passed or failed)

3. **Status update format** (every 60 seconds):
   ```
   [HH:MM:SS] Still waiting for CI tests...

   Updates since last check:
   - PR #XXX: fedora-ci (f40-x86_64) completed: PASSED ✅

   Still waiting for:
   - PR #XXX: fedora-ci (f41-x86_64) - RUNNING ⏳
   - PR #XXX: fedora-ci (rawhide-x86_64) - PENDING ⏳
   - PR #YYY: fedora-ci (rawhide-x86_64) - PENDING ⏳

   Will check again in 60 seconds...
   ```

4. **Continue monitoring** until one of these conditions:
   - All required CI tests complete (proceed to step 10.4)
   - User explicitly interrupts and requests to proceed without waiting
   - Tests have been pending for >30 minutes without progress (ask user if they want to continue waiting or proceed with available results)

**If all required CI tests are already complete**: Proceed directly to step 10.4.

#### Step 10.4: Review CI Test Results

Once all tests are complete, analyze the results:

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