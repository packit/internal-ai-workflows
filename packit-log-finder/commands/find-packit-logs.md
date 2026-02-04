---
description: Find and analyze Packit service logs for a specific event reported by users
---

## User Input

```text
$LOG_FILE_PATH $USER_QUERY
```

## Purpose

Help debug Packit service issues by analyzing Celery worker logs. Uses grep-based analysis with **task UUID aggregation** to trace what happened.

## Log Format

Celery worker logs follow this format:
```
[TIMESTAMP: LEVEL/PROCESS] TaskName.task_type[TASK_UUID] message
```

Example:
```
[2026-02-02 15:58:08,964: DEBUG/ForkPoolWorker-2] TaskName.downstream_koji_build[e785ec96-09ea-4675-86f1-fdc00199d182] Cloning repo...
```

## Common Issue Types

### Type 1: Task Not Triggered
User says: "Nothing happened" / "Build didn't start" / "Retrigger didn't work"

**Investigation flow:**
1. Was the event received? → Search for repo/PR in `process_message` logs
2. Did a handler match? → Look for `Got signature for handler`
3. Was a task dispatched? → Look for `Task.*received`

### Type 2: External Update Not Sent
User says: "Status is pending" / "Dashboard updated but PR not" / "Callback not received"

**Investigation flow:**
1. Find the task that should have sent the update
2. Check if task completed successfully
3. Look for external API calls (status updates, webhooks, callbacks)
4. Check for API errors (rate limits, auth failures, network issues)

### Type 3: Task Failed
User says: "Build failed" / "Got an error" / "Task crashed"

**Investigation flow:**
1. Find the task by repo/PR/identifier
2. Get all logs for the task UUID
3. Search for ERROR, stderr, raise, exception patterns
4. Identify the root cause

## Process

### 1. Parse the User Query

Extract identifiers:
- **URLs:** PR/MR URLs, build URLs, artifact URLs
- **Identifiers:** PR numbers, build IDs, commit SHAs
- **Names:** Repository name, package name, project name
- **Status/Check names:** The specific check that's problematic
- **Time references:** When the issue occurred
- **Keywords:** What type of operation failed

### 2. Find Initial Matches

Search for entries matching the extracted identifiers:

```
# By repository/project name
Grep pattern="my-repo-name" path="$LOG_FILE" output_mode="content" head_limit=100

# By PR/MR number
Grep pattern="_pr_id.*123|pull-request/123|pull/123|merge_requests/123" path="$LOG_FILE" output_mode="content"

# By specific identifier or status name
Grep pattern="my-status-name|my-build-id" path="$LOG_FILE" output_mode="content"
```

### 3. Extract Task UUIDs

From matches, identify Celery task UUIDs (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`):

Look for:
- `TaskName.task_type[UUID]` - In log prefix
- `task_uuid: UUID` - In message body
- `root_id.*UUID` - Parent task reference
- `id.*UUID` - Task ID in JSON

### 4. Aggregate Logs by Task

For each task UUID, get ALL related entries:

```
Grep pattern="e785ec96-09ea-4675-86f1-fdc00199d182" path="$LOG_FILE" output_mode="content"
```

### 5. Analyze Task Outcome

**Task lifecycle patterns:**

| Pattern | Meaning |
|---------|---------|
| `Task.*received` | Worker picked up task |
| `Task.*succeeded` | Task completed successfully |
| `Task.*failed` | Task failed with exception |
| `Task.*retry` | Task will be retried |
| `ERROR` | Error occurred during execution |
| `Job finished` | Cleanup completed |

**External call patterns:**

| Pattern | Meaning |
|---------|---------|
| `Setting.*status` | Status update attempted |
| `API.*call\|request\|response` | External API interaction |
| `webhook\|callback` | Outgoing notification |
| `POST\|PUT\|PATCH` | HTTP method used |

**Error patterns:**

| Pattern | Meaning |
|---------|---------|
| `ERROR\|Exception\|Traceback` | Error occurred |
| `stderr:` | Command stderr output |
| `failed\|failure` | Operation failed |
| `rate.limit\|429` | Rate limited |
| `403\|401\|Forbidden\|Unauthorized` | Auth/permission error |
| `timeout\|timed out` | Operation timed out |
| `connection.*error\|refused` | Network error |

### 6. Identify Task Context

Look for contextual information:

| Pattern | Information |
|---------|-------------|
| `TaskName.<type>` | Task type in log prefix |
| `handler.*Handler` | Handler class processing event |
| `branch\|target` | Target branch/environment |
| `identifier:` | Job/package identifier |
| `Command:` | External command executed |

### 7. Build Timeline

Sort events chronologically:

1. **Event received** - `process_message`, webhook received
2. **Handler matched** - `Got signature for handler`, handler selected
3. **Task dispatched** - `Task.*received`, worker picked up
4. **Execution** - Main task logic
5. **External calls** - API calls, status updates
6. **Outcome** - `succeeded`, `failed`, `ERROR`

## Example Grep Commands

```
# Step 1: Find entries for a project
Grep pattern="my-project" path="/path/to/logs.csv" output_mode="content" head_limit=50

# Step 2: Find specific task type
Grep pattern="copr_build.*my-project" path="/path/to/logs.csv" output_mode="content"

# Step 3: Get all logs for a task UUID
Grep pattern="e785ec96-09ea-4675-86f1-fdc00199d182" path="/path/to/logs.csv" output_mode="content"

# Step 4: Find errors for a task
Grep pattern="e785ec96.*(ERROR|Failed|stderr|Exception)" path="/path/to/logs.csv" output_mode="content"

# Step 5: Find external API calls
Grep pattern="e785ec96.*(status|API|POST|webhook)" path="/path/to/logs.csv" output_mode="content"

# Step 6: Find outcome
Grep pattern="e785ec96.*(succeeded|failed|retry)" path="/path/to/logs.csv" output_mode="content"
```

## Analysis Output Format

### Summary Table

```
| Task UUID (short) | Type         | Target    | Outcome | External Update |
|-------------------|--------------|-----------|---------|-----------------|
| e785ec96...       | build_end    | target-1  | SUCCESS | Yes             |
| e7a19159...       | build_end    | target-2  | SUCCESS | ERROR (403)     |
| a1b2c3d4...       | test_results | target-1  | FAILED  | N/A             |
```

### Timeline

```
1. [15:57:38] Event received: webhook payload
2. [15:57:39] Handler matched: BuildEndHandler
3. [15:57:47] Task dispatched: e785ec96...
4. [15:57:54] Task completed successfully
5. [15:57:55] Status update → ERROR: 403 Forbidden
```

### Root Cause

Explain what happened vs what user expected:
- Did the task run? (Yes/No/Partially)
- Did it complete successfully? (Yes/No - with error details)
- Were external updates sent? (Yes/No/Failed)
- What was the failure point?

### Recommendations

Specific next steps based on findings.

## Reference

For Packit-specific task and handler definitions, see:
- **Tasks:** https://github.com/packit/packit-service/blob/main/packit_service/worker/tasks.py
- **Handlers:** https://github.com/packit/packit-service/tree/main/packit_service/worker/handlers/
- **Reporting:** https://github.com/packit/packit-service/tree/main/packit_service/worker/reporting/

Use WebFetch to get current implementations when investigating unfamiliar task types.

ARGUMENTS: $LOG_FILE_PATH $USER_QUERY
