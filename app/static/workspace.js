import {query, readInput, encodeInput} from './api.js';
import {el, evidence, table} from './table.js';

const byId = id => document.getElementById(id);
const settings = JSON.parse(byId('settings').textContent);
const links = [...document.querySelectorAll('[data-module]')];
const body = byId('grid-data');
const alert = byId('notice');
const live = byId('state');
const action = document.querySelector('#source button[type=submit]');
const topExport = byId('export');
const confirmBtn = byId('confirm-batch');
let selected = Object.hasOwn(settings.tabs, location.hash.slice(1)) ? location.hash.slice(1) : 'signals';
let result = null;
let inputs = {};
let reviewVersion = 0;
let renderEpoch = 0;
let activeView = null;
const filter = byId('filter');
const onlyOpen = byId('only-open');

function notice(message, error = false) {
  alert.value = message;
  alert.classList.toggle('problem', error);
}

function tag(code) {
  return el('span', settings.reasons[code] || code, code === 'OK' || code === 'MATCH' ? 'state' : 'state problem');
}

function filterTable() {
  if (!activeView) return;
  const {columns, rows, stage} = activeView;
  const term = filter.value.trim().toLocaleLowerCase();
  const chosen = rows.filter(row => {
    if (stage === 'signals' && onlyOpen.checked && row.status !== 'open') return false;
    return !term || [row.key, row.store_name, row.region, row.code, row.status, row.start_day,
      row.trigger_day, row.end_day, row.detail, ...(row.corrections || []).map(c => c.detail)]
      .some(value => String(value ?? '').toLocaleLowerCase().includes(term));
  });
  byId('shown').textContent = `${chosen.length} / ${rows.length}`;
  table(body, columns, chosen);
}
filter.addEventListener('input', filterTable);
onlyOpen.addEventListener('change', filterTable);
const uploaded = new Map();

function showEvidence(row) {
  const record = byId('evidence-key');
  const details = byId('signal');
  if (!row) {
    record.textContent = '';
    details.replaceChildren(el('p', '本批没有预警区间', 'empty'));
    return;
  }
  record.textContent = `${row.key || ''} ${row.start_day || ''}`.trim();
  const ev = row.evidence || {};
  const lines = [
    ['触发日', row.trigger_day], ['可干预区间', `${row.start_day} → ${row.end_day}`],
    ['首个基准日', ev.baseline_day], ['状态', row.status],
    ['走弱营业日', (ev.weak_days || []).join('、')],
    ['缺口日（停业/缺报）', (ev.gap_days || []).join('、') || '无'],
    ['跨财周', row.cross_week ? '是（不拆段）' : '否'],
    ['财周序号', (ev.fiscal_weeks || []).join('、')],
  ];
  const content = el('ol', undefined, byId('evidence-panel').dataset.instrument);
  for (const [metric, value] of lines) {
    const line = el('li');
    line.append(el('span', metric));
    line.append(el('strong', value ?? '—', 'measure'));
    content.append(line);
  }
  if (row.corrections?.length) {
    content.append(el('li', `迟到/留痕 ${row.corrections.length} 条：${row.corrections.map(c => c.kind).join('、')}`));
  }
  details.replaceChildren(content);
}

function inspect(row) {
  const button = el('button', '查看依据', 'btn');
  button.type = 'button';
  button.addEventListener('click', () => showEvidence(row));
  const raw = evidence('来源字段', row.raw || []);
  const cell = el('div');
  cell.append(button, raw);
  return cell;
}

function setRun(report) {
  result = report;
  byId('created').textContent = `${report.manifest.created.slice(0, 19).replace('T', ' ')} UTC`;
  const id = result.manifest.run_id;
  byId('run-id').textContent = id.slice(0, 9);
  byId('run-id').title = id;
  topExport.hidden = false;
  topExport.href = `/api/export/${id}`;
  confirmBtn.hidden = false;
  const openCount = report.alerts.filter(a => a.status === 'open').length;
  const values = {...report.counts, open_count: openCount};
  for (const cell of document.querySelectorAll('[data-count]')) cell.textContent = values[cell.dataset.count] ?? '—';
  live.textContent = `批次 ${id.slice(0, 9)} · ${report.balanced ? '记录已闭合' : '记录数不符'}` +
    (report.confirmed_run ? ' · 本批已确认锁定' : '');
  showEvidence(report.alerts[0]);
}

