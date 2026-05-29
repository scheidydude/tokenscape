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


def _extract_tools(content: list[object]) -> tuple[list[str], list[str]]:
    tools: list[str] = []
    bash_inputs: list[str] = []
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
    return tools, bash_inputs


def _extract_user_text(content: list[object]) -> str:
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'text':
            text = block.get('text', '')
            if isinstance(text, str):
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


def _iter_session_files() -> Iterator[Path]:
    projects = claude_projects_dir()
    if projects.exists():
        yield from projects.rglob('*.jsonl')
    desktop = claude_desktop_sessions_dir()
    if desktop:
        yield from desktop.rglob('*.jsonl')


def stream_turns(
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[Turn]:
    seen_ids: set[str] = set()

    for path in _iter_session_files():
        pending_user_text = ''

        for entry in _stream_jsonl(path):
            role = entry.get('type') or (
                entry.get('message', {}).get('role') if isinstance(entry.get('message'), dict) else None
            )

            # Capture user text for next assistant turn
            msg = entry.get('message', {})
            if not isinstance(msg, dict):
                msg = {}

            if entry.get('type') == 'user' or msg.get('role') == 'user':
                content = msg.get('content', [])
                if isinstance(content, list):
                    pending_user_text = _extract_user_text(content)
                elif isinstance(content, str):
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
            tools, bash_inputs = _extract_tools(content) if isinstance(content, list) else ([], [])

            cwd_raw = str(entry.get('cwd', '') or '')

            seen_ids.add(msg_id)
            yield Turn(
                message_id=msg_id,
                timestamp=ts,
                model=display_name(model_raw),
                usage=usage,
                tools_used=tools,
                bash_inputs=bash_inputs,
                user_text=pending_user_text,
                cwd=cwd_raw,
                project=_project_name(cwd_raw),
            )
            pending_user_text = ''
