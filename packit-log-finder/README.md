# Packit Log Finder Plugin

Claude Code plugin for analyzing Packit service logs to debug user-reported issues. The plugin currently requires to have CSV log file downloaded from our Splunk instance for the period when the event to investigate happened.

## Overview

When users report issues like "build didn't start", "status not updated", or "task failed", this plugin helps trace what happened by:

- Searching logs for relevant identifiers (repo, PR, status name)
- Aggregating entries by Celery task UUID
- Building a timeline of events and identifying failure points

## Usage

```
/packit-log-finder:find-packit-logs <LOG_FILE_PATH> <USER_QUERY>
```

Provide a path to a log file (CSV) from Splunk and describe the issue in plain language.

**Example:**

```
/packit-log-finder:find-packit-logs ./worker-logs.csv Status for rpm-build is pending but dashboard shows success for https://github.com/org/repo/pull/123
```