async function render() {
  const ticket = ++renderEpoch;
  const stage = selected;
  byId('phase').textContent = settings.tabs[stage];
  byId('review').hidden = true;
  for (const link of links) {
    if (link.dataset.module === stage) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  if (!result) return;
  const id = result.manifest.run_id;
  const keyCol = [settings.key, 'key'];
  const line = ['行号', 'line', 'num'];
  try {
    let view, rows;
    if (stage === 'signals') {
      const liveSignals = await query('/api/signals');
      view = [keyCol, ['门店', 'store_name'], ['区域', 'region'], ['起始日', 'start_day'],
              ['触发日', 'trigger_day', 'num'], ['截止日', 'end_day', 'num'],
              ['状态', r => el('span', r.status, r.status === 'confirmed' ? 'state' : 'state problem')],
              ['依据', r => inspect(r)]];
      rows = liveSignals.alerts;
      byId('only-open-wrap').hidden = false;
    } else if (stage === 'domain') {
      const domain = await query('/api/domain', inputs);
      view = [keyCol, ['营业日', 'day', 'num'], ['财周', 'calendar'], ['状态', 'status'],
              ['本年', 'amount', 'num'], ['基准', 'baseline', 'num'], ['阈值', 'threshold', 'num'],
              ['判定', r => tag(r.code)]];
      rows = domain.days;
      byId('only-open-wrap').hidden = true;
    } else if (stage === 'quality') {
      const quality = await query('/api/quality', inputs);
      const raw = r => evidence('来源字段', r.raw || []);
      view = [keyCol, line, ['判定', r => tag(r.code)], ['说明', 'detail'], ['字段', raw]];
      rows = [...quality.rejected, ...quality.suppressed].sort((a, b) => a.line - b.line);
      byId('only-open-wrap').hidden = true;
    } else if (stage === 'intake') {
      const intake = await query('/api/intake', inputs);
      const raw = r => evidence('来源字段', r.raw || []);
      view = [line, ['分类', 'kind'], ['字段', raw]];
      rows = [...intake.rows.map(r => ({...r, kind: '完整记录'})), ...intake.rejected.map(r => ({...r, kind: '坏行'})),
              ...intake.blank_lines.map(l => ({line: l, kind: '空白行', raw: []})),
              ...intake.header_lines.map(l => ({line: l, kind: '重复表头', raw: []}))].sort((a, b) => a.line - b.line);
      byId('only-open-wrap').hidden = true;
    } else if (stage === 'contract') {
      const contract = await query('/api/contract', inputs);
      view = [keyCol, line, ['修订', 'revision', 'num'], ['营业日', 'day'], ['状态', 'status'],
              ['来源时刻 UTC', 'time'], ['字段', r => evidence('归一值', Object.entries(r.fields).map(([k, v]) => `${k} · ${v}`))]];
      rows = contract.accepted;
      byId('only-open-wrap').hidden = true;
    } else if (stage === 'runs') {
      const runs = await query('/api/runs');
      view = [['指纹', 'id'], ['创建 UTC', 'created'], ['操作', r => {
        const current = r.id === id;
        const button = el('button', current ? '复算当前批' : '打开此批', 'btn');
        button.addEventListener('click', async () => {
          button.disabled = true;
          try {
            if (current) {
              setRun(await query(`/api/runs/${id}/replay`, {}));
              notice('复算已核对，确认结论未回退');
            } else {
              const [past, original] = await Promise.all(
                [query(`/api/runs/${r.id}`), query(`/api/runs/${r.id}/source`)]);
              inputs = original;
              setRun(past);
              notice('已打开历史批次');
              await render();
            }
          } catch (error) { notice(error.message, true); }
          finally { button.disabled = false; }
        });
        return button;
      }]];
      rows = runs;
      byId('only-open-wrap').hidden = true;
    } else {
      const timeline = await query(`/api/review/${id}`);
      view = [['版本', 'version', 'num'], ['结论', 'decision'], ['处理意见', 'note'], ['登记 UTC', 'changed']];
      rows = timeline;
      byId('only-open-wrap').hidden = true;
      if (ticket === renderEpoch) {
        reviewVersion = timeline[0]?.version || 0;
        byId('review').hidden = false;
      }
    }
    if (ticket === renderEpoch) {
      if (activeView?.stage !== stage) filter.value = '';
      activeView = {stage, columns: view, rows};
      byId('tools').hidden = false;
      filterTable();
    }
  } catch (error) {
    if (ticket === renderEpoch) notice(error.message, true);
  }
}

window.addEventListener('hashchange', () => {
  selected = Object.hasOwn(settings.tabs, location.hash.slice(1)) ? location.hash.slice(1) : 'signals';
  render();
});

byId('sample').addEventListener('click', async () => {
  try {
    const responses = await Promise.all(['shift', 'external'].map(name => fetch(`/api/samples/${name}`)));
    if (responses.some(r => !r.ok)) throw Error('样例暂时不可用');
    const files = await Promise.all(responses.map(r => r.arrayBuffer()));
    for (const [index, name] of ['source', 'book'].entries()) {
      const decoded = new TextDecoder('utf-8').decode(files[index]);
      byId(`${name}-csv`).value = decoded;
      uploaded.set(name, {text: byId(`${name}-csv`).value, bytes: files[index]});
    }
    byId('source-file').value = '';
    byId('book-file').value = '';
    document.querySelector('#source details').open = true;
    notice('样例已载入');
  } catch (error) { notice(error.message, true); }
});

for (const name of ['source', 'book']) {
  byId(`${name}-file`).addEventListener('change', async event => {
    const file = event.target.files[0];
    if (!file) return;
    action.disabled = true;
    try {
      const [text, bytes] = await readInput(file);
      byId(`${name}-csv`).value = text;
      uploaded.set(name, {text: byId(`${name}-csv`).value, bytes});
      notice(`已读取 ${file.name}`);
    } catch (error) {
      event.target.value = '';
      notice(error.message, true);
    } finally { action.disabled = false; }
  });
}

byId('source').addEventListener('submit', async event => {
  event.preventDefault();
  const candidate = {};
  for (const [control, name] of [['source', 'data'], ['book', 'book']]) {
    const text = byId(`${control}-csv`).value;
    const original = uploaded.get(control);
    if (original && text === original.text) candidate[`${name}_base64`] = encodeInput(original.bytes);
    else if (text.length || original) candidate[name] = text;
  }
  action.disabled = true;
  ++renderEpoch;
  notice('计算中');
  try {
    const report = await query('/api/runs', candidate);
    inputs = candidate;
    setRun(report);
    notice(report.corrections?.length ? `批次已计算，${report.corrections.length} 条迟到/锁定留痕` : '批次已计算');
    await render();
  } catch (error) { notice(error.message, true); }
  finally { action.disabled = false; }
});

confirmBtn.addEventListener('click', async () => {
  if (!result) return;
  try {
    const conf = await query(`/api/runs/${result.manifest.run_id}/confirm`, {});
    notice(`已确认锁定 ${conf.count} 个区间，后续重跑不再新增`);
    setRun(await query(`/api/runs/${result.manifest.run_id}/replay`, {}));
    await render();
  } catch (error) { notice(error.message, true); }
});

byId('review').addEventListener('submit', async event => {
  event.preventDefault();
  const id = result.manifest.run_id;
  const note = byId('review-note');
  try {
    await query(`/api/review/${id}`, {version: reviewVersion, decision: byId('decision').value, note: note.value});
    notice('值班意见已登记');
    note.value = '';
    await render();
  } catch (error) {
    notice(error.message, true);
    if (error.status === 409) await render();
  }
});
render();
