from __future__ import annotations

import json
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from .config import codex_sessions_dir
from .models import display_name
from .types import TokenUsage, Turn

_MODEL_RE = re.compile(r'based on (GPT-[\d.]+\S*)', re.I)


def _parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except ValueError:
        return datetime.now(timezone.utc)


def _project_name(cwd: str) -> str:
    if not cwd:
        return 'unknown'
    return Path(cwd).name or cwd


def _iter_codex_session_files() -> Iterator[Path]:
    base = codex_sessions_dir()
    if base and base.exists():
        yield from base.rglob('*.jsonl')


def _stream_jsonl(path: Path) -> Iterator[dict]:
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
    seen: dict[str, datetime] = {}
    for path in _iter_codex_session_files():
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        cwd = ''
        for entry in _stream_jsonl(path):
            if entry.get('type') == 'session_meta':
                cwd = str(entry.get('payload', {}).get('cwd', '') or '')
                break
        if not cwd:
            continue
        name = _project_name(cwd)
        if name not in seen or mtime > seen[name]:
            seen[name] = mtime
    return sorted(seen.items(), key=lambda x: x[1], reverse=True)


def _stream_turns_from_path(
    path: Path,
    seen_ids: set[str],
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[Turn]:
    entries = list(_stream_jsonl(path))

    session_cwd = ''
    model_name = 'GPT-5'
    for entry in entries:
        if entry.get('type') == 'session_meta':
            p = entry.get('payload', {})
            session_cwd = str(p.get('cwd', '') or '')
            text = (p.get('base_instructions', {}) or {}).get('text', '') or ''
            m = _MODEL_RE.search(text)
            if m:
                model_name = display_name(m.group(1).lower())
            break

    current_turn_id: str | None = None
    current_ts: datetime | None = None
    current_tokens: list[dict] = []
    current_tools: list[str] = []
    current_bash: list[str] = []
    current_user_text: str = ''
    current_cwd: str = session_cwd

    def _flush() -> Turn | None:
        if not current_turn_id or current_turn_id in seen_ids:
            return None
        usage = TokenUsage()
        for u in current_tokens:
            usage = TokenUsage(
                input=usage.input + int(u.get('input_tokens', 0) or 0),
                output=usage.output + int(u.get('output_tokens', 0) or 0),
                cache_read=usage.cache_read + int(u.get('cached_input_tokens', 0) or 0),
                cache_write=0,
            )
        if usage.total == 0:
            return None
        ts = current_ts or datetime.now(timezone.utc)
        if from_dt and ts < from_dt:
            return None
        if to_dt and ts > to_dt:
            return None
        seen_ids.add(current_turn_id)
        cwd = current_cwd or session_cwd
        return Turn(
            message_id=current_turn_id,
            timestamp=ts,
            model=model_name,
            usage=usage,
            tools_used=list(current_tools),
            bash_inputs=list(current_bash),
            edited_files=[],
            user_text=current_user_text,
            cwd=cwd,
            project=_project_name(cwd),
        )

    for entry in entries:
        etype = entry.get('type', '')
        payload = entry.get('payload', {})
        if not isinstance(payload, dict):
            payload = {}
        ptype = payload.get('type', '')

        if etype == 'turn_context':
            cwd = str(payload.get('cwd', '') or '')
            if cwd:
                current_cwd = cwd
            continue

        if etype == 'event_msg':
            if ptype == 'task_started':
                current_turn_id = str(payload.get('turn_id', '') or '')
                ts_raw = entry.get('timestamp', '')
                current_ts = _parse_iso(str(ts_raw)) if ts_raw else datetime.now(timezone.utc)
                current_tokens = []
                current_tools = []
                current_bash = []
                current_user_text = ''

            elif ptype == 'token_count' and current_turn_id:
                last = (payload.get('info', {}) or {}).get('last_token_usage', {})
                if isinstance(last, dict):
                    current_tokens.append(last)

            elif ptype == 'user_message':
                msg = str(payload.get('message', '') or '')
                if msg:
                    current_user_text = msg

            elif ptype == 'task_complete':
                turn = _flush()
                if turn:
                    yield turn
                current_turn_id = None
                current_ts = None
                current_tokens = []
                current_tools = []
                current_bash = []
                current_user_text = ''

        elif etype == 'response_item' and current_turn_id:
            ri_type = payload.get('type', '')
            if ri_type in ('function_call', 'custom_tool_call'):
                name = str(payload.get('name', '') or '')
                if name:
                    current_tools.append(name)
                    if name == 'exec_command':
                        try:
                            args = json.loads(payload.get('arguments', '{}') or '{}')
                            cmd = str(args.get('cmd', '') or '').strip()
                            if cmd:
                                current_bash.append(cmd)
                        except (json.JSONDecodeError, TypeError):
                            pass


def stream_turns(
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[Turn]:
    seen_ids: set[str] = set()
    for path in _iter_codex_session_files():
        yield from _stream_turns_from_path(path, seen_ids, from_dt, to_dt)


def stream_sessions(
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> Iterator[list[Turn]]:
    for path in _iter_codex_session_files():
        seen_ids: set[str] = set()
        turns = list(_stream_turns_from_path(path, seen_ids, from_dt, to_dt))
        if turns:
            yield turns
