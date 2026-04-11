#!/usr/bin/env python3
"""
UserPromptSubmit hook: search commonplace with keywords from the user's message
and inject relevant memory as a systemMessage before Claude responds.

Fires only when the message signals that historical context is relevant
(past events, decisions, errors, project work, etc.).

To add your own project/topic signals, create ~/.commonplace/recall-signals.txt
with one keyword per line. These are added to the base set.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# Generic signals that suggest historical context is needed
BASE_SIGNALS = [
    # Temporal
    r"remember", r"recall", r"last\s+time", r"before", r"earlier",
    r"yesterday", r"last\s+week", r"previously",
    # Questions about past
    r"did\s+we", r"have\s+we", r"was\s+there", r"what\s+was", r"what\s+did",
    r"when\s+did", r"how\s+did", r"where\s+did",
    # Status / progress
    r"status\s+of", r"update\s+on", r"progress\s+on",
    # Decisions and issues
    r"decided", r"decision", r"error", r"bug", r"fix", r"issue", r"problem",
    # Generic tech work
    r"project", r"setup", r"config", r"service", r"tool", r"script",
    r"cron", r"hook", r"deploy", r"build", r"install",
]


def load_user_signals():
    """Load optional user-defined recall signals from ~/.commonplace/recall-signals.txt"""
    signals_file = Path.home() / ".commonplace/recall-signals.txt"
    if not signals_file.exists():
        return []
    try:
        lines = signals_file.read_text().splitlines()
        return [re.escape(l.strip()) for l in lines if l.strip() and not l.startswith("#")]
    except Exception:
        return []


def build_pattern():
    signals = BASE_SIGNALS + load_user_signals()
    return re.compile(r"\b(" + "|".join(signals) + r")\b", re.IGNORECASE)


def extract_keywords(prompt):
    """Pull meaningful tokens from the prompt for BM25/semantic search."""
    text = re.sub(r"https?://\S+|`[^`]+`", " ", prompt)
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", text)
    stops = {"the", "and", "for", "are", "was", "you", "can", "this", "that",
              "with", "have", "has", "not", "but", "from", "they", "will",
              "what", "how", "why", "when", "where", "who", "its", "also",
              "just", "like", "make", "want", "need", "would", "should", "could"}
    keywords = [w for w in words if w.lower() not in stops]
    return " ".join(keywords[:20])


def search_commonplace(query):
    result = subprocess.run(
        ["commonplace", "search", query, "--limit", "5"],
        capture_output=True, text=True, timeout=8
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = ""
    if isinstance(data, dict):
        prompt = data.get("prompt") or data.get("message") or ""
        if isinstance(prompt, list):
            prompt = " ".join(
                b.get("text", "") for b in prompt
                if isinstance(b, dict) and b.get("type") == "text"
            )

    if not prompt or len(prompt) < 15:
        sys.exit(0)

    pattern = build_pattern()
    if not pattern.search(prompt):
        sys.exit(0)

    keywords = extract_keywords(prompt)
    if not keywords:
        sys.exit(0)

    results = search_commonplace(keywords)
    if not results or len(results) < 20:
        sys.exit(0)

    out = {"systemMessage": f"Relevant memory from commonplace:\n{results}"}
    print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
