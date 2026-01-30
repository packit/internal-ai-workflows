#!/usr/bin/python3
"""
Find dist-git updates of Packit projects and review them.
"""

import argparse
import os
import sys
import ogr
from ogr.abstract.status import CommitStatus, PRStatus
import requests
import warnings
import yaml
from pathlib import Path

# filter `from pydantic.v1.datetime_parse import (  # type: ignore # pyright: ignore[reportMissingImports] # Pydantic v2`
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality")
warnings.filterwarnings("ignore", module="pydantic")

fedora_distgit_url = "https://src.fedoraproject.org"

# Try to get token from environment variable first
token = os.getenv("FEDORA_DISTGIT_TOKEN")

# If not set, try to read from ~/.config/packit.yaml
if not token:
    packit_config_path = Path.home() / ".config" / "packit.yaml"
    if packit_config_path.exists():
        try:
            with open(packit_config_path, "r") as f:
                config = yaml.safe_load(f)
                token = config.get("authentication", {}).get("pagure", {}).get("token")
        except Exception as e:
            print(f"Warning: Failed to read token from {packit_config_path}: {e}", file=sys.stderr)

if not token:
    raise ValueError(
        "Fedora dist-git token not found. Please either:\n"
        "  1. Set FEDORA_DISTGIT_TOKEN environment variable, or\n"
        "  2. Configure token in ~/.config/packit.yaml under authentication.pagure.token"
    )

fedora_distgit_service = ogr.PagureService(token=token, instance_url=fedora_distgit_url)
allowed_projects = ["packit", "python-ogr", "python-specfile"]

def print_pr_info(pr):
    out = f"PR {pr.id}: {pr.title}, Source branch: {pr.source_branch}\n"
    out += f"Target branch: {pr.target_branch}\nDescription: {pr.description}\nFile diff: {pr.patch}\n"
    statuses = pr.get_statuses()
    for status in statuses:
        if status.state in [CommitStatus.error, CommitStatus.failure, CommitStatus.warning]:
            out += f"Failed CI job: {status.name}\n"
            # TODO: fix getting logs
            # logs_request = requests.get(status.url)
            # if logs_request.ok:
            #     out += f"Failed CI job logs:\n{logs_request.text}\n"
    print(out)


def do_print_pr_info(args):
    fedora_distgit_project = fedora_distgit_service.get_project(namespace="rpms", repo=args.package)
    prs = fedora_distgit_project.get_pr_list(status=PRStatus.open)
    # prs = [fedora_distgit_project.get_pr(x) for x in [1608, 1604, 1601, 1599]]  # packit
    found = False
    for pr in prs:
        if args.version in pr.title and args.dist_git_branch == pr.target_branch:
            print_pr_info(pr)
            found = True
    if not found:
        print(f"No open PRs found for {args.package} on {args.dist_git_branch}")

def do_close(args):
    fedora_distgit_project = fedora_distgit_service.get_project(namespace="rpms", repo=args.package)
    pr = fedora_distgit_project.get_pr(args.pr_id)
    pr.close()
    print(f"Closed PR {args.pr_id} for {args.package}")

def do_merge(args):
    fedora_distgit_project = fedora_distgit_service.get_project(namespace="rpms", repo=args.package)
    pr = fedora_distgit_project.get_pr(args.pr_id)
    pr.merge()
    print(f"Merged PR {args.pr_id} for {args.package}")

def cli():
    """
    Set up CLI interface
    """
    parser = argparse.ArgumentParser(
        description="Review, close, or merge Fedora dist-git PRs for Packit projects."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser(
        "print-pr",
        help="Print info for PRs that are opened for a given version and dist-git branch",
    )
    review_parser.add_argument("package", choices=allowed_projects, help="Package name to print info for")
    review_parser.add_argument("version", help="Version to review")
    review_parser.add_argument("dist_git_branch", help="Dist-git branch to filter PRs for")
    review_parser.set_defaults(func=do_print_pr_info)

    close_parser = subparsers.add_parser("close", help="Close matching dist-git PRs")
    close_parser.add_argument("package", choices=allowed_projects, help="Package name to close PRs for")
    close_parser.add_argument("pr_id", type=int, help="PR to close")
    close_parser.set_defaults(func=do_close)

    merge_parser = subparsers.add_parser("merge", help="Merge matching dist-git PRs")
    merge_parser.add_argument("package", choices=allowed_projects, help="Package name to merge PRs for")
    merge_parser.add_argument("pr_id", type=int, help="PR to merge")
    merge_parser.set_defaults(func=do_merge)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
        sys.exit(2)
    sys.exit(0)
