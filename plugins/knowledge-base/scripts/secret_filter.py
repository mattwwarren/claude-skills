"""Regex-based secret redaction for wiki content.

Runs at two points (defense-in-depth):
  1. As an explicit pipeline step in /wiki-ingest
  2. Inline in transcript_reader.py on error message capture

Usage:
    from scripts.secret_filter import redact
    clean = redact(raw_text)

    # CLI usage:
    python3 scripts/secret_filter.py < input.txt > clean.txt
"""

from __future__ import annotations

import re
import sys

# ---------------------------------------------------------------------------
# Secret pattern families
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Anthropic API keys
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}", re.ASCII)),
    # Generic SK keys (Stripe, OpenAI, etc.)
    ("sk-key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}", re.ASCII)),
    # Stripe publishable keys
    ("stripe-pk", re.compile(r"\bpk_(test|live)_[A-Za-z0-9]{20,}", re.ASCII)),
    # GitHub PATs
    ("github-pat", re.compile(r"\b(ghp|gho|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}", re.ASCII)),
    # Slack tokens
    ("slack-token", re.compile(r"\b(xoxb|xoxp|xoxa|xoxr)-[A-Za-z0-9\-]{10,}", re.ASCII)),
    # AWS access key IDs
    ("aws-access-key", re.compile(r"\bAKIA[A-Z0-9]{16}\b", re.ASCII)),
    # Google OAuth client secrets
    ("google-oauth", re.compile(r"\bGOCSPX-[A-Za-z0-9_\-]{20,}", re.ASCII)),
    # GCP project IDs
    ("gcp-project", re.compile(r"\bapi-project-\d{10,}\b", re.ASCII)),
    # AWS Cognito pool IDs (us-east-1_XXXXXXXXX format)
    ("cognito-pool", re.compile(r"\bus-[a-z]+-\d_[A-Za-z0-9]{9}\b", re.ASCII)),
    # JWT tokens (header.payload.signature — all three parts present)
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b",
            re.ASCII,
        ),
    ),
    # Bearer tokens: "Bearer <token>"
    (
        "bearer-token",
        re.compile(r"\bBearer\s+([A-Za-z0-9_\-\.]{20,})", re.ASCII),
    ),
    # Long tokens in backticks (20+ chars alphanumeric, not safe)
    (
        "backtick-token",
        re.compile(r"`([A-Za-z0-9_\-]{20,})`"),
    ),
    # Long bare tokens outside backticks (30+ chars) — catches secrets in logs/env vars
    (
        "bare-token",
        re.compile(r"(?<![`/\.\w])([A-Za-z0-9_\-]{30,})(?![`/\.\w])"),
    ),
]

# Replacement placeholder
_REDACTED = "[REDACTED]"

# ---------------------------------------------------------------------------
# Safe-token heuristics — tokens that must NOT be redacted
# ---------------------------------------------------------------------------

# Structural file path pattern (must start with ~ / . /)
_RE_FILE_PATH = re.compile(r"^[~.]?/[\w./@\-]+$")
# Simple filename (word.ext)
_RE_SIMPLE_FILENAME = re.compile(r"^[\w\-]+\.[\w]+$")
# Git SHA (40 hex chars) or short SHA (7-8 hex chars)
_RE_GIT_SHA = re.compile(r"^[0-9a-f]{7,40}$", re.ASCII)
# UUID (8-4-4-4-12 hex)
_RE_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.ASCII | re.IGNORECASE
)
# MCP tool name prefix
_RE_MCP = re.compile(r"^mcp__")
# CLI flag (--flag or -f)
_RE_CLI_FLAG = re.compile(r"^-{1,2}[a-z][\w\-]*$", re.ASCII | re.IGNORECASE)
# Known safe prefixes that are not secrets
_SAFE_PREFIXES = ("com.", "org.", "net.", "io.", "dev.")


def _is_safe_token(token: str) -> bool:
    """Return True if token is safe (should not be redacted)."""
    if _RE_GIT_SHA.match(token):
        return True
    if _RE_UUID.match(token):
        return True
    if _RE_MCP.match(token):
        return True
    if _RE_CLI_FLAG.match(token):
        return True
    if _RE_FILE_PATH.match(token):
        return True
    if _RE_SIMPLE_FILENAME.match(token):
        return True
    if any(token.startswith(p) for p in _SAFE_PREFIXES):
        return True
    return False


def redact(text: str) -> str:
    """Redact all secret patterns from text, preserving safe tokens."""
    for _name, pattern in _PATTERNS:
        def _replace(m: re.Match[str]) -> str:
            # For patterns with a capture group (backtick-token, bare-token, bearer-token),
            # check if the captured token is safe before redacting.
            if m.lastindex:
                captured = m.group(1)
                if _is_safe_token(captured):
                    return m.group(0)  # leave untouched
                # Redact only the captured portion
                return m.group(0).replace(captured, _REDACTED)
            return _REDACTED

        text = pattern.sub(_replace, text)
    return text


def main() -> None:
    raw = sys.stdin.read()
    print(redact(raw), end="")


if __name__ == "__main__":
    main()
