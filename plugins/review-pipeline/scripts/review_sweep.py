#!/usr/bin/env python3
"""
Review sweep: find and track unreviewed PRs for automated code review.

Subcommands:
  query   — Find reviewable PRs (filters merge-backs, already-reviewed)
  mark    — Record a completed review
  status  — Show current sweep state
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Type alias for the nested state structure:
# {"reviewed": {"123": {"sha": "...", ...}}, "skipped": {"456": {"reason": "..."}}}
SweepState = dict[str, dict[str, dict[str, Any]]]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# State file lives in the repo's .claude/ directory
STATE_FILE = Path(".claude/.review-sweep-state.json")

# Bot reviewers whose reviews don't count as "human reviewed"
REVIEW_BOTS: set[str] = {"sourcery-ai", "github-actions", "github-actions[bot]"}

# Patterns indicating a merge commit message
MERGE_PATTERNS = [
    re.compile(r"^Merge branch 'main'"),
    re.compile(r"^Merge remote-tracking branch 'origin/main'"),
    re.compile(r"^Merge branch 'master'"),
    re.compile(r"^Merge remote-tracking branch 'origin/master'"),
    re.compile(r"^Merge pull request #\d+"),
]


def _run_gh(args: list[str]) -> str:
    """Run a gh CLI command and return stdout.

    Raises SystemExit on failure.
    """
    cmd = ["gh", *args]
    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        logger.exception("gh CLI not found. Install it: https://cli.github.com/")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.exception("gh command failed: %s\n%s", " ".join(cmd), e.stderr.strip())
        sys.exit(1)
    return result.stdout.strip()


def _load_state() -> SweepState:
    """Load the sweep state file, returning empty state if missing."""
    if not STATE_FILE.exists():
        return {"reviewed": {}, "skipped": {}}
    try:
        data = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Corrupt state file, starting fresh: %s", e)
        return {"reviewed": {}, "skipped": {}}
    # Ensure expected keys
    if "reviewed" not in data:
        data["reviewed"] = {}
    if "skipped" not in data:
        data["skipped"] = {}
    return data


def _save_state(state: SweepState) -> None:
    """Write state to disk, creating parent directories as needed."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def _is_merge_message(message: str) -> bool:
    """Check if a commit message matches merge-back patterns."""
    return any(pat.search(message) for pat in MERGE_PATTERNS)


