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
 * @param {string} text contents of a labels.yml
 * @returns {Array<{name: string, color: string, description: string}>}
 */
function parseLabels(text) {
  if (typeof text !== 'string') return [];
  const out = [];
  const seen = new Set();
  for (const line of text.split('\n')) {
    if (/^\s*#/.test(line)) continue;
    const name = line.match(/\bname:\s*"([^"]+)"/);
    const color = line.match(/\bcolor:\s*"([^"]+)"/);
    const description = line.match(/\bdescription:\s*"([^"]*)"/);
    if (!name || !color || !description) continue;
    if (seen.has(name[1])) continue;
    seen.add(name[1]);
    out.push({ name: name[1], color: color[1], description: description[1] });
  }
  return out;
}

/**
 * Decide what a repository needs so its labels match the taxonomy.
 *
 * GitHub label names are case-insensitive, so `Bug` and `bug` are one label:
 * a case-only difference is an update (rename), never a second create. Colors
 * compare case-insensitively without a leading `#`. Labels the repository has
 * that the taxonomy does not name are left alone — the sync is additive.
 *
 * Pure, so the sweep can report an exact plan in dry-run and a test can pin it.
 *
 * @param {Array<{name: string, color: string, description?: string|null}>} existing
 *   labels the repository has now (GitHub API shape)
 * @param {Array<{name: string, color: string, description: string}>} desired
 *   the taxonomy, from parseLabels
 * @returns {{
 *   create: Array<{name: string, color: string, description: string}>,
 *   update: Array<{current_name: string, name: string, color: string, description: string}>,
 *   unchanged: string[],
 * }}
 */
function planLabelSync(existing, desired) {
  const byKey = new Map();
  for (const label of existing || []) {
    if (label && typeof label.name === 'string') byKey.set(label.name.toLowerCase(), label);
  }
  const norm = (c) => String(c || '').replace(/^#/, '').toLowerCase();
  const plan = { create: [], update: [], unchanged: [] };
  for (const want of desired || []) {
    const have = byKey.get(want.name.toLowerCase());
    if (!have) {
      plan.create.push({ name: want.name, color: want.color, description: want.description });
      continue;
    }
    const same =
      have.name === want.name &&
      norm(have.color) === norm(want.color) &&
      (have.description || '') === want.description;
    if (same) {
      plan.unchanged.push(want.name);
    } else {
      plan.update.push({
        current_name: have.name,
        name: want.name,
        color: want.color,
        description: want.description,
      });
    }
  }
  return plan;
}

module.exports = { parseLabels, planLabelSync };
