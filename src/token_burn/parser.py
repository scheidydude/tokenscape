from __future__ import annotations

import json
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from .config import claude_desktop_sessions_dir, claude_projects_dir
from .models import display_name
from .types import TokenUsage, Turn

_MCP_RE = re.compile(r'^mcp__([^_]+)__')


def _parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except ValueError:
        return datetime.now(timezone.utc)


def _project_name(cwd: str) -> str:
    if not cwd:
        return 'unknown'
    return Path(cwd).name or cwd


def _extract_tools(content: list[object]) -> tuple[list[str], list[str], list[str]]:
    tools: list[str] = []
    bash_inputs: list[str] = []
    edited_files: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'tool_use':
            name = block.get('name', '')
            if isinstance(name, str) and name:
                tools.append(name)
                if name == 'Bash':
                    inp = block.get('input', {})
                    if isinstance(inp, dict):
                        cmd = inp.get('command', '')
                        if isinstance(cmd, str) and cmd.strip():
                            bash_inputs.append(cmd.strip())
                elif name in ('Edit', 'Write', 'NotebookEdit'):
                    inp = block.get('input', {})
                    if isinstance(inp, dict):
                        fp = inp.get('file_path', '') or inp.get('path', '')
                        if isinstance(fp, str) and fp.strip():
                            edited_files.append(fp.strip())
    return tools, bash_inputs, edited_files


_XML_BLOCK_RE = re.compile(r'^<[a-z]')


def _is_injected_content(text: str) -> bool:
    s = text.strip()
    if s.startswith('Base directory for this skill:'):
        return True
    # Skill prompt templates have Usage/Example sections
    if len(s) > 200 and ('\nUsage:' in s or '\nExample:' in s or '\nExample\n' in s):
        return True
    # Long markdown-headed blocks are skill documentation
    if len(s) > 300 and re.match(r'^#+ \w', s):
        return True
    # System/task XML notifications: <task-notification>, <system-reminder>, etc.
    if _XML_BLOCK_RE.match(s):
        return True
    return False


def _extract_user_text(content: list[object]) -> str:
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'text':
            text = block.get('text', '')
            if isinstance(text, str) and not _is_injected_content(text):
                parts.append(text)
        elif isinstance(block, str):
            parts.append(block)
    return ' '.join(parts)


def _stream_jsonl(path: Path) -> Iterator[dict[str, object]]:
    with path.open(encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
            except json.JSONDecodeError:
                continue


def list_projects() -> list[tuple[str, datetime]]:
    '''Return (project_name, last_modified) sorted most-recent first.'''
    seen: dict[str, datetime] = {}
    for path in _iter_session_files():
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        cwd = ''
        try:
            with path.open(encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    try:
                        obj = json.loads(line.strip())
                        if isinstance(obj, dict) and obj.get('cwd'):
                            cwd = str(obj['cwd'])
                            break
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
        if not cwd:
            continue
        name = _project_name(cwd)
        if name not in seen or mtime > seen[name]:
            seen[name] = mtime
    return sorted(seen.items(), key=lambda x: x[1], reverse=True)


def _iter_session_files() -> Iterator[Path]:
    projects = claude_projects_dir()
    if projects.exists():
        yield from projects.rglob('*.jsonl')
    desktop = claude_desktop_sessions_dir()
    if desktop:
        yield from desktop.rglob('*.jsonl')


def _stream_turns_from_path(
    path: Path,
    seen_ids: set[str],
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[Turn]:
    pending_user_text = ''

    for entry in _stream_jsonl(path):
        msg = entry.get('message', {})
        if not isinstance(msg, dict):
            msg = {}

        if entry.get('type') == 'user' or msg.get('role') == 'user':
            content = msg.get('content', [])
            if isinstance(content, list):
                pending_user_text = _extract_user_text(content)
            elif isinstance(content, str) and not _is_injected_content(content):
                pending_user_text = content
            continue

        if entry.get('type') not in ('assistant', None):
            if msg.get('role') != 'assistant':
                pending_user_text = ''
                continue

        if msg.get('role') not in ('assistant', None) and entry.get('type') != 'assistant':
            pending_user_text = ''
            continue

        msg_id = msg.get('id', '')
        if not isinstance(msg_id, str) or not msg_id:
            pending_user_text = ''
            continue

        if msg_id in seen_ids:
            pending_user_text = ''
            continue

        usage_raw = msg.get('usage', {})
        if not isinstance(usage_raw, dict):
            pending_user_text = ''
            continue

        usage = TokenUsage(
            input=int(usage_raw.get('input_tokens', 0) or 0),
            output=int(usage_raw.get('output_tokens', 0) or 0),
            cache_read=int(usage_raw.get('cache_read_input_tokens', 0) or 0),
            cache_write=int(usage_raw.get('cache_creation_input_tokens', 0) or 0),
        )

        if usage.total == 0:
            pending_user_text = ''
            continue

        ts_raw = entry.get('timestamp', '')
        ts = _parse_iso(str(ts_raw)) if ts_raw else datetime.now(timezone.utc)

        if from_dt and ts < from_dt:
            pending_user_text = ''
            continue
        if to_dt and ts > to_dt:
            pending_user_text = ''
            continue

        model_raw = str(msg.get('model', '') or '')
        content = msg.get('content', [])
        tools, bash_inputs, edited_files = _extract_tools(content) if isinstance(content, list) else ([], [], [])

        cwd_raw = str(entry.get('cwd', '') or '')

        seen_ids.add(msg_id)
        yield Turn(
            message_id=msg_id,
            timestamp=ts,
            model=display_name(model_raw),
            usage=usage,
            tools_used=tools,
            bash_inputs=bash_inputs,
            edited_files=edited_files,
            user_text=pending_user_text,
            cwd=cwd_raw,
            project=_project_name(cwd_raw),
        )
        pending_user_text = ''


def stream_turns(
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[Turn]:
    seen_ids: set[str] = set()
    for path in _iter_session_files():
        yield from _stream_turns_from_path(path, seen_ids, from_dt, to_dt)


def stream_sessions(
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[list[Turn]]:
    '''Yield turns grouped by session file, in order, with per-file deduplication.'''
    for path in _iter_session_files():
        seen_ids: set[str] = set()
        turns = list(_stream_turns_from_path(path, seen_ids, from_dt, to_dt))
        if turns:
            yield turns
