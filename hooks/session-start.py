#!/usr/bin/env python3
"""
SessionStart hook: inject recent commonplace memory into context.
Installs via /commonplace setup.
"""
import subprocess
import json


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()


topics = run(["commonplace", "topics"])
recent = run(["commonplace", "search", "decisions errors preferences context projects", "--limit", "8"])

context = f"=== Commonplace Memory (auto-recalled at session start) ===\nTopics:\n{topics}\n\nRecent relevant entries:\n{recent}"

out = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(out))
