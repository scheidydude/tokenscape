const LARGE_FILE_BYTES = 250 * 1024 * 1024;

const $ = (id) => document.getElementById(id);
const els = {
  drop: $('drop'), file: $('file'), dropText: $('drop-text'), dropSub: $('drop-sub'), sizeWarn: $('size-warn'),
  period: $('period'), custom: $('custom'), from: $('from'), to: $('to'),
  run: $('run'), status: $('status'),
  result: $('result'), summary: $('summary'), report: $('report'),
  dlHtml: $('dl-html'), dlMd: $('dl-md'), version: $('version'),
};

let engineReady = false;
let busy = false;
let selected = null;
let lastResult = null;

const DROP_HINTS = {
  claude: 'A <code>tokenscape bundle</code> zip, or a zip of <code>~/.claude/projects</code>',
  codex: 'A <code>tokenscape --tool codex bundle</code> zip, or a zip of <code>~/.codex/sessions</code>',
};

const selectedTool = () => document.querySelector('input[name="tool"]:checked').value;

const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle('error', isError);
}

function updateRunButton() {
  els.run.disabled = !(engineReady && selected && !busy);
}

function formatBytes(n) {
  if (n >= 1024 ** 3) return `${(n / 1024 ** 3).toFixed(1)} GB`;
  if (n >= 1024 ** 2) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(n / 1024))} KB`;
}

function utcDay(offsetDays = 0) {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

// Dates are inclusive UTC days, matching tokenscape.webapp.build_reports.
function periodRange() {
  const value = els.period.value;
  if (value === 'all') return { fromDate: null, toDate: null, periodLabel: 'all time' };
  if (value === 'custom') {
    return { fromDate: els.from.value || null, toDate: els.to.value || null, periodLabel: 'custom' };
  }
  const days = Number(value);
  return { fromDate: utcDay(-(days - 1)), toDate: utcDay(), periodLabel: `last ${days} days` };
}

function chooseFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.zip')) {
    setStatus('Please choose a .zip file.', true);
    return;
  }
  selected = file;
  els.dropText.textContent = `${file.name} · ${formatBytes(file.size)}`;
  els.sizeWarn.hidden = file.size < LARGE_FILE_BYTES;
  if (engineReady) setStatus('Ready.');
  updateRunButton();
}

function download(text, type, name) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement('a'), { href: url, download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

worker.onmessage = ({ data }) => {
  if (data.type === 'ready') {
    engineReady = true;
    setStatus(selected ? 'Ready.' : 'Ready. Choose a zip to start.');
    updateRunButton();
    return;
  }
  if (data.type === 'fatal') {
    setStatus(`The analysis engine failed to load: ${data.error}`, true);
    return;
  }

  busy = false;
  updateRunButton();
  if (data.error) {
    setStatus(data.error, true);
    return;
  }
  lastResult = data;
  els.version.textContent = `tokenscape ${data.version}`;
  els.summary.textContent =
    `${data.turns.toLocaleString()} turns · ${data.sessions.toLocaleString()} sessions · ` +
    `${data.files.toLocaleString()} files · ${data.from} to ${data.to}`;
  els.report.srcdoc = data.html;
  els.result.hidden = false;
  setStatus('Done.');
  els.result.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

worker.onerror = (event) => {
  busy = false;
  updateRunButton();
  setStatus(`Something went wrong: ${event.message || 'worker error'}`, true);
};

els.file.addEventListener('change', () => chooseFile(els.file.files[0]));
for (const name of ['dragenter', 'dragover']) {
  els.drop.addEventListener(name, (e) => { e.preventDefault(); els.drop.classList.add('over'); });
}
for (const name of ['dragleave', 'drop']) {
  els.drop.addEventListener(name, () => els.drop.classList.remove('over'));
}
els.drop.addEventListener('drop', (e) => {
  e.preventDefault();
  chooseFile(e.dataTransfer.files[0]);
});

for (const radio of document.querySelectorAll('input[name="tool"]')) {
  radio.addEventListener('change', () => { els.dropSub.innerHTML = DROP_HINTS[selectedTool()]; });
}

els.period.addEventListener('change', () => {
  els.custom.hidden = els.period.value !== 'custom';
});

els.run.addEventListener('click', async () => {
  if (!selected) return;
  busy = true;
  updateRunButton();
  setStatus('Analyzing…');
  const zip = await selected.arrayBuffer();
  worker.postMessage({ zip, tool: selectedTool(), ...periodRange() }, [zip]);
});

els.dlHtml.addEventListener('click', () => {
  if (lastResult) download(lastResult.html, 'text/html', `tokenscape-${lastResult.from}-to-${lastResult.to}.html`);
});
els.dlMd.addEventListener('click', () => {
  if (lastResult) download(lastResult.markdown, 'text/markdown', `tokenscape-${lastResult.from}-to-${lastResult.to}.md`);
});