def _is_merge_back_pr(pr_number: int) -> bool:
    """Determine if a PR consists only of merge-back commits.

    A PR is a merge-back if ALL its commits have merge-pattern messages.
    """
    raw = _run_gh(
        [
            "pr",
            "view",
            str(pr_number),
            "--json",
            "commits",
        ]
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Could not parse commits for PR #%d", pr_number)
        return False

    commits = data.get("commits", [])
    if not commits:
        return False

    return all(_is_merge_message(c.get("messageHeadline", "")) for c in commits)


def _has_human_review(pr: dict[str, Any]) -> bool:
    """Check if a PR has at least one non-bot review."""
    for review in pr.get("reviews", []):
        login = review.get("author", {}).get("login", "")
        if login and login not in REVIEW_BOTS:
            return True
    return False


def cmd_query(
    *,
    include_mine: bool = False,
    include_drafts: bool = False,
) -> None:
    """Find reviewable PRs and output as JSON.

    Fetches all open PRs with their reviews, then filters to PRs that have
    no human reviews (bot reviews like sourcery-ai don't count).
    """
    json_fields = "number,title,author,url,headRefName,headRefOid,additions,deletions,isDraft,reviews,createdAt"

    raw = _run_gh(
        [
            "pr",
            "list",
            "--json",
            json_fields,
            "--limit",
            "50",
        ]
    )

    try:
        prs: list[dict[str, Any]] = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("Failed to parse PR list output")
        sys.exit(1)

    if not prs:
        print(json.dumps([]))
        return

    # Filter drafts
    if not include_drafts:
        prs = [pr for pr in prs if not pr.get("isDraft", False)]

    # Filter WIP
    prs = [pr for pr in prs if not pr.get("title", "").startswith("WIP")]

    # Filter out own PRs unless --include-mine
    if not include_mine:
        user_raw = _run_gh(["api", "user", "--jq", ".login"])
        current_user = user_raw.strip()
        prs = [pr for pr in prs if pr.get("author", {}).get("login", "") != current_user]

    # Filter to PRs with no human reviews
    prs = [pr for pr in prs if not _has_human_review(pr)]

    state = _load_state()
    candidates = []

    for pr in prs:
        pr_num = str(pr["number"])

        # Check if already skipped as merge-back
        if pr_num in state.get("skipped", {}):
            continue

        # Check if it's a merge-back PR
        if _is_merge_back_pr(pr["number"]):
            state.setdefault("skipped", {})[pr_num] = {
                "reason": "merge-back",
                "checked_at": datetime.now(UTC).isoformat(),
            }
            _save_state(state)
            logger.info("Skipped PR #%s (merge-back)", pr_num)
            continue

        # headRefOid already in response — no extra API call needed
        head_sha = pr.get("headRefOid", "")

        # Check if already reviewed at current HEAD
        reviewed = state.get("reviewed", {}).get(pr_num)
        if reviewed and reviewed.get("sha") == head_sha:
            continue

        # Build clean candidate entry (strip reviews from output)
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        candidates.append(
            {
                "number": pr["number"],
                "title": pr.get("title", ""),
                "author": pr.get("author", {}),
                "url": pr.get("url", ""),
                "headRefName": pr.get("headRefName", ""),
                "additions": additions,
                "deletions": deletions,
                "size": additions + deletions,
                "head_sha": head_sha,
                "createdAt": pr.get("createdAt", ""),
            }
        )

    # Sort by size (smallest first)
    candidates.sort(key=lambda p: p.get("size", 0))

    print(json.dumps(candidates, indent=2))


def cmd_mark(
    pr_number: int,
    sha: str,
    result_summary: str,
    depth: str = "light",
) -> None:
    """Record that a PR has been reviewed."""
    state = _load_state()
    state["reviewed"][str(pr_number)] = {
        "sha": sha,
        "reviewed_at": datetime.now(UTC).isoformat(),
        "result": result_summary,
        "depth": depth,
    }
    _save_state(state)
    logger.info("Marked PR #%d as reviewed (depth=%s)", pr_number, depth)


def cmd_status() -> None:
    """Display current sweep state."""
    state = _load_state()
    reviewed = state.get("reviewed", {})
    skipped = state.get("skipped", {})

    print("\nReview Sweep Status")
    print(f"{'=' * 40}")
    print(f"Reviewed: {len(reviewed)} PRs")
    print(f"Skipped:  {len(skipped)} PRs")

    if reviewed:
        print("\nRecently reviewed:")
        # Sort by review time, most recent first
        sorted_reviews = sorted(
            reviewed.items(),
            key=lambda x: x[1].get("reviewed_at", ""),
            reverse=True,
        )
        for pr_num, info in sorted_reviews[:10]:
            depth = info.get("depth", "unknown")
            result = info.get("result", "no summary")
            reviewed_at = info.get("reviewed_at", "unknown")
            print(f"  PR #{pr_num} [{depth}] — {result} ({reviewed_at})")

    if skipped:
        print("\nSkipped PRs:")
        for pr_num, info in skipped.items():
            reason = info.get("reason", "unknown")
            print(f"  PR #{pr_num} — {reason}")

    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Review sweep: find and track unreviewed PRs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # query subcommand
    query_parser = subparsers.add_parser(
        "query",
        help="Find reviewable PRs",
    )
    query_parser.add_argument(
        "--include-mine",
        action="store_true",
        help="Include PRs authored by you",
    )
    query_parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="Include draft PRs",
    )

    # mark subcommand
    mark_parser = subparsers.add_parser(
        "mark",
        help="Record a completed review",
    )
    mark_parser.add_argument(
        "pr_number",
        type=int,
        help="PR number",
    )
    mark_parser.add_argument(
        "sha",
        help="HEAD SHA of the PR at review time",
    )
    mark_parser.add_argument(
        "result_summary",
        help="Brief summary of review result",
    )
    mark_parser.add_argument(
        "--depth",
        choices=["light", "deep"],
        default="light",
        help="Review depth (default: light)",
    )

    # status subcommand
    subparsers.add_parser(
        "status",
        help="Show current sweep state",
    )

    args = parser.parse_args()

    if args.command == "query":
        cmd_query(
            include_mine=args.include_mine,
            include_drafts=args.include_drafts,
        )
    elif args.command == "mark":
        cmd_mark(
            pr_number=args.pr_number,
            sha=args.sha,
            result_summary=args.result_summary,
            depth=args.depth,
        )
    elif args.command == "status":
        cmd_status()


if __name__ == "__main__":
    main()
