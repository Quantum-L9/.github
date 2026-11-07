"""PATCH-01: drop min_items declared under type: string_list (ignored by the pinned v1 interpreter).
Line-level edit; proves the parsed result equals the original minus exactly those keys."""
import copy, json, re, sys, yaml
from pathlib import Path
KEY = re.compile(r"^(\s*)min_items:\s*(\d+)\s*$")
def indent(l): return len(l) - len(l.lstrip(" "))
def patch(path):
    lines = Path(path).read_text().splitlines(keepends=True)
    drop = []
    for i, l in enumerate(lines):
        m = KEY.match(l)
        if not m: continue
        ind = len(m.group(1)); sib = []
        j = i - 1
        while j >= 0 and (lines[j].strip()=="" or indent(lines[j]) >= ind):
            if indent(lines[j]) == ind: sib.append(lines[j].strip())
            j -= 1
        j = i + 1
        while j < len(lines) and (lines[j].strip()=="" or indent(lines[j]) >= ind):
            if indent(lines[j]) == ind: sib.append(lines[j].strip())
            j += 1
        if "type: string_list" in sib: drop.append((i, int(m.group(2))))
    return lines, drop
def paths(node, p="$", out=None):
    out = [] if out is None else out
    if isinstance(node, dict):
        if node.get("type") == "string_list" and "min_items" in node:
            out.append((p, node["min_items"]))
        for k, v in node.items():
            if k in ("properties","fields"):
                for kk, vv in (v or {}).items(): paths(vv, f"{p}.{kk}", out)
            elif k == "items": paths(v, f"{p}[*]", out)
    return out
def strip(node):
    if isinstance(node, dict):
        if node.get("type") == "string_list": node.pop("min_items", None)
        for v in node.values(): strip(v)
    elif isinstance(node, list):
        for v in node: strip(v)
ledger = []
for f in sys.argv[1:]:
    before = yaml.safe_load(Path(f).read_text())
    expected = copy.deepcopy(before); strip(expected)
    locs = paths({k: before[k] for k in ("type","properties") if k in before})
    lines, drop = patch(f)
    idx = {i for i, _ in drop}
    new = "".join(l for i, l in enumerate(lines) if i not in idx)
    after = yaml.safe_load(new)
    assert after == expected, f"{f}: parsed result differs from expected strip"
    assert len(drop) == len(locs), (f, len(drop), len(locs))
    Path(f).write_text(new)
    ledger.append({"file": f, "removed": len(drop),
                   "minimums": dict(sorted({str(n): sum(1 for _, x in locs if x == n) for _, n in locs}.items())),
                   "locations": [{"path": p, "min_items": n} for p, n in locs]})
json.dump(ledger, sys.stdout, indent=1)
