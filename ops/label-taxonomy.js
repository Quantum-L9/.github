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

module.exports = { parseLabels };
