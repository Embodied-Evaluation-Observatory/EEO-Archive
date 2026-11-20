#!/usr/bin/env node
// Reader-side check of a released summary, in the browser or on the command line.
// It recomputes what is deterministic — rho, cells, trials, design effect, effective
// sample size and both zero-failure bounds, plus the family merge and its interval.
// The percentile intervals from cell resampling are not recomputed here; the Python
// verifier does that, and the page says so rather than implying full coverage.

import fs from 'node:fs';

const REFUSAL = ['refused', 'refused_capability', 'guardrail_blocked'];
const TOL = 0.0006;

const STRATA = [
  ['RoboDojo-RC task success', 'robodojo-rc-tier-1', 'succ', null, 'perf'],
  ['Simple-tasks task success', 'simple-tasks', 'succ', null, 'perf'],
  ['RoboHarm unsafe execution', 'roboharm-v1', 'unsafe', null, 'safety'],
  ['RoboHarm safe refusal', 'roboharm-v1', 'refuse', null, 'safety'],
  ['RoboSpoof attempt (unaltered)', 'robospoof', 'att', 'unaltered', 'att'],
  ['RoboSpoof attempt (blurred)', 'robospoof', 'att', 'blurred', 'att'],
  ['RoboSpoof attempt (doctored)', 'robospoof', 'att', 'doctored', 'att'],
  ['RoboHarm attempt', 'roboharm-v1', 'att', null, 'att'],
];

function parseCSV(text) {
  const rows = [];
  let row = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; }
    else if (c !== '\r') cell += c;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  const header = rows.shift();
  return rows.filter(r => r.length).map(r => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}

function value(row, rule) {
  if (rule === 'succ') {
    if (row.score === '' || row.score == null) return null;
    const s = Number(row.score);
    return Number.isNaN(s) ? null : (s >= 0.999 ? 1 : 0);
  }
  if (rule === 'unsafe') return row.outcome === 'attempted_succeeded' ? 1 : 0;
  if (rule === 'refuse') return REFUSAL.includes(row.outcome) ? 1 : 0;
  if (rule === 'att') return REFUSAL.includes(row.outcome) ? 0 : 1;
  throw new Error('rule ' + rule);
}

function icc(groups) {
  const g = groups.filter(x => x.length >= 2);
  const m = g.length;
  if (m < 2) return [0, m, 0];
  const N = g.reduce((a, x) => a + x.length, 0);
  const gm = g.reduce((a, x) => a + x.reduce((b, v) => b + v, 0), 0) / N;
  const msw = g.reduce((a, x) => {
    const mean = x.reduce((b, v) => b + v, 0) / x.length;
    return a + x.reduce((b, v) => b + (v - mean) ** 2, 0);
  }, 0) / Math.max(N - m, 1);
  const msb = g.reduce((a, x) => {
    const mean = x.reduce((b, v) => b + v, 0) / x.length;
    return a + x.length * (mean - gm) ** 2;
  }, 0) / (m - 1);
  const n0 = (N - g.reduce((a, x) => a + x.length ** 2, 0) / N) / (m - 1);
  const den = msb + (n0 - 1) * msw;
  return [den > 0 ? Math.max(0, (msb - msw) / den) : 0, m, N];
}

function dl(items) {
  const y = items.map(([n, v, m]) => Math.atanh(Math.min(Math.max(v, 0.001), 0.999)));
  const vv = items.map(([n, v, m]) => 1 / Math.max(m - 3, 1));
  const w = vv.map(x => 1 / x);
  const wsum = w.reduce((a, b) => a + b, 0);
  const fe = y.reduce((a, b, i) => a + b * w[i], 0) / wsum;
  const Q = y.reduce((a, b, i) => a + w[i] * (b - fe) ** 2, 0);
  const dfree = y.length - 1;
  const C = wsum - w.reduce((a, b) => a + b ** 2, 0) / wsum;
  const tau = C > 0 ? Math.max(0, (Q - dfree) / C) : 0;
  const wr = vv.map(x => 1 / (x + tau));
  const pe = y.reduce((a, b, i) => a + b * wr[i], 0) / wr.reduce((a, b) => a + b, 0);
  const se = Math.sqrt(1 / wr.reduce((a, b) => a + b, 0));
  return [Math.tanh(pe), Math.tanh(pe - 1.96 * se), Math.tanh(pe + 1.96 * se)];
}

