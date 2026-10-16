'use strict';

/**
 * Parse the org label taxonomy from `.github/labels.yml`.
 *
 * Extracted so the org-wide weekly sweep (sync-labels-all.yml), the per-repo
 * CLI (scripts/sync-labels.sh), and the targeted birth bootstrap
 * (repo-birth-bootstrap.yml) share one parser. Three copies of the same regex
 * is how a taxonomy silently diverges between the sweep and a birth.
 *
 * The format is the single-line flow-mapping form the org file already uses:
 *   - { name: "area/ci", color: "0e8a16", description: "CI and automation" }
 * Keys may appear in any order; a line missing any of the three is skipped
 * rather than half-applied, because GitHub's label API requires all three and
 * a partial label is worse than an absent one.
 */

/**
 * Every well-formed label line, in file order, duplicates included. The one
 * line grammar both parseLabels() and the closure check read.
 *
 * @param {string} text contents of a labels.yml
 * @returns {Array<{name: string, color: string, description: string}>}
 */
function parseLabelLines(text) {
  if (typeof text !== 'string') return [];
  const out = [];
  for (const line of text.split('\n')) {
    if (/^\s*#/.test(line)) continue;
    const name = line.match(/\bname:\s*"([^"]+)"/);
    const color = line.match(/\bcolor:\s*"([^"]+)"/);
    const description = line.match(/\bdescription:\s*"([^"]*)"/);
    if (!name || !color || !description) continue;
    out.push({ name: name[1], color: color[1], description: description[1] });
  }
  return out;
}

/**
 * @param {string} text contents of a labels.yml
 * @returns {Array<{name: string, color: string, description: string}>}
 */
function parseLabels(text) {
  const out = [];
  const seen = new Set();
  for (const label of parseLabelLines(text)) {
    if (seen.has(label.name)) continue;
    seen.add(label.name);
    out.push(label);
  }
  return out;
}

// ── Producer-to-consumer closure ────────────────────────────────────────────
// A label a form, workflow or config names but the taxonomy does not declare
// is silently dropped by GitHub (issue forms) or created ad hoc with a random
// color (API writes) — either way the taxonomy stops describing reality. The
// extractors below read only the literal label positions of each consumer
// kind; they are not a taxonomy parser, and a dynamically built name (e.g.
// `sev:${key}`) is out of their reach by design.

