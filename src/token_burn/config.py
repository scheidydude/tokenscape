import os
import tomllib
from pathlib import Path


def claude_projects_dir() -> Path:
    base = os.environ.get('CLAUDE_CONFIG_DIR')
    if base:
        return Path(base) / 'projects'
    return Path.home() / '.claude' / 'projects'


def claude_desktop_sessions_dir() -> Path | None:
    p = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'local-agent-mode-sessions'
    return p if p.exists() else None


def load_labels_config() -> dict[str, str] | None:
    xdg = os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))
    path = Path(xdg) / 'token-burn' / 'config.toml'
    if not path.exists():
        return None
    try:
        with path.open('rb') as f:
            data = tomllib.load(f)
        section = data.get('labels', {})
        base_url = section.get('base_url', '').rstrip('/')
        model = section.get('model', '')
        if not base_url or not model:
            return None
        return {
            'base_url': base_url,
            'api_key': section.get('api_key', 'none'),
            'model': model,
        }
    except Exception:
        return None
