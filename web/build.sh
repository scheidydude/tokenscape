#!/usr/bin/env bash
# Build the static site into web/dist: page files, self-hosted Pyodide, and a tokenscape wheel
# built from this checkout. Serve locally with: python3 -m http.server -d web/dist
set -euo pipefail

web="$(cd "$(dirname "$0")" && pwd)"
repo="$(dirname "$web")"
out="$web/dist"

cd "$web"
[ -d node_modules/pyodide ] || npm ci

rm -rf "$out"
mkdir -p "$out/pyodide"
cp index.html style.css app.js worker.js "$out/"
for f in pyodide.mjs pyodide.asm.js pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
  cp "node_modules/pyodide/$f" "$out/pyodide/"
done

# A fixed name keeps the page independent of the version; Pyodide installs it by content.
uv build --wheel --directory "$repo" --out-dir "$out/wheel" >/dev/null
mv "$out"/wheel/tokenscape-*.whl "$out/tokenscape.whl"
rm -rf "$out/wheel"

echo "Built $out ($(du -sh "$out" | cut -f1))"
