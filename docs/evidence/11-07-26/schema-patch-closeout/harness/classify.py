"""PATCH-02: classify retained required/const/enum/min_items constraints of the 20 schemas by basis.
G = governed by the canonical profile/composition/dispatch contract; S = pinned snapshot of selected
data at the recorded coordinates; U = anomaly (neither). Reads files only; derives nothing."""
import json, re, sys, collections, yaml
from pathlib import Path
NAMES = ["authority-resolution","evidence-assessment","semantic-change-context","architecture-break-test",
         "globalization-assessment","work-state-continuity","hard-constraint-context","identity-assurance",
         "strategic-metacognition","strategic-planning-context"]
IDF = re.compile(r'^\$\.(\w+)\[\?\(@\.id=="([^"]+)"\)\]$')
FLD = re.compile(r'^\$\.(\w+)(?:\.(\w+))?$')
root = Path(sys.argv[1])
pcat = yaml.safe_load((root/"semantics/projection_profiles.yaml").read_text())
def selectors(name):
    [p] = [x for x in pcat["projection_profiles"] if x["id"] == f"l9.projection/{name}@1"]
    return {cls: s["selectors"] for cls, s in p["sources"].items()}
def key_info(sels):
    """per root key: ('ids', set) when only id-filter selections, else ('whole'|'subkeys', ...)"""
    info = collections.defaultdict(lambda: {"ids": set(), "whole": False, "sub": set()})
    for s in sels:
        m = IDF.match(s)
        if m: info[m.group(1)]["ids"].add(m.group(2)); continue
        m = FLD.match(s)
        if m:
            if m.group(2): info[m.group(1)]["sub"].add(m.group(2))
            else: info[m.group(1)]["whole"] = True
            continue
        info["__other__"]["whole"] = True
    return info
rows = []
def classify(file, desc, path, depth, kinfo, out):
    """depth = path segments below the source-payload root."""
    if not isinstance(desc, dict): return
    t = desc.get("type")
    rootkey = path[0] if path else None
    ki = kinfo.get(rootkey) if rootkey else None
    idsel = ki is not None and ki["ids"] and not ki["whole"] and not ki["sub"]
    for k in ("const", "enum"):
        if k in desc:
            if depth == 1 and path == ["schema"] and k == "const":
                out.append((file, ".".join(map(str,path)), k, "G", "dispatch: profile output.schema"))
            elif k == "enum" and idsel and depth == 3 and path[-1] == "id":
                ok = set(desc["enum"]) == ki["ids"]
                out.append((file, ".".join(map(str,path)), k, "G" if ok else "U",
                            "profile id-filter selectors" if ok else "enum != selector ids"))
            else:
                out.append((file, ".".join(map(str,path)), k, "S", "observed selected value"))
    if "required" in desc:
        for r in desc["required"] or []:
            if depth == 0 and r in kinfo:
                out.append((file, ".".join(map(str,[*path, r])), "required", "G", "profile selector key"))
            elif depth == 1 and ki and r in ki["sub"]:
                out.append((file, ".".join(map(str,[*path, r])), "required", "G", "profile selector sub-key"))
            else:
                out.append((file, ".".join(map(str,[*path, r])), "required", "S", "observed key presence"))
    if t == "array" and isinstance(desc.get("min_items"), int):
        if idsel and depth == 1:
            ok = desc["min_items"] == len(ki["ids"])
            out.append((file, ".".join(map(str,path)), "min_items", "G" if ok else "S",
                        "count of profile id-filter selectors" if ok else "observed length != selector count"))
        else:
            out.append((file, ".".join(map(str,path)), "min_items", "S", "observed length"))
    for kk, v in (desc.get("properties") or {}).items():
        classify(file, v, [*path, kk], depth + 1, kinfo, out)
    if isinstance(desc.get("items"), dict):
        classify(file, desc["items"], [*path, "[]"], depth + 1, kinfo, out)
out = []
for n in NAMES:
    stem = n.replace("-", "_"); sels = selectors(n)
    allsel = [s for v in sels.values() for s in v]
    p = yaml.safe_load((root/f"semantics/{stem}_projection.schema.yaml").read_text())
    pf = f"semantics/{stem}_projection.schema.yaml"
    classify(pf, {"properties": p["properties"]}, [], 0, key_info(allsel), out)
    c = yaml.safe_load((root/f"semantics/{stem}_composition.schema.yaml").read_text())
    cf = f"semantics/{stem}_composition.schema.yaml"
    for r in c.get("required") or []:
        out.append((cf, r, "required", "G" if r in sels else "U", "composition namespace = declared source class"))
    for ns, d in c["properties"].items():
        if ns == "schema":
            out.append((cf, "schema", "const", "G", "dispatch: composition profile output.schema")); continue
        classify(cf, d, [], 0, key_info(sels.get(ns, [])), [] if False else out)
        # namespace paths are relative; prefix for readability
summary = collections.defaultdict(lambda: collections.Counter())
for f, p, k, cls, why in out: summary[f][(k, cls)] += 1
json.dump({"rows": [dict(zip(("file","path","constraint","class","basis"), r)) for r in out],
           "by_file": {f: {f"{k}:{c}": v for (k, c), v in sorted(cnt.items())} for f, cnt in sorted(summary.items())}},
          open(sys.argv[2], "w"), indent=1)
tot = collections.Counter((k, c) for _, _, k, c, _ in out)
for k in sorted(tot): print(k, tot[k])
print("U rows:", [r for r in out if r[3] == "U"][:20])
