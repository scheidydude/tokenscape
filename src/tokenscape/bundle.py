from __future__ import annotations

import zipfile
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

from .config import claude_desktop_sessions_dir, claude_projects_dir, codex_sessions_dir
from .parser import SessionFile

# Folder names inside a bundle zip, per tool. Any other layout is read as "all .jsonl files".
BUNDLE_DIRS: dict[str, tuple[str, ...]] = {
    'claude': ('projects', 'desktop-sessions'),
    'codex': ('codex-sessions',),
}


def _local_session_dirs(tool: str) -> list[tuple[str, Path]]:
    if tool == 'codex':
        codex = codex_sessions_dir()
        return [('codex-sessions', codex)] if codex else []
    dirs = [('projects', claude_projects_dir())]
    desktop = claude_desktop_sessions_dir()
    if desktop:
        dirs.append(('desktop-sessions', desktop))
    return dirs


def create(output_path: Path | None = None, tool: str = 'claude') -> tuple[Path, int, int]:
    if output_path is None:
        date = datetime.now().strftime('%Y%m%d')
        suffix = '' if tool == 'claude' else f'-{tool}'
        output_path = Path.cwd() / f'tokenscape-bundle{suffix}-{date}.zip'

    file_count = 0
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arc_dir, local in _local_session_dirs(tool):
            if not local.exists():
                continue
            for jsonl in local.rglob('*.jsonl'):
                zf.write(jsonl, Path(arc_dir) / jsonl.relative_to(local))
                file_count += 1

    size_bytes = output_path.stat().st_size
    return output_path, file_count, size_bytes


class UnsafeBundleError(ValueError):
    '''A bundle zip that is malformed, too large, or contains unsafe paths.'''


@dataclass(frozen=True)
class ZipLimits:
    max_files: int = 100_000
    max_total_bytes: int = 20 * 1024**3
    # Applied per entry, only above min_ratio_bytes; real .jsonl transcripts compress ~5-15x.
    max_ratio: float = 200.0
    min_ratio_bytes: int = 1024**2


DEFAULT_LIMITS = ZipLimits()


def _is_unsafe_name(name: str) -> bool:
    if name.startswith(('/', '\\')):
        return True
    parts = PurePosixPath(name).parts
    return '..' in parts or (bool(parts) and ':' in parts[0])


def _validated_entries(zf: zipfile.ZipFile, limits: ZipLimits) -> list[zipfile.ZipInfo]:
    '''Check every entry against `limits` and return the .jsonl file entries in archive order.'''
    infos = zf.infolist()
    if len(infos) > limits.max_files:
        raise UnsafeBundleError(f'bundle has {len(infos)} entries (limit {limits.max_files})')
    total = 0
    jsonl: list[zipfile.ZipInfo] = []
    for info in infos:
        if _is_unsafe_name(info.filename):
            raise UnsafeBundleError(f'unsafe path in bundle: {info.filename!r}')
        if info.is_dir() or not info.filename.lower().endswith('.jsonl'):
            continue
        total += info.file_size
        if total > limits.max_total_bytes:
            raise UnsafeBundleError(f'bundle expands past {limits.max_total_bytes} bytes')
        if (
            info.file_size > limits.min_ratio_bytes
            and info.file_size > limits.max_ratio * max(info.compress_size, 1)
        ):
            raise UnsafeBundleError(f'suspicious compression ratio for {info.filename!r}')
        jsonl.append(info)
    return jsonl


def _known_dirs() -> set[str]:
    return {d for dirs in BUNDLE_DIRS.values() for d in dirs}


def _pick_for_tool(names: list[str], tool: str) -> list[str]:
    '''The tool's bundle folders, in order; every file if the zip has no known bundle folders.'''
    if not any(n.split('/', 1)[0] in _known_dirs() for n in names):
        return names
    return [n for sub in BUNDLE_DIRS[tool] for n in names if n.startswith(f'{sub}/')]


@contextmanager
def source_context(
    source: str, limits: ZipLimits = DEFAULT_LIMITS, tool: str = 'claude'
) -> Generator[list[SessionFile], None, None]:
    '''Yield `tool`'s session files in a bundle zip or directory, for `files=` on its parser.

    Zip entries are read in place (never extracted) and checked against `limits` first.
    '''
    if tool not in BUNDLE_DIRS:
        raise ValueError(f'unknown tool: {tool!r}')
    if source.lower().endswith('.zip'):
        try:
            zf = zipfile.ZipFile(source)
        except zipfile.BadZipFile as exc:
            raise UnsafeBundleError(f'not a valid zip: {source}') from exc
        with zf:
            names = [i.filename for i in _validated_entries(zf, limits)]
            yield [zipfile.Path(zf, n) for n in _pick_for_tool(names, tool)]
        return

    source_dir = Path(source)
    if any((source_dir / d).is_dir() for d in _known_dirs()):
        roots = [source_dir / d for d in BUNDLE_DIRS[tool] if (source_dir / d).is_dir()]
    else:
        roots = [source_dir]
    yield [f for root in roots for f in root.rglob('*.jsonl')]
