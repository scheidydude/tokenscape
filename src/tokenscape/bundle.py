from __future__ import annotations

import shutil
import tempfile
import zipfile
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .config import claude_desktop_sessions_dir, claude_projects_dir


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


@contextmanager
def source_context(source: str) -> Generator[Path, None, None]:
    import tokenscape.parser as parser_mod

    tmp_dir: Path | None = None
    if source.lower().endswith('.zip'):
        tmp_dir = Path(tempfile.mkdtemp(prefix='tokenscape-'))
        with zipfile.ZipFile(source) as zf:
            zf.extractall(tmp_dir)
        source_dir = tmp_dir
    else:
        source_dir = Path(source)

    orig_iter = parser_mod._iter_session_files

    def _from_source():
        found_any_subdir = False
        for subdir in ('projects', 'desktop-sessions'):
            d = source_dir / subdir
            if d.exists():
                found_any_subdir = True
                yield from d.rglob('*.jsonl')
        if not found_any_subdir:
            yield from source_dir.rglob('*.jsonl')

    parser_mod._iter_session_files = _from_source
    try:
        yield source_dir
    finally:
        parser_mod._iter_session_files = orig_iter
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)
