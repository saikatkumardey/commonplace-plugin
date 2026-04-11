---
name: setup
description: "Install commonplace hooks into ~/.claude/settings.json. Run once after installing the plugin. Copies session-start and session-summarize hooks, then wires them into Stop and SessionStart events."
---

# Commonplace Setup

Install the commonplace hooks so memory recall and session summarization happen automatically.

## What this installs

- **SessionStart hook**: injects recent commonplace entries into context at the start of every session
- **Stop hook**: summarizes the session using Haiku and writes it to commonplace when the session ends

## Steps

1. Find the plugin's hooks directory. The plugin is installed at one of:
   - `~/.claude/plugins/commonplace@*/hooks/`
   - Or check: `ls ~/.claude/plugins/ | grep commonplace`

2. Copy both hook scripts to `~/.claude/hooks/`:

```bash
PLUGIN_DIR=$(ls -d ~/.claude/plugins/commonplace@* 2>/dev/null | head -1)
mkdir -p ~/.claude/hooks
cp "$PLUGIN_DIR/hooks/session-start.py" ~/.claude/hooks/commonplace-session-start.py
cp "$PLUGIN_DIR/hooks/session-summarize.py" ~/.claude/hooks/commonplace-session-summarize.py
chmod +x ~/.claude/hooks/commonplace-session-start.py ~/.claude/hooks/commonplace-session-summarize.py
echo "Hooks copied."
```

3. Wire the hooks into `~/.claude/settings.json` using Python (safe merge, won't clobber existing hooks):

```bash
python3 << 'EOF'
import json
from pathlib import Path

settings_path = Path.home() / ".claude/settings.json"
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
hooks = settings.setdefault("hooks", {})

# SessionStart hook
session_start_hooks = hooks.setdefault("SessionStart", [{}])
if not session_start_hooks:
    session_start_hooks.append({})
start_group = session_start_hooks[0]
start_commands = start_group.setdefault("hooks", [])
start_script = str(Path.home() / ".claude/hooks/commonplace-session-start.py")
if not any(start_script in h.get("command", "") for h in start_commands):
    start_commands.append({
        "type": "command",
        "command": f"python3 {start_script} 2>/dev/null || true",
        "timeout": 10,
        "statusMessage": "Recalling memory..."
    })

# Stop hook
stop_hooks = hooks.setdefault("Stop", [{}])
if not stop_hooks:
    stop_hooks.append({})
stop_group = stop_hooks[0]
stop_commands = stop_group.setdefault("hooks", [])
stop_script = str(Path.home() / ".claude/hooks/commonplace-session-summarize.py")
if not any(stop_script in h.get("command", "") for h in stop_commands):
    stop_commands.append({
        "type": "command",
        "command": f"python3 {stop_script} 2>/dev/null || true",
        "timeout": 45,
        "async": True
    })

settings_path.write_text(json.dumps(settings, indent=2))
print("Hooks wired into settings.json.")
EOF
```

4. Confirm both hooks are registered:

```bash
python3 -c "
import json
from pathlib import Path
s = json.loads((Path.home() / '.claude/settings.json').read_text())
for event in ('SessionStart', 'Stop'):
    cmds = [h['command'][:60] for g in s.get('hooks', {}).get(event, []) for h in g.get('hooks', [])]
    print(f'{event}: {cmds}')
"
```

Both should show `commonplace` in the output.

## Notes

- The session-summarize hook uses `claude -p` with Haiku — requires `claude` CLI in PATH
- The Stop hook runs async so it doesn't block session exit
- Re-running setup is safe — it checks before adding duplicates
- The session-start hook injects memory as `additionalContext`, visible in the session system prompt
