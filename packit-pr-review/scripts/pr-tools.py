#!/usr/bin/env python3
"""
CLI tools for reviewing open PRs across the packit GitHub org.

Requires: gh CLI authenticated with read:org and repo scopes.
No pip dependencies.

Subcommands:
    run                             Full pipeline: fetch, review, enrich (JSON)
    fetch-prs                       Fetch all open PRs (JSON)
    fetch-members                   Fetch org members (one login per line)
    fetch-reviews [refs...]         Fetch review status for given PRs (JSON)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone


def gh(*args, parse_json=True):
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"gh error: {result.stderr.strip()}", file=sys.stderr)
        return [] if parse_json else ""
    if parse_json:
        return json.loads(result.stdout)
    return result.stdout.strip()


def fetch_reviews_graphql(pr_refs):
    """Fetch review info for PRs using batched GraphQL queries.

    Batches up to 25 PRs per query to minimize API calls.
    Returns a dict keyed by ref with reviewDecision, reviews, isDraft, labels.
    """
    results = {}
    batch_size = 25
    total = len(pr_refs)

    for batch_start in range(0, total, batch_size):
        batch = pr_refs[batch_start:batch_start + batch_size]
        query_parts = []
        ref_map = {}

        for i, ref in enumerate(batch):
            if "#" not in ref:
                continue
            repo, number = ref.rsplit("#", 1)
            owner, name = repo.split("/", 1)
            alias = f"pr_{i}"
            ref_map[alias] = ref
            query_parts.append(f"""
                {alias}: repository(owner: "{owner}", name: "{name}") {{
                    pullRequest(number: {number}) {{
                        reviewDecision
                        isDraft
                        labels(first: 20) {{ nodes {{ name }} }}
                        reviews(first: 30) {{
                            nodes {{
                                state
                                author {{ login }}
                                submittedAt
                            }}
                        }}
                        commits(last: 1) {{
                            nodes {{
                                commit {{
                                    committedDate
                                }}
                            }}
                        }}
                    }}
                }}
            """)

        if not query_parts:
            continue

        query = "query { " + "\n".join(query_parts) + " }"
        result = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            print(f"GraphQL batch error: {result.stderr.strip()}", file=sys.stderr)
            for ref in batch:
                results[ref] = _fetch_review_single(ref)
            continue

        data = json.loads(result.stdout).get("data", {})
        for alias, ref in ref_map.items():
            repo_data = data.get(alias, {})
            pr_data = repo_data.get("pullRequest") if repo_data else None
            if not pr_data:
                results[ref] = {
                    "reviewDecision": "", "reviews": [],
                    "isDraft": False, "labels": [],
                }
                continue

            reviews = [
                {
                    "state": r["state"],
                    "author": {"login": r["author"]["login"]},
                    "submittedAt": r.get("submittedAt", ""),
                }
                for r in (pr_data.get("reviews", {}).get("nodes") or [])
                if r.get("author")
            ]
            labels = [
                {"name": l["name"]}
                for l in (pr_data.get("labels", {}).get("nodes") or [])
            ]
            commits_nodes = (
                pr_data.get("commits", {}).get("nodes") or []
            )
            last_commit_date = ""
            if commits_nodes:
                last_commit_date = (
                    commits_nodes[-1].get("commit", {}).get("committedDate", "")
                )
            results[ref] = {
                "reviewDecision": pr_data.get("reviewDecision") or "",
                "reviews": reviews,
                "isDraft": pr_data.get("isDraft", False),
                "labels": labels,
                "lastCommitDate": last_commit_date,
            }

        done = min(batch_start + batch_size, total)
        print(f"  Reviews: {done}/{total}", file=sys.stderr)

    return results


def _fetch_review_single(ref):
    """Fallback: fetch review for a single PR via gh CLI."""
    if "#" not in ref:
        return {"reviewDecision": "", "reviews": [], "isDraft": False, "labels": []}
    repo, number = ref.rsplit("#", 1)
    data = gh(
        "pr", "view", number, "--repo", repo,
        "--json", "reviewDecision,reviews,isDraft,labels",
    )
    return data or {
        "reviewDecision": "", "reviews": [], "isDraft": False, "labels": [],
    }


def _enrich_pr(pr, reviews, team, now):
    """Build an enriched PR entry with review data and computed fields."""
    repo_full = pr["repository"]["nameWithOwner"]
    author = pr["author"]["login"]
    ref = f"{repo_full}#{pr['number']}"

    rv = reviews.get(ref, {
        "reviewDecision": "", "reviews": [], "isDraft": False, "labels": [],
        "lastCommitDate": "",
    })

    created = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
    updated = datetime.fromisoformat(pr["updatedAt"].replace("Z", "+00:00"))

    is_draft = pr["isDraft"] or rv.get("isDraft", False)

    labels = set(l["name"] for l in pr.get("labels", []))
    for l in rv.get("labels", []):
        labels.add(l["name"] if isinstance(l, dict) else l)

    decision = rv.get("reviewDecision", "")

    # Filter out bot reviewers (accounts with [bot] suffix or known bots)
    BOT_REVIEWERS = {"gemini-code-assist"}
    human_non_author = [
        r for r in rv.get("reviews", [])
        if not r.get("author", {}).get("login", "").endswith("[bot]")
        and r.get("author", {}).get("login", "") not in BOT_REVIEWERS
        and r.get("author", {}).get("login", "") != author
    ]
    reviewers = sorted(set(
        r["author"]["login"] for r in human_non_author
    ))

    # Determine if the author has pushed commits after the last actionable
    # review (CHANGES_REQUESTED or COMMENTED from a human non-author).
    # If so, the ball is back with reviewers, not the author.
    #
    # Key: only consider each reviewer's LATEST review state. If a reviewer
    # left comments but then approved, their earlier comments don't count
    # as outstanding. This avoids false positives where a reviewer's
    # approval is the resolution of their own earlier comments.
    last_commit_date = rv.get("lastCommitDate", "")

    # Build latest review state per reviewer
    latest_by_reviewer = {}
    for r in human_non_author:
        login = r.get("author", {}).get("login", "")
        submitted = r.get("submittedAt", "")
        if not login or not submitted:
            continue
        prev = latest_by_reviewer.get(login)
        if prev is None or submitted > prev["submittedAt"]:
            latest_by_reviewer[login] = r

    # Only count reviews where the reviewer's LATEST state is still
    # CHANGES_REQUESTED or COMMENTED (i.e. they haven't approved since)
    actionable_reviews = [
        r for r in latest_by_reviewer.values()
        if r.get("state") in ("CHANGES_REQUESTED", "COMMENTED")
    ]
    has_changes_requested = any(
        r.get("state") == "CHANGES_REQUESTED" for r in actionable_reviews
    )
    last_review_date = ""
    if actionable_reviews:
        last_review_date = max(r["submittedAt"] for r in actionable_reviews)

    # True when there are actionable reviews but the author has since pushed
    # new commits, meaning the PR is back in the reviewers' court.
    author_responded = False
    if last_review_date and last_commit_date:
        author_responded = last_commit_date > last_review_date

    # waiting_for_author is true only when changes were requested (or review
    # comments were left) AND the author has NOT pushed since that review.
    # If GitHub's reviewDecision is already APPROVED, the PR is approved
    # regardless — reviewers are satisfied.
    waiting_for_author = (
        decision != "APPROVED"
        and (has_changes_requested or bool(actionable_reviews))
        and not author_responded
    )

    return {
        "ref": ref,
        "repo": repo_full,
        "repo_short": pr["repository"]["name"],
        "number": pr["number"],
        "title": pr["title"],
        "url": pr["url"],
        "author": author,
        "is_bot": author.endswith("[bot]"),
        "author_type": "team" if author in team else "external",
        "age_days": (now - created).days,
        "stale_days": (now - updated).days,
        "is_draft": is_draft,
        "labels": sorted(labels),
        "review_decision": decision,
        "reviewers": reviewers,
        "changes_requested": has_changes_requested,
        "waiting_for_author": waiting_for_author,
    }


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_run():
    """Full pipeline: fetch PRs + members, fetch reviews, enrich all.

    Outputs JSON with all PRs enriched with review data.
    No filtering — the LLM decides what to skip/categorise.
    """
    print("Fetching open PRs...", file=sys.stderr)
    prs = gh(
        "search", "prs", "--owner", "packit", "--state", "open",
        "--json", "repository,title,url,author,createdAt,updatedAt,"
                  "isDraft,commentsCount,labels,number",
        "--limit", "500",
    )
    print(f"Fetched {len(prs)} PRs", file=sys.stderr)

    print("Fetching org members...", file=sys.stderr)
    raw = gh("api", "orgs/packit/members", "--jq", ".[].login", parse_json=False)
    team = set(line.strip() for line in raw.splitlines() if line.strip())
    print(f"Found {len(team)} team members", file=sys.stderr)

    refs = [
        f"{pr['repository']['nameWithOwner']}#{pr['number']}"
        for pr in prs
    ]

    print(f"Fetching reviews for {len(refs)} PRs...", file=sys.stderr)
    reviews = fetch_reviews_graphql(refs)

    now = datetime.now(timezone.utc)
    enriched = [_enrich_pr(pr, reviews, team, now) for pr in prs]

    output = {
        "generated_at": now.isoformat(),
        "total": len(enriched),
        "team_members": sorted(team),
        "prs": enriched,
    }

    json.dump(output, sys.stdout, indent=2)
    print()


def cmd_fetch_prs():
    """Fetch all open PRs across the packit org. Outputs JSON array to stdout."""
    prs = gh(
        "search", "prs", "--owner", "packit", "--state", "open",
        "--json", "repository,title,url,author,createdAt,updatedAt,"
                  "isDraft,commentsCount,labels,number",
        "--limit", "500",
    )
    print(f"Fetched {len(prs)} PRs", file=sys.stderr)
    json.dump(prs, sys.stdout, indent=2)
    print()


def cmd_fetch_members():
    """Fetch packit org members. Outputs one login per line to stdout."""
    raw = gh("api", "orgs/packit/members", "--jq", ".[].login", parse_json=False)
    if raw:
        print(raw)


def cmd_fetch_reviews(pr_refs):
    """Fetch review status for PRs using batched GraphQL."""
    results = fetch_reviews_graphql(pr_refs)
    json.dump(results, sys.stdout, indent=2)
    print()


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

COMMANDS = {
    "run": "Full pipeline: fetch, review, enrich all PRs (JSON output)",
    "fetch-prs": "Fetch all open PRs across the packit org (JSON)",
    "fetch-members": "Fetch packit org member logins (one per line)",
    "fetch-reviews": "Fetch review status. Args: [--from-file <file>] [OWNER/REPO#NUM ...]",
}

if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
    print("Usage: pr-tools.py <command> [args...]")
    print()
    for name, desc in COMMANDS.items():
        print(f"  {name:20s} {desc}")
    sys.exit(1)

cmd = sys.argv[1]

if cmd == "run":
    cmd_run()

elif cmd == "fetch-prs":
    cmd_fetch_prs()

elif cmd == "fetch-members":
    cmd_fetch_members()

elif cmd == "fetch-reviews":
    refs = []
    args = sys.argv[2:]
    if args and args[0] == "--from-file":
        if len(args) < 2:
            print("Usage: pr-tools.py fetch-reviews --from-file <refs.txt>", file=sys.stderr)
            sys.exit(1)
        with open(args[1]) as f:
            refs = [line.strip() for line in f if line.strip()]
    else:
        refs = args
    if not refs:
        print("No PR refs provided.", file=sys.stderr)
        sys.exit(1)
    cmd_fetch_reviews(refs)
