from __future__ import annotations

import json
import zipfile
from pathlib import Path

from tokenscape.webapp import build_reports

FIXTURE = Path(__file__).parent / 'fixtures' / 'sample-session.jsonl'


def _bundle(tmp_path: Path, entries: dict[str, str]) -> str:
    path = tmp_path / 'b.zip'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return str(path)


def test_all_time_report(tmp_path: Path):
    out = json.loads(build_reports(_bundle(tmp_path, {'projects/p/a.jsonl': FIXTURE.read_text()})))
    assert out['turns'] == 2
    assert out['sessions'] == 1
    assert (out['from'], out['to']) == ('2026-05-29', '2026-05-29')
    assert out['markdown'].startswith('# tokenscape report')
    assert out['html'].startswith('<!DOCTYPE html>')


def test_to_date_is_inclusive(tmp_path: Path):
    zip_path = _bundle(tmp_path, {'projects/p/a.jsonl': FIXTURE.read_text()})
    assert json.loads(build_reports(zip_path, '2026-05-29', '2026-05-29'))['turns'] == 2
    assert 'error' in json.loads(build_reports(zip_path, '2026-05-30', '2026-06-30'))


def test_unsafe_zip_is_an_error_not_an_exception(tmp_path: Path):
    out = json.loads(build_reports(_bundle(tmp_path, {'../evil.jsonl': FIXTURE.read_text()})))
    assert out['error'].startswith('This zip was rejected')


def test_zip_without_sessions(tmp_path: Path):
    out = json.loads(build_reports(_bundle(tmp_path, {'readme.txt': 'hi'})))
    assert 'No .jsonl' in out['error']