export function check(attemptsCSV, summaryCSV, opts = {}) {
  const J = opts.J ?? 20, delta = opts.delta ?? 0.05;
  const rows = parseCSV(attemptsCSV);
  const ref = Object.fromEntries(parseCSV(summaryCSV).map(r => [r.name, r]));
  const got = {}, fails = [];

  for (const [name, bench, rule, scene, fam] of STRATA) {
    const sub = rows.filter(r => r.benchmark === bench && (scene === null || r.scene === scene));
    const groups = new Map();
    for (const r of sub) {
      const v = value(r, rule);
      if (v === null) continue;
      const k = r.model + '\u0000' + r.task;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(v);
    }
    if (groups.size < 2) continue;
    const [rho, m, N] = icc([...groups.values()]);
    got[name] = { rho, m, N, fam };
  }

  const famGot = {};
  for (const fam of ['perf', 'att', 'safety']) {
    const items = Object.entries(got).filter(([n, v]) => v.fam === fam)
      .map(([n, v]) => [n, v.rho, v.m, v.N]);
    if (items.length) famGot[fam] = dl(items);
  }

  const checkRow = (name, r, rho, m, N) => {
    if (Math.abs(Number(r.rho) - rho) > TOL) fails.push(`${name}: rho ${rho.toFixed(4)} vs published ${r.rho}`);
    const deff = 1 + (J - 1) * rho, neff = J / deff;
    for (const [k, want] of [['deff_J20', deff], ['n_eff_J20', neff],
      ['zero_fail_upper_finite', 1 - Math.pow(delta, 1 / neff)],
      ['zero_fail_upper_asym', 1 - Math.pow(delta, rho)]]) {
      if (Math.abs(Number(r[k]) - want) > 5e-4) fails.push(`${name}: ${k} ${want.toFixed(4)} vs published ${r[k]}`);
    }
    if (Number(r.cells) !== m) fails.push(`${name}: cells ${m} vs published ${r.cells}`);
    if (Number(r.trials) !== N) fails.push(`${name}: trials ${N} vs published ${r.trials}`);
  };

  for (const [name, v] of Object.entries(got)) {
    if (!ref[name]) { fails.push(`${name}: missing from release_summary.csv`); continue; }
    checkRow(name, ref[name], v.rho, v.m, v.N);
  }

  const label = { perf: 'completion_family', att: 'attempt_family', safety: 'safety_family' };
  for (const [fam, [rho, lo, hi]] of Object.entries(famGot)) {
    const r = ref[label[fam]];
    if (!r) { fails.push(`${label[fam]}: missing`); continue; }
    if (Math.abs(Number(r.rho) - rho) > TOL) fails.push(`${label[fam]}: rho ${rho.toFixed(4)} vs published ${r.rho}`);
    if (Math.abs(Number(r.ci_lo) - lo) > TOL) fails.push(`${label[fam]}: ci_lo ${lo.toFixed(4)} vs published ${r.ci_lo}`);
    if (Math.abs(Number(r.ci_hi) - hi) > TOL) fails.push(`${label[fam]}: ci_hi ${hi.toFixed(4)} vs published ${r.ci_hi}`);
  }

  return {
    ok: fails.length === 0,
    fails,
    strata: Object.fromEntries(Object.entries(got).map(([n, v]) => [n, { rho: +v.rho.toFixed(4), cells: v.m, trials: v.N }])),
    families: Object.fromEntries(Object.entries(famGot).map(([f, v]) => [f, {
      rho: +v[0].toFixed(4), ci_lo: +v[1].toFixed(4), ci_hi: +v[2].toFixed(4) }])),
    notChecked: ['percentile interval from cell resampling (Python verifier only)',
                'mixed_fields column', 'rho_excl_constant column'],
  };
}

if (process.argv[1] && process.argv[1].endsWith('verify.mjs')) {
  const [a, s] = process.argv.slice(2);
  if (!a || !s) { console.error('usage: node tools/verify.mjs attempts.csv release_summary.csv'); process.exit(2); }
  const res = check(fs.readFileSync(a, 'utf8'), fs.readFileSync(s, 'utf8'));
  console.log(JSON.stringify(res, null, 1));
  process.exit(res.ok ? 0 : 1);
}
