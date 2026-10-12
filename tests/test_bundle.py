from __future__ import annotations

import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tokenscape.bundle import UnsafeBundleError, ZipLimits, source_context
from tokenscape.cli import app
from tokenscape.parser import stream_sessions, stream_turns

FIXTURE = Path(__file__).parent / 'fixtures' / 'sample-session.jsonl'


def _make_zip(path: Path, entries: dict[str, str | bytes]) -> Path:
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(zipfile.ZipInfo(name), data, compress_type=zipfile.ZIP_DEFLATED)
    return path


def _fixture_with_prefix(prefix: str) -> str:
    return FIXTURE.read_text().replace('"msg_0', f'"{prefix}msg_0')


def test_zip_source_reads_in_place(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {
        'projects/p/a.jsonl': FIXTURE.read_text(),
        'desktop-sessions/s/b.jsonl': _fixture_with_prefix('d'),
    })
    with source_context(str(bundle)) as files:
        turns = list(stream_turns(files=files))
        sessions = list(stream_sessions(files=files))
    assert [t.message_id for t in turns] == ['msg_01', 'msg_02', 'dmsg_01', 'dmsg_02']
    assert len(sessions) == 2


def test_zip_without_bundle_subdirs_reads_all_jsonl(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {'x/a.jsonl': FIXTURE.read_text()})
    with source_context(str(bundle)) as files:
        assert len(list(stream_turns(files=files))) == 2


def test_zip_ignores_non_jsonl_entries(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {
        'projects/p/a.jsonl': FIXTURE.read_text(),
        'projects/p/notes.txt': 'not a session',
        '__MACOSX/._a.jsonl.meta': b'\x00\x01',
    })
    with source_context(str(bundle)) as files:
        assert [f.name for f in files] == ['a.jsonl']


def test_directory_source(tmp_path: Path):
    (tmp_path / 'projects' / 'p').mkdir(parents=True)
    (tmp_path / 'projects' / 'p' / 'a.jsonl').write_text(FIXTURE.read_text())
    with source_context(str(tmp_path)) as files:
        assert len(list(stream_turns(files=files))) == 2


def test_parallel_bundles_do_not_mix(tmp_path: Path):
    a = _make_zip(tmp_path / 'a.zip', {'projects/p/a.jsonl': _fixture_with_prefix('A')})
    b = _make_zip(tmp_path / 'b.zip', {'projects/p/b.jsonl': _fixture_with_prefix('B')})
    # Both contexts are open before either one streams, which the old global swap got wrong.
    barrier = threading.Barrier(2)

    def run(bundle: Path) -> set[str]:
        with source_context(str(bundle)) as files:
            barrier.wait(timeout=5)
            return {t.message_id for t in stream_turns(files=files)}

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids_a, ids_b = pool.map(run, [a, b])
    assert ids_a == {'Amsg_01', 'Amsg_02'}
    assert ids_b == {'Bmsg_01', 'Bmsg_02'}


@pytest.mark.parametrize('name', ['../evil.jsonl', 'projects/../../evil.jsonl', '/etc/evil.jsonl', 'C:/evil.jsonl'])
def test_unsafe_paths_rejected(tmp_path: Path, name: str):
    bundle = _make_zip(tmp_path / 'b.zip', {name: FIXTURE.read_text()})
    with pytest.raises(UnsafeBundleError, match='unsafe path'):
        with source_context(str(bundle)):
            pass


def test_zip_bomb_ratio_rejected(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {'projects/p/bomb.jsonl': b'\x00' * (8 * 1024**2)})
    with pytest.raises(UnsafeBundleError, match='compression ratio'):
        with source_context(str(bundle)):
            pass


def test_total_size_limit(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {
        'projects/p/a.jsonl': FIXTURE.read_text(),
        'projects/p/b.jsonl': FIXTURE.read_text(),
    })
    limits = ZipLimits(max_total_bytes=FIXTURE.stat().st_size + 1)
    with pytest.raises(UnsafeBundleError, match='expands past'):
        with source_context(str(bundle), limits):
            pass


def test_file_count_limit(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {f'projects/p/{i}.jsonl': '' for i in range(3)})
    with pytest.raises(UnsafeBundleError, match='entries'):
        with source_context(str(bundle), ZipLimits(max_files=2)):
            pass


def test_not_a_zip_rejected(tmp_path: Path):
    bad = tmp_path / 'b.zip'
    bad.write_text('not a zip')
    with pytest.raises(UnsafeBundleError, match='not a valid zip'):
        with source_context(str(bad)):
            pass


def test_full_report_rejects_unsafe_bundle(tmp_path: Path):
    bundle = _make_zip(tmp_path / 'b.zip', {'../evil.jsonl': FIXTURE.read_text()})
    result = CliRunner().invoke(app, ['full-report', '--source', str(bundle)])
    assert result.exit_code == 1
    assert 'unsafe path' in result.output
