import os
from pathlib import Path


def claude_projects_dir() -> Path:
    base = os.environ.get('CLAUDE_CONFIG_DIR')
    if base:
        return Path(base) / 'projects'
    return Path.home() / '.claude' / 'projects'


def claude_desktop_sessions_dir() -> Path | None:
    p = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'local-agent-mode-sessions'
    return p if p.exists() else None
