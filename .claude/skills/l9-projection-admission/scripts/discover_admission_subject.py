"""Deterministic admission-subject discovery and closure for Quantum-L9/.github semantics.

Compares an exact candidate tree with the admitted base and computes, for the eight kinds the
skill admits (invariants, vocabulary terms, contracts, canonical sources, source classes,
projection profiles, composition profiles, payload schemas):

  identities                  new, changed, removed and unchanged identities per kind
  admission_subjects          new or changed identities: what an owner decision must cover
  revisions                   changed identities whose meaning is redefined on purpose; each
                              must be declared, or it is a silent reinterpretation
  required_dependencies       what each subject depends on, and whether that dependency is
                              admitted (present unchanged at the base) or itself a subject
  changed_derived_coordinates derivation digests and counts that changed (the digest cascade)
  unclassified_changes        changed semantics files no admission kind accounts for

It is read-only. The admitted base defaults to the commit that admitted the highest release
on main whose admission evidence verifies (`--base admitted`); any exact ref may be given.

A reviewed scope declaration (`--declared subject.json`) is then checked against the
discovery: an omitted subject, an undeclared revision, a declared revision that changes
nothing, or a subject dependency that is neither admitted nor in the subject fails closure.

Usage:
  python3 discover_admission_subject.py --checkout REPO [--base admitted|REF]
      [--candidate REF] [--main-ref origin/main] [--declared SUBJECT.json]
      [--write-subject OUT.json]

Exit codes: 0 closure passes, 1 it fails, 2 UNRESOLVED.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

import check_admission_closure as cac

CLOSURE_SCHEMA = "l9.projection-admission-subject-closure/v1"
# Changed identities of these kinds redefine admitted meaning and must be declared.
# Profiles are excluded: an admitted profile version is immutable (PROJECTION-013).
# Canonical sources need a declaration when their registry entry changes; a change to a
# ledger's content is a subject without one, since its items are reviewed as subjects.
REVISION_KINDS = (
    "invariants",
    "vocabulary_terms",
    "contracts",
    "canonical_sources",
    "source_classes",
    "schemas",
)
# Collections a registered source hosts as identities of their own kind; they are removed
# from the source's residual content so an added invariant is not also a changed ledger.
HOSTED = {
    "invariants.yaml": ("invariants",),
    "vocabulary.yaml": ("terms",),
    "contracts.yaml": ("contracts",),
    "projection_profiles.yaml": ("source_classes", "projection_profiles"),
}
# Registry files that are not themselves registered sources, and the parts of each that are
# identities; anything else in them that changes is outside the eight kinds.
REGISTRY_HOSTS = {
    "canonical_sources.yaml": (("sources",),),
    "composition_profiles.yaml": (("profiles",),),
    "generic_compiler_manifest.yaml": (
        ("requires", "artifact_schemas"),
        ("requires", "semantic_catalogs"),
    ),
}


# --------------------------------------------------------------------------- admitted base


def admitted_base(repo: Path, main: cac.Tree) -> dict[str, Any]:
    """The admission commit of the highest release on main whose admission verifies.

    The base is what owners have admitted: a release record nominates it, and only
    `verify_admission_evidence.release_admission` (history plus decision binding) accepts it.
    No admitted release means an empty base: every identity is new.
    """
    import verify_admission_evidence as evidence  # local: it imports check_admission_closure

    tried = []
    for version in reversed(cac.release_versions(main)):
        if cac.release_status(main, version) != "ADMITTED":
            continue
        if cac.accepted_adr(main, version) is None:
            tried.append({"release": version, "reason": "no ADR accepts this version"})
            continue
        proof = evidence.release_admission(repo, main, version)
        if proof["status"] != "pass":
            tried.append({"release": version, "reason": "; ".join(proof["gaps"])})
            continue
        commit = proof["admission_commit"]
        return {
            "release": version,
            "admission_commit": commit,
            "adr": proof["adr"],
            "tree": cac.Tree(repo, commit),
            "tried": tried,
        }
    return {"release": None, "admission_commit": None, "tree": None, "tried": tried}


# --------------------------------------------------------------------------- census


def _strip(
    document: dict[str, Any], paths: tuple[tuple[str, ...], ...]
) -> dict[str, Any]:
    doc = copy.deepcopy(document)
    for path in paths:
        node: Any = doc
        for key in path[:-1]:
            node = node.get(key) if isinstance(node, dict) else None
        if isinstance(node, dict):
            node.pop(path[-1], None)
    return doc


# Inside a `derivation` block, only these leaves are derived coordinates (the digest
# cascade). Anything else there, such as a `rule`, is governing text and stays meaning.
COORDINATE = re.compile(r"(sha256|digest|_count)$")


def _strip_coordinates(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _strip_coordinates(v)
            for k, v in value.items()
            if not COORDINATE.search(k)
        }
    if isinstance(value, list):
        return [_strip_coordinates(v) for v in value]
    return value


def _has_content(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_has_content(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_content(v) for v in value)
    return True


def _without_derivation(value: Any) -> Any:
    """The document with every derivation coordinate removed and everything else kept.

    A derivation block that held nothing but coordinates disappears entirely, so adding
    or rebinding the digest cascade is never a change of meaning.
    """
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k == "derivation":
                stripped = _strip_coordinates(v)
                if _has_content(stripped):
                    out[k] = stripped
            else:
                out[k] = _without_derivation(v)
        return out
    if isinstance(value, list):
        return [_without_derivation(v) for v in value]
    return value


def _coordinates(value: Any, path: str, inside: bool) -> dict[str, Any]:
    found: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}"
            if inside and COORDINATE.search(key):
                found[here] = child
            else:
                found.update(_coordinates(child, here, inside or key == "derivation"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.update(_coordinates(child, f"{path}[{index}]", inside))
    return found


def _derivations(value: Any) -> dict[str, Any]:
    """Every derivation coordinate (digest or count under a `derivation` key) by path."""
    return _coordinates(value, "$", False)


def _by_id(entries: Any, kind: str, problems: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for entry in entries or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        if entry["id"] in out:
            problems.append(f"{kind} {entry['id']} is defined more than once")
        out[entry["id"]] = entry
    return out


class Census:
    """Every identity of the eight kinds in one tree (an absent tree is empty)."""

    def __init__(self, tree: cac.Tree | None) -> None:
        self.tree = tree
        self.problems: list[str] = []
        self.items: dict[str, dict[str, Any]] = {k: {} for k in cac.ITEM_KINDS}
        self.source_paths: dict[str, str] = {}
        self.schema_consts: dict[str, str] = {}
        self.derivations: dict[str, dict[str, Any]] = {}
        self.registry_residue: dict[str, Any] = {}
        self.other_files: dict[str, str] = {}
        if tree is not None:
            self._read(tree)

    def _read(self, tree: cac.Tree) -> None:
        y = tree.yaml_or_empty
        items = self.items
        items["invariants"] = _by_id(
            y("semantics/invariants.yaml").get("invariants"), "invariant", self.problems
        )
        items["vocabulary_terms"] = dict(
            y("semantics/vocabulary.yaml").get("terms") or {}
        )
        items["contracts"] = _by_id(
            y("semantics/contracts.yaml").get("contracts"), "contract", self.problems
        )
        profiles_doc = y("semantics/projection_profiles.yaml")
        items["source_classes"] = dict(profiles_doc.get("source_classes") or {})
        items["projection_profiles"] = _by_id(
            profiles_doc.get("projection_profiles"), "projection profile", self.problems
        )
        items["composition_profiles"] = _by_id(
            y("semantics/composition_profiles.yaml").get("profiles"),
            "composition profile",
            self.problems,
        )
        sources, problems = cac.source_registry(tree)
        self.problems += problems
        for ident, entry in sources.items():
            path = entry.get("path")
            data = tree.read(path) if isinstance(path, str) else None
            content: Any = None
            if data is not None:
                document = cac.parse_yaml_mapping(data, f"{tree.label()}:{path}")
                name = Path(path).name
                self.derivations[path] = _derivations(document)
                residual = _strip(document, tuple((k,) for k in HOSTED.get(name, ())))
                content = cac.digest(_without_derivation(residual))
            items["canonical_sources"][ident] = {"entry": entry, "content": content}
            if isinstance(path, str):
                self.source_paths[path] = ident
        registry = cac.schema_registry(tree)
        self.problems += registry["problems"]
        for name in dict.fromkeys(registry["files"]):
            data = tree.read(f"semantics/{name}")
            items["schemas"][name] = None if data is None else cac.sha_bytes(data)
        for const, names in registry["consts"].items():
            if len(names) == 1:
                self.schema_consts[const] = names[0]
        for name, paths in REGISTRY_HOSTS.items():
            self.registry_residue[name] = cac.digest(
                _strip(y(f"semantics/{name}"), paths)
            )
        accounted = (
            set(self.source_paths)
            | {f"semantics/{n}" for n in items["schemas"]}
            | {f"semantics/{n}" for n in REGISTRY_HOSTS}
        )
        for name in tree.listdir("semantics"):
            rel = f"semantics/{name}"
            if name.endswith(".yaml") and rel not in accounted:
                data = tree.read(rel)
                self.other_files[rel] = None if data is None else cac.sha_bytes(data)

    def record(self, kind: str, ident: str) -> Any:
        return self.items[kind].get(ident)

    def dependencies(self, kind: str, ident: str) -> list[tuple[str, str]]:
        """What one identity needs to resolve, as (kind, id) pairs, in this tree."""
        record = self.record(kind, ident)
        if not isinstance(record, dict):
            return []
        deps: list[tuple[str, str]] = []
        if kind == "contracts":
            deps += [("invariants", r) for r in record.get("source_invariants") or []]
        elif kind == "vocabulary_terms":
            if isinstance(record.get("subtype_of"), str):
                deps.append(("vocabulary_terms", record["subtype_of"]))
            model = record.get("detailed_model")
            if isinstance(model, str):
                deps.append(
                    (
                        "canonical_sources",
                        self.source_paths.get(f"semantics/{model}", model),
                    )
                )
        elif kind == "source_classes":
            artifact = record.get("canonical_artifact")
            if isinstance(artifact, str):
                path = f"semantics/{artifact}"
                deps.append(("canonical_sources", self.source_paths.get(path, path)))
        elif kind in ("projection_profiles", "composition_profiles"):
            if kind == "projection_profiles":
                deps += [("source_classes", c) for c in record.get("sources") or {}]
                if isinstance(record.get("successor_of"), str):
                    deps.append(("projection_profiles", record["successor_of"]))
            else:
                composes = (record.get("composes") or {}).get("projection_profile")
                if isinstance(composes, str):
                    deps.append(("projection_profiles", composes))
            schema = (record.get("output") or {}).get("schema")
            if isinstance(schema, str):
                deps.append(("schemas", self.schema_consts.get(schema, schema)))
        elif kind == "schemas" and self.tree is not None:
            doc = (cac.schema_registry(self.tree)["docs"]).get(ident) or {}
            governed = doc.get("governed_by")
            if isinstance(governed, dict):
                for key, ref in governed.items():
                    target = (
                        "composition_profiles"
                        if key.startswith("composition")
                        else "projection_profiles"
                    )
                    deps.append((target, ref))
        return deps


# --------------------------------------------------------------------------- discovery


def _key(kind: str, ident: str) -> str:
    return f"{kind}:{ident}"


def _revision_needed(kind: str, before: Any, after: Any) -> bool:
    if kind not in REVISION_KINDS:
        return False
    if kind == "canonical_sources":
        return cac.digest(before.get("entry")) != cac.digest(after.get("entry"))
    return True


def discover(repo: Path, base: cac.Tree | None, candidate: cac.Tree) -> dict[str, Any]:
    del repo  # both trees already name the repository
    before = Census(base)
    after = Census(candidate)
    gaps = [f"candidate: {p}" for p in after.problems]
    identities: dict[str, Any] = {}
    subjects: dict[str, list[str]] = {}
    revisions: list[str] = []
    for kind in cac.ITEM_KINDS:
        old, new = before.items[kind], after.items[kind]
        added = sorted(i for i in new if i not in old)
        changed = sorted(
            i for i in new if i in old and cac.digest(old[i]) != cac.digest(new[i])
        )
        removed = sorted(i for i in old if i not in new)
        identities[kind] = {
            "new": added,
            "changed": changed,
            "removed": removed,
            "unchanged": len(new) - len(added) - len(changed),
        }
        subjects[kind] = added + changed
        revisions += [
            _key(kind, i) for i in changed if _revision_needed(kind, old[i], new[i])
        ]
        gaps += [
            f"{kind} {i}: removed from the admitted base; additive admission cannot "
            "remove an admitted identity"
            for i in removed
        ]
        if kind in ("projection_profiles", "composition_profiles"):
            gaps += [
                f"{kind} {i}: admitted and edited in place; an existing version is "
                "immutable (PROJECTION-013), register @N+1"
                for i in changed
            ]
    superseded = [
        {
            "profile": i,
            "successor_of": after.items["projection_profiles"][i]["successor_of"],
        }
        for i in subjects["projection_profiles"]
        if isinstance(after.items["projection_profiles"][i].get("successor_of"), str)
    ]
    dependencies = []
    subject_keys = {_key(k, i) for k in cac.ITEM_KINDS for i in subjects[k]}
    for kind in cac.ITEM_KINDS:
        for ident in subjects[kind]:
            for dep_kind, dep in after.dependencies(kind, ident):
                state = _dependency_state(before, after, dep_kind, dep, subject_keys)
                dependencies.append(
                    {
                        "subject": _key(kind, ident),
                        "dependency": _key(dep_kind, dep),
                        "state": state,
                    }
                )
                if state == "missing":
                    gaps.append(
                        f"{_key(kind, ident)} depends on {_key(dep_kind, dep)}, which "
                        "does not resolve in the candidate"
                    )
    derived = []
    for path in sorted(set(before.derivations) | set(after.derivations)):
        old = before.derivations.get(path, {})
        new = after.derivations.get(path, {})
        derived += [
            {"file": path, "path": at}
            for at in sorted(set(old) | set(new))
            if cac.digest(old.get(at)) != cac.digest(new.get(at))
        ]
    unclassified = sorted(
        rel
        for rel in set(before.other_files) | set(after.other_files)
        if before.other_files.get(rel) != after.other_files.get(rel)
    )
    unclassified += sorted(
        f"semantics/{name} (outside its identity collections)"
        for name in REGISTRY_HOSTS
        if before.registry_residue.get(name) != after.registry_residue.get(name)
        and base is not None
    )
    gaps += [
        f"{rel}: changed outside the eight admission kinds; this skill cannot admit it"
        for rel in unclassified
    ]
    return {
        "schema": CLOSURE_SCHEMA,
        "base": base.ref if base is not None else None,
        "candidate": candidate.ref or "WORKTREE",
        "identities": identities,
        "admission_subjects": subjects,
        "revisions": revisions,
        "superseded": superseded,
        "required_dependencies": dependencies,
        "changed_derived_coordinates": derived,
        "unclassified_changes": unclassified,
        "status": "pass" if not gaps else "fail",
        "gaps": gaps,
        "_before": before,
    }


def _dependency_state(
    before: Census, after: Census, kind: str, ident: str, subjects: set[str]
) -> str:
    if after.record(kind, ident) is None:
        return "missing"
    if _key(kind, ident) in subjects:
        return "subject"
    return "admitted"


def scope_check(
    discovery: dict[str, Any], declared: dict[str, list[str]]
) -> dict[str, Any]:
    """A declared subject is complete and closed against the discovery."""
    gaps = list(discovery["gaps"])
    declared_keys = {_key(k, i) for k in cac.ITEM_KINDS for i in declared[k]}
    discovered = discovery["admission_subjects"]
    omitted = sorted(
        _key(k, i)
        for k in cac.ITEM_KINDS
        for i in discovered[k]
        if _key(k, i) not in declared_keys
    )
    gaps += [
        f"scope closure: {key} is new or changed since the admitted base but omitted "
        "from the subject"
        for key in omitted
    ]
    declared_revisions = set(declared.get("revisions") or [])
    undeclared = sorted(set(discovery["revisions"]) - declared_revisions)
    gaps += [
        f"semantic ownership: {key} redefines an admitted identity without a declared "
        "revision"
        for key in undeclared
    ]
    stale = sorted(declared_revisions - set(discovery["revisions"]))
    gaps += [
        f"semantic ownership: {key} is declared as a revision but does not change an "
        "admitted identity"
        for key in stale
    ]
    before: Census = discovery["_before"]
    changed = {_key(k, i) for k in cac.ITEM_KINDS for i in discovered[k]}
    after_deps = {d["subject"]: [] for d in discovery["required_dependencies"]}
    for d in discovery["required_dependencies"]:
        after_deps[d["subject"]].append(d)
    for key in sorted(declared_keys):
        for dep in after_deps.get(key, []):
            target = dep["dependency"]
            dep_kind, _, dep_id = target.partition(":")
            admitted = (
                before.record(dep_kind, dep_id) is not None and target not in changed
            )
            if dep["state"] == "missing" or (
                not admitted and target not in declared_keys
            ):
                gaps.append(
                    f"semantic closure: {key} depends on {target}, which is neither "
                    "admitted at the base nor in the subject"
                )
    unchanged = sorted(k for k in declared_keys if k not in changed)
    return {
        "status": "pass" if not gaps else "fail",
        "gaps": gaps,
        "omitted": omitted,
        "undeclared_revisions": undeclared,
        "declared_already_admitted": unchanged,
        "discovery": public(discovery),
    }


def public(discovery: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in discovery.items() if not k.startswith("_")}


def subject_document(discovery: dict[str, Any]) -> dict[str, Any]:
    """The generated subject.json: every discovered subject and every revision."""
    doc: dict[str, Any] = {
        "schema": cac.SUBJECT_SCHEMA,
        "description": f"discovered against base {discovery['base']}",
    }
    for kind in cac.ITEM_KINDS:
        if discovery["admission_subjects"][kind]:
            doc[kind] = list(discovery["admission_subjects"][kind])
    if discovery["revisions"]:
        doc["revisions"] = list(discovery["revisions"])
    return doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--base", default="admitted")
    parser.add_argument("--candidate", help="a ref; the working tree when omitted")
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--declared", type=Path)
    parser.add_argument("--write-subject", type=Path)
    args = parser.parse_args(argv)
    try:
        repo = args.checkout.resolve()
        top = cac.run_git(repo, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or top.stdout.strip() != str(repo):
            raise cac.InputError(f"{repo} is not the top of a git checkout")
        if args.base == "admitted":
            base_info = admitted_base(repo, cac.Tree(repo, args.main_ref))
            base = base_info["tree"]
        else:
            base = cac.Tree(repo, args.base)
            base_info = {"release": None, "admission_commit": base.ref}
        candidate = cac.Tree(repo, args.candidate)
        found = discover(repo, base, candidate)
        report: dict[str, Any] = public(found)
        report["admitted_base"] = {k: v for k, v in base_info.items() if k != "tree"}
        if args.declared is not None:
            report["scope"] = scope_check(found, cac.load_subject(args.declared))
            report["scope"].pop("discovery")
            report["status"] = report["scope"]["status"]
        if args.write_subject is not None:
            if not any(found["admission_subjects"].values()):
                raise cac.InputError(
                    "nothing changed since the base; no subject to write"
                )
            args.write_subject.write_text(
                json.dumps(subject_document(found), indent=2) + "\n", encoding="utf-8"
            )
    except cac.InputError as exc:
        print(
            json.dumps(
                {"schema": CLOSURE_SCHEMA, "status": "UNRESOLVED", "reason": str(exc)}
            )
        )
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
