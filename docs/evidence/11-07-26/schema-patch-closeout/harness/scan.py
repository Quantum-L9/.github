import sys, yaml, collections
from pathlib import Path
ENF = {"const","enum","type"}
OBJ = {"required","fields","properties"}
ARR = {"min_items","items"}
META = {"description"}
def walk(d, path, out, fname):
    if not isinstance(d, dict): return
    t = d.get("type")
    for k in d:
        ok = k in ENF or k in META or (t=="object" and k in OBJ) or (t=="array" and k in ARR)
        # items without type but with required is handled specially (array items)
        if not ok:
            out.append((fname, path, t, k, d[k] if k=="min_items" else None))
    if t=="object" or (t is None and "properties" in d):
        props = d.get("fields") if d.get("fields") is not None else d.get("properties", {})
        for kk, v in (props or {}).items():
            walk(v, f"{path}.{kk}", out, fname)
    if t=="array" and isinstance(d.get("items"), dict):
        it=d["items"]
        if "type" not in it and "required" in it:
            out.append((fname, path+"[]", None, "items-without-type(only required checked)", None))
        else:
            walk(it, path+"[]", out, fname)
root=Path(sys.argv[1])
files=[f for f in sys.argv[2:]]
out=[]
for f in files:
    doc=yaml.safe_load((root/f).read_text())
    top={k:v for k,v in doc.items() if k in("type","properties","required","fields")}
    walk(top,"$",out,f)
c=collections.Counter((o[0],o[2],o[3]) for o in out)
for k,v in sorted(c.items()): print(v,*k)