const unquote = (v) => v.trim().replace(/^["']|["']$/g, '').trim();
const splitList = (v) => v.split(',').map(unquote).filter(Boolean);

/** `labels:` of an issue form: flow `[a, b]` or a block list. */
function issueFormLabels(text) {
  const lines = String(text || '').split('\n');
  const i = lines.findIndex((l) => /^labels:/.test(l));
  if (i === -1) return [];
  const inline = lines[i].replace(/^labels:\s*/, '').replace(/\s+#.*$/, '');
  if (inline.startsWith('[')) return splitList(inline.replace(/^\[|\]$/g, ''));
  if (inline) return splitList(inline);
  const out = [];
  for (const l of lines.slice(i + 1)) {
    const m = l.match(/^\s+-\s*(.+?)\s*$/);
    if (!m) break;
    out.push(unquote(m[1]));
  }
  return out;
}

/** actions/stale inputs whose key names a label (comma-separated values). */
function staleWorkflowLabels(text) {
  const out = [];
  for (const l of String(text || '').split('\n')) {
    const m = l.match(/^\s*([a-z-]*label[a-z-]*):\s*(.+?)\s*$/);
    if (m) out.push(...splitList(m[2]));
  }
  return out;
}

// Dependabot's own label when an `updates` entry sets no `labels:` (GitHub
// docs, "Dependabot options reference" > labels): every PR gets
// `dependencies`, plus a per-ecosystem label once more than one package
// manager is configured. `labels: [ ]` disables both.
const DEPENDABOT_DEFAULT_LABEL = 'dependencies';

/**
 * Labels Dependabot applies: the explicit `labels:` lists under `updates`
 * entries (flow or block), plus the implicit default for every
 * `- package-ecosystem:` entry that sets none. The per-ecosystem default
 * label is not derivable here, so with more than one ecosystem an entry
 * without `labels:` yields a reference no taxonomy declares and the closure
 * fails closed until the entry names its labels explicitly.
 */
function dependabotLabels(text) {
  const lines = String(text || '').split('\n');
  const out = [];
  const entries = [];
  lines.forEach((l, i) => {
    const m = /^(\s*)-\s*package-ecosystem:\s*["']?([^"'\s#]+)/.exec(l);
    if (!m) return;
    let end = lines.length;
    for (let j = i + 1; j < lines.length; j++) {
      const next = lines[j];
      if (!next.trim() || /^\s*#/.test(next)) continue;
      const indent = next.length - next.trimStart().length;
      if (indent < m[1].length || (indent === m[1].length && /^\s*-/.test(next))) { end = j; break; }
    }
    const body = lines.slice(i + 1, end);
    entries.push({ ecosystem: m[2], hasLabels: body.some((b) => /^\s*labels:/.test(b)) });
  });
  const ecosystems = new Set(entries.map((e) => e.ecosystem));
  for (const e of entries) {
    if (e.hasLabels) continue;
    out.push(DEPENDABOT_DEFAULT_LABEL);
    if (ecosystems.size > 1) out.push(`<dependabot default ecosystem label for ${e.ecosystem}>`);
  }
  lines.forEach((l, i) => {
    const m = l.match(/^(\s*)labels:\s*(.*?)\s*$/);
    if (!m) return;
    if (m[2].startsWith('[')) {
      out.push(...splitList(m[2].replace(/^\[|\]$/g, '')));
      return;
    }
    for (const next of lines.slice(i + 1)) {
      const item = next.match(/^(\s*)-\s*(.+?)\s*$/);
      if (!item || item[1].length < m[1].length) break;
      out.push(unquote(item[2]));
    }
  });
  return out;
}

/** actions/labeler config: every top-level key is a label it applies. */
function labelerConfigLabels(text) {
  const out = [];
  for (const l of String(text || '').split('\n')) {
    const m = l.match(/^([^\s#-].*?):\s*$/);
    if (m) out.push(unquote(m[1]));
  }
  return out;
}

/**
 * Literal label names in a workflow's github-script: `labels: 'a,b'`,
 * `labels: ['a', 'b']` (create/addLabels/listForRepo), and `add.add('a')`
 * (the triage label sets). `labels: [...add]` carries no literal.
 */
function workflowScriptLabels(text) {
  const src = String(text || '');
  const out = [];
  for (const m of src.matchAll(/\blabels:\s*'([^']+)'/g)) out.push(...splitList(m[1]));
  for (const m of src.matchAll(/\blabels:\s*\[([^\]]*)\]/g)) {
    for (const q of m[1].matchAll(/'([^']+)'|"([^"]+)"/g)) out.push(q[1] || q[2]);
  }
  for (const m of src.matchAll(/\badd\.add\('([^']+)'\)/g)) out.push(m[1]);
  return out;
}

const EXTRACTORS = Object.freeze({
  'issue-form': issueFormLabels,
  stale: staleWorkflowLabels,
  dependabot: dependabotLabels,
  labeler: labelerConfigLabels,
  'workflow-script': workflowScriptLabels,
});

/**
 * @param {'issue-form'|'stale'|'dependabot'|'labeler'|'workflow-script'} kind
 * @param {string} text consumer file contents
 * @returns {string[]} label names referenced, in file order
 */
function extractLabelReferences(kind, text) {
  const fn = EXTRACTORS[kind];
  if (!fn) throw new Error(`unknown label consumer kind ${kind}`);
  return fn(text);
}

/**
 * Check that every referenced label resolves to exactly one taxonomy entry.
 *
 * @param {string} labelsText contents of the taxonomy labels.yml
 * @param {Array<{source: string, name: string}>} references
 * @returns {{ok: boolean, missing: Array<{source: string, name: string}>,
 *   duplicated: Array<{source: string, name: string, count: number}>,
 *   resolved: number}}
 */
function checkLabelClosure(labelsText, references) {
  const counts = new Map();
  for (const { name } of parseLabelLines(labelsText)) counts.set(name, (counts.get(name) || 0) + 1);
  const missing = [];
  const duplicated = [];
  let resolved = 0;
  for (const ref of references) {
    const n = counts.get(ref.name) || 0;
    if (n === 0) missing.push(ref);
    else if (n > 1) duplicated.push({ ...ref, count: n });
    else resolved++;
  }
  return { ok: missing.length === 0 && duplicated.length === 0, missing, duplicated, resolved };
}

module.exports = { parseLabels, parseLabelLines, extractLabelReferences, checkLabelClosure };
