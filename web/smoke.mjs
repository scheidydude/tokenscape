// Smoke test for the browser build: loads the built Pyodide + wheel from dist/ the same way
// worker.js does and runs build_reports on a bundle. Usage: node smoke.mjs [bundle.zip]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import zlib from 'node:zlib';
import { loadPyodide } from './dist/pyodide/pyodide.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(here, 'dist');

// Minimal single-entry stored zip, so the test needs no fixture tooling.
function zipOf(name, text) {
  const data = Buffer.from(text);
  const nameBuf = Buffer.from(name);
  const crc = zlib.crc32(data);
  const local = Buffer.alloc(30);
  local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4);
  local.writeUInt32LE(crc, 14); local.writeUInt32LE(data.length, 18); local.writeUInt32LE(data.length, 22);
  local.writeUInt16LE(nameBuf.length, 26);
  const central = Buffer.alloc(46);
  central.writeUInt32LE(0x02014b50, 0); central.writeUInt16LE(20, 4); central.writeUInt16LE(20, 6);
  central.writeUInt32LE(crc, 16); central.writeUInt32LE(data.length, 20); central.writeUInt32LE(data.length, 24);
  central.writeUInt16LE(nameBuf.length, 28);
  const centralOffset = local.length + nameBuf.length + data.length;
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(1, 8); end.writeUInt16LE(1, 10);
  end.writeUInt32LE(central.length + nameBuf.length, 12); end.writeUInt32LE(centralOffset, 16);
  return Buffer.concat([local, nameBuf, data, central, nameBuf, end]);
}

const bundle = process.argv[2]
  ? fs.readFileSync(process.argv[2])
  : zipOf('projects/p/a.jsonl', fs.readFileSync(path.join(here, '../tests/fixtures/sample-session.jsonl'), 'utf8'));

const t0 = performance.now();
const py = await loadPyodide({ indexURL: path.join(dist, 'pyodide') + path.sep });
py.unpackArchive(new Uint8Array(fs.readFileSync(path.join(dist, 'tokenscape.whl'))), 'wheel');
py.FS.writeFile('/bundle.zip', new Uint8Array(bundle));
const buildReports = py.pyimport('tokenscape.webapp').build_reports;
const result = JSON.parse(buildReports('/bundle.zip', null, null, 'all time'));
const seconds = ((performance.now() - t0) / 1000).toFixed(2);

if (result.error) {
  console.error(`FAIL: ${result.error}`);
  process.exit(1);
}
if (!result.html.startsWith('<!DOCTYPE html>') || !result.markdown.startsWith('# tokenscape report')) {
  console.error('FAIL: unexpected report output');
  process.exit(1);
}
console.log(`OK tokenscape ${result.version}: ${result.turns} turns, ${result.sessions} sessions, ${result.from} to ${result.to} in ${seconds}s`);
