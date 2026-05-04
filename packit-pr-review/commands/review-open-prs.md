---
description: Review all open PRs across the packit GitHub org - categorise by status and generate action items
---

## Purpose

Review all open pull requests across the `packit` GitHub organisation.
Categorise each PR by its current status and generate concrete action items.

## Prerequisites

- `gh` CLI authenticated (`gh auth login`)

## Important

Do NOT write custom Python or bash scripts. Use only the provided tools below and present
the results directly.

## Process

### 1. Fetch data

Run the full pipeline in a single command. This fetches all PRs, members, and review status
(using batched GraphQL). Progress appears on stderr.

```bash
./packit-pr-review/scripts/pr-tools.py run 2>/dev/null
```

The output is a JSON object with:
- `total`: total number of open PRs
- `team_members`: list of org member logins
- `prs`: array of enriched PR objects, each with:
  - `ref`, `repo`, `repo_short`, `number`, `title`, `url`
  - `author`, `is_bot` (true if author login ends with `[bot]`), `author_type` (`team`/`external`)
  - `age_days`, `stale_days`, `is_draft`
  - `labels`, `review_decision`, `reviewers`, `changes_requested`, `waiting_for_author`

### 2. Triage and categorise

The script outputs ALL PRs without filtering. You must categorise them:

**Filter out these groups first (do NOT include them in the report at all):**

- **Bot/automated PRs**: PRs where `is_bot` is true, or the author is clearly a release bot
  or CI automation (e.g. release bots, renovation bots, `pre-commit-ci[bot]`,
  `dependabot[bot]`, `usercont-release-bot`). Exclude silently.
- **Test/playground repos**: Repos that only contain old test PRs, playground experiments,
  or are clearly not active projects (e.g. `hello-world`, `docker-py-source-git`,
  `testing_repo_changed_name`, `upsint`, or repos where all PRs are titled "[test]",
  "testing", "Test case:", etc.). Exclude silently.

**Then categorise the remaining human PRs into:**

1. **Approved - Ready to Merge**: `review_decision` is `APPROVED` and no blocking labels
   (`do-not-merge`, `blocked`, `discuss`)
2. **Approved - Blocked**: `review_decision` is `APPROVED` but has blocking labels, OR has
   `discuss` label regardless of review status
3. **Waiting for Author**: `waiting_for_author` is true. This field is timing-aware: it is
   true when a human reviewer's *latest* review is CHANGES_REQUESTED or COMMENTED AND the
   author has NOT pushed new commits since that review. If the author has already pushed
   after the last review, the PR is back in the reviewers' court and belongs in "Waiting
   for Review". **Note:** this flag is a heuristic. If `review_decision` is `APPROVED`,
   the PR should be categorised as Approved regardless of the flag value.
4. **Waiting for Review**: `waiting_for_author` is false and no approval yet
5. **Draft / WIP / Blocked**: `is_draft` is true, title contains "WIP" or "DO NOT MERGE",
   or has `do-not-merge`/`blocked` labels

**Use your judgment for edge cases.** The script's `waiting_for_author` and
`changes_requested` fields are heuristics based on review timing. When the data seems
contradictory (e.g. a PR is APPROVED but `waiting_for_author` is true, or the title/context
suggests a different status), trust the higher-signal fields (`review_decision`, `is_draft`,
labels) over the timing heuristics, and note any ambiguity in the report.

### 3. Present results

Present as a structured report with:

1. **Quick stats**: total PRs (after filtering), count per category, stale count (>30d)
2. **Approved - Ready to Merge** — two sub-tables: *External contributors* then *Team*, each sorted by most recently updated first
3. **Approved - Blocked** table if any exist, sorted by most recently updated first
4. **Waiting for Review** — two sub-tables: *External contributors* then *Team*, each sorted by most recently updated first
5. **Waiting for Author** — two sub-tables: *External contributors* then *Team*, each sorted by most recently updated first, flag changes_requested PRs
6. **Draft / WIP / Blocked** table, sorted by most recently updated first

All tables must be sorted by most recently updated first (lowest `stale_days` at top).

Every PR in every table must include a clickable link to the PR (use the `url` field).

Use staleness labels: Fresh (<=7d), Aging (7-30d), Stale (30-90d), Very stale (>90d).

### 4. Generate action items

At the end, produce a numbered checklist:

1. Merge approved fresh PRs (<=30d since last update)
2. Rebase/verify CI on older approved PRs, then merge
3. Review PRs - external contributors first, then team, oldest first
4. Ping authors who haven't responded in >7 days
5. Consider closing very stale PRs (>90d without updates)
6. Bring blocked/discuss PRs to team discussion

### 5. Slack-ready summary

After the full report, produce a concise copy-pasteable message for Slack (or similar).
Use this exact format — plain text with URLs, no markdown tables:

```
Ready to merge (just click the button):
- <url> -- <title> (<author>)
- <url> -- <title> (<author>, needs rebase - <N>d stale)

Reviews needed -- external contributors waiting on us:
- <url> -- <title> (<author>, <stale_days>d)

Reviews needed -- team:
- <url> -- <title> (<author>, <stale_days>d)
```

Rules:
- **Ready to merge**: all "Approved - Ready to Merge" PRs. If `stale_days` > 30, append
  `needs rebase - <N>d stale` in parentheses. Mark external contributors with `, external`.
- **Reviews needed -- external contributors**: all "Waiting for Review" PRs from external
  contributors, sorted by `stale_days` ascending. Only include PRs with `stale_days` <= 90
  (skip very stale ones — those belong in a close-or-revive discussion, not a review ask).
  Show `stale_days` in parentheses.
- **Reviews needed -- team**: same, but for team PRs with `stale_days` <= 90.
- Omit sections that would be empty.
- Do NOT include Waiting for Author, Draft, or Blocked PRs — those are tracked in the full
  report but not actionable as a team ping.
- Keep it concise: no header decorations, no staleness labels, just the URL/title/author/days.

### 6. Notes

- Do NOT merge, close, or modify any PRs. This command is read-only.
- If `gh` commands fail due to auth, inform the user and suggest `gh auth login`.
- If rate-limited, wait briefly and retry.

## Advanced: individual subcommands

The script also supports individual subcommands if you need step-by-step control:

```bash
# Fetch all open PRs (JSON)
./packit-pr-review/scripts/pr-tools.py fetch-prs > prs.json

# Fetch org member logins (one per line)
./packit-pr-review/scripts/pr-tools.py fetch-members > members.txt

# Fetch review status using batched GraphQL (JSON object keyed by ref)
./packit-pr-review/scripts/pr-tools.py fetch-reviews --from-file refs.txt > reviews.json
```
