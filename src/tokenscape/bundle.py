from __future__ import annotations

import zipfile
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

from .config import claude_desktop_sessions_dir, claude_projects_dir
from .parser import SessionFile


def create(output_path: Path | None = None) -> tuple[Path, int, int]:
    if output_path is None:
        date = datetime.now().strftime('%Y%m%d')
        output_path = Path.cwd() / f'tokenscape-bundle-{date}.zip'

    projects = claude_projects_dir()
    desktop = claude_desktop_sessions_dir()

    file_count = 0
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if projects.exists():
            for jsonl in projects.rglob('*.jsonl'):
                zf.write(jsonl, Path('projects') / jsonl.relative_to(projects))
                file_count += 1
        if desktop and desktop.exists():
            for jsonl in desktop.rglob('*.jsonl'):
                zf.write(jsonl, Path('desktop-sessions') / jsonl.relative_to(desktop))
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

_SUBDIRS = ('projects', 'desktop-sessions')


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


def _order_like_bundle(names: list[str]) -> list[str]:
    '''Bundle subdirs first (projects, then desktop-sessions); everything if neither exists.'''
    picked = [n for sub in _SUBDIRS for n in names if n.startswith(f'{sub}/')]
    return picked or names


@contextmanager
def source_context(
    source: str, limits: ZipLimits = DEFAULT_LIMITS
) -> Generator[list[SessionFile], None, None]:
    '''Yield the session files in a bundle zip or directory, for passing as `files=` to the parser.

    Zip entries are read in place (never extracted) and checked against `limits` first.
    '''
    if source.lower().endswith('.zip'):
        try:
            zf = zipfile.ZipFile(source)
        except zipfile.BadZipFile as exc:
            raise UnsafeBundleError(f'not a valid zip: {source}') from exc
        with zf:
            names = [i.filename for i in _validated_entries(zf, limits)]
            yield [zipfile.Path(zf, n) for n in _order_like_bundle(names)]
        return

    source_dir = Path(source)
    subdirs = [source_dir / sub for sub in _SUBDIRS if (source_dir / sub).exists()]
    roots = subdirs or [source_dir]
    yield [f for root in roots for f in root.rglob('*.jsonl')]
