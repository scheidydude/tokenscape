from __future__ import annotations

import subprocess
import sys

# The browser build (Pyodide) loads only these modules; they must not pull in CLI/TUI deps.
CORE = ['parser', 'bundle', 'aggregate', 'patterns', 'classifier', 'report', 'html_report', 'webapp']
CLI_ONLY = ('rich', 'typer', 'textual', 'click', 'numpy')


def test_core_modules_import_without_cli_deps():
    imports = '; '.join(f'import tokenscape.{m}' for m in CORE)
    code = (
        f'import sys; {imports}; '
        f'print(sorted(m for m in sys.modules if m.split(".")[0] in {CLI_ONLY!r}))'
    )
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == '[]'
