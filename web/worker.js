// Runs Pyodide + tokenscape off the main thread. The zip arrives as bytes from the page and is
// written to Pyodide's in-memory filesystem only; nothing here makes a network request except
// loading the self-hosted runtime and wheel from this site.
import { loadPyodide } from './pyodide/pyodide.mjs';

const ready = (async () => {
  const py = await loadPyodide({ indexURL: new URL('./pyodide/', import.meta.url).href });
  const wheel = await fetch(new URL('./tokenscape.whl', import.meta.url));
  if (!wheel.ok) throw new Error(`could not load tokenscape.whl (${wheel.status})`);
  py.unpackArchive(await wheel.arrayBuffer(), 'wheel');
  return { py, buildReports: py.pyimport('tokenscape.webapp').build_reports };
})();

ready.then(
  () => self.postMessage({ type: 'ready' }),
  (err) => self.postMessage({ type: 'fatal', error: String(err?.message ?? err) }),
);

self.onmessage = async ({ data }) => {
  const { zip, fromDate, toDate, periodLabel } = data;
  const path = '/bundle.zip';
  try {
    const { py, buildReports } = await ready;
    py.FS.writeFile(path, new Uint8Array(zip));
    try {
      const result = JSON.parse(buildReports(path, fromDate, toDate, periodLabel));
      self.postMessage({ type: 'result', ...result });
    } finally {
      py.FS.unlink(path);
    }
  } catch (err) {
    self.postMessage({ type: 'result', error: String(err?.message ?? err) });
  }
};
