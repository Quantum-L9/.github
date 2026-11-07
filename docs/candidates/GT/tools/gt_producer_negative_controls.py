#!/usr/bin/env python3
"""GT producer negative controls against the REAL semantic compiler.

Each control mutates one canonical file of the integrated rehearsal revision in a
throwaway commit (git plumbing; HEAD and the worktree are untouched), asks the
producer for coordinates at that commit, and projects or composes. Every control
names the mechanism it targets and the exit code, typed failure and criterion or
message fragment it must produce; ``mechanism_matched`` is true only when all
three agree. Usage::

    gt_producer_negative_controls.py --authority-root R --revision REV \
        --compiler-src SRC --run1 QUAL/run1 --out results.json
"""

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

GT_PROFILE = "l9.projection/strategic-planner-interaction@1"
GT_COMPOSITION = "l9.compose/strategic-planner-interaction@1"
SCHEMA = "semantics/strategic_interaction_projection.schema.yaml"
FORBIDDEN = "sv_semantic_records_excluded_from_gt_projection"

# control -> (exit code, typed_failure suffix or None, fragment or None)
EXPECT = {
    "positive_control_invariants_projection": (0, None, None),
    "profile_selects_sv_invariant": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        "payload_schema",
    ),
    "profile_selects_sv_invariant_with_schema_widened": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        FORBIDDEN,
    ),
    "profile_selects_sv_vocabulary_term": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        FORBIDDEN,
    ),
    "profile_selects_sv_contract": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        "payload_schema",
    ),
    "profile_selects_sv_contract_with_schema_widened": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        FORBIDDEN,
    ),
    "profile_reverts_to_unregistered_forbidden_tokens": (
        3,
        None,
        "declared_constraint:forbidden:projection_ranking_or_executing",
    ),
    "profile_drops_one_governing_invariant": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        "payload_schema",
    ),
    "governing_invariant_id_renamed": (
        2,
        "INVALID_PROFILE",
        "missing required selector result",
    ),
    "gt_core_contract_id_renamed": (
        2,
        "INVALID_PROFILE",
        "missing required selector result",
    ),
    "vocabulary_definition_removed": (
        2,
        "STRUCTURAL_VALIDATION_FAILED",
        "payload_schema",
    ),
    "projection_schema_discriminator_removed": (3, None, "payload_schema"),
    "profile_digest_mutated": (2, "REVISION_MISMATCH", "profile_digest"),
    "source_digest_mutated": (2, "REVISION_MISMATCH", "source_digest"),
    "composition_missing_namespace": (2, "INVALID_REQUEST", "source_coverage"),
    "composition_duplicate_source": (2, "AMBIGUOUS_SEMANTICS", "duplicate_source"),
    "composition_profile_digest_mutated": (
        2,
        "REVISION_MISMATCH",
        "composition_profile_digest",
    ),
    "artifact_payload_tampered": (2, "REVISION_MISMATCH", "projection_digest"),
    "positive_control_verify_untampered_artifact": (0, None, None),
}


class Runner:
    def __init__(self, root, revision, compiler_src):
        self.root = Path(root).resolve()
        self.revision = revision
        self.env = dict(os.environ, PYTHONPATH=str(Path(compiler_src).resolve()))
        self.results = []

    def cli(self, *args):
        proc = subprocess.run(
            [sys.executable, "-m", "l9_semantic_compiler", *args],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def git(self, *args, **kw):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            check=True,
            **kw,
        ).stdout

    def commit_with(self, path, transform, message, extra=()):
        index = Path(tempfile.mkdtemp()) / "index"
        env = dict(os.environ, GIT_INDEX_FILE=str(index))
        self.git("read-tree", self.revision, env=env)
        for rel, fn in ((path, transform), *extra):
            before = self.git("show", f"{self.revision}:{rel}")
            after = fn(before)
            if after == before:
                raise RuntimeError(f"mutation for {message} did not change {rel}")
            blob = self.git("hash-object", "-w", "--stdin", input=after).strip()
            self.git("update-index", "--cacheinfo", f"100644,{blob},{rel}", env=env)
        tree = self.git("write-tree", env=env).strip()
        cenv = dict(
            os.environ,
            GIT_AUTHOR_NAME="neg",
            GIT_AUTHOR_EMAIL="neg@localhost",
            GIT_COMMITTER_NAME="neg",
            GIT_COMMITTER_EMAIL="neg@localhost",
            GIT_AUTHOR_DATE="2026-11-07T00:00:00Z",
            GIT_COMMITTER_DATE="2026-11-07T00:00:00Z",
        )
        return subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "commit-tree",
                tree,
                "-p",
                self.revision,
                "-m",
                "NEG " + message,
            ],
            capture_output=True,
            text=True,
            check=True,
            env=cenv,
        ).stdout.strip()

    def verify(self, artifact):
        return self.cli(
            "verify-projection",
            "--authority-root",
            str(self.root),
            "--revision",
            self.revision,
            "--repository",
            "Quantum-L9/.github",
            "--artifact",
            str(artifact),
        )

    def coords(self, revision, source_class):
        rc, out, err = self.cli(
            "projection-coordinates",
            "--authority-root",
            str(self.root),
            "--revision",
            revision,
            "--repository",
            "Quantum-L9/.github",
            "--profile",
            GT_PROFILE,
            "--source-class",
            source_class,
        )
        if rc != 0:
            return None, rc, out, err
        request = yaml.safe_load(out)
        request["schema"] = "l9.semantic-projection-request/v1"
        request["authority"]["root"] = str(self.root)
        return request, rc, out, err

    def run_request(self, verb, request):
        with tempfile.TemporaryDirectory() as tmp:
            request = copy.deepcopy(request)
            request["output_root"] = tmp
            path = Path(tmp) / "request.yaml"
            path.write_text(yaml.safe_dump(request), encoding="utf-8")
            return self.cli(verb, str(path))

    def record(self, name, mechanism, rc, out, err):
        try:
            doc = yaml.safe_load(out)
        except yaml.YAMLError:
            doc = None
        doc = doc if isinstance(doc, dict) else {}
        diag = doc.get("diagnostic_coordinates") or {}
        arts = doc.get("artifacts") or []
        unresolved = sorted(
            {c for a in arts for c in (a.get("unresolved_criteria") or [])}
        )
        summary = {
            "status": doc.get("status"),
            "result": doc.get("result"),
            "typed_failure": doc.get("typed_failure"),
            "criterion": diag.get("criterion"),
            "message": diag.get("message"),
            "unresolved_criteria": unresolved,
        }
        want_rc, want_failure, want_fragment = EXPECT[name]
        observed = " ".join(
            [str(summary["criterion"] or ""), str(summary["message"] or "")]
            + [str(summary["typed_failure"] or "")]
            + unresolved
            + [err[-600:]]
        )
        matched = (
            rc == want_rc
            and (
                want_failure is None
                or str(summary["typed_failure"] or "").endswith(want_failure)
            )
            and (want_fragment is None or want_fragment in observed)
        )
        self.results.append(
            {
                "control": name,
                "intended_mechanism": mechanism,
                "exit_code": rc,
                "summary": summary,
                "stderr_tail": err.strip()[-400:],
                "expected": {
                    "exit_code": want_rc,
                    "typed_failure": want_failure,
                    "criterion_or_message": want_fragment,
                },
                "mechanism_matched": matched,
            }
        )

    def mutated_projection(
        self, name, mechanism, path, transform, source_class, extra=()
    ):
        revision = self.commit_with(path, transform, name, extra)
        request, rc, out, err = self.coords(revision, source_class)
        if request is None:
            self.record(name, mechanism, rc, out, err)
            return
        self.record(name, mechanism, *self.run_request("project", request))


def profile_edit(old, new):
    def transform(text):
        if text.count(old) != 1:
            raise RuntimeError(f"profile anchor not unique: {old!r}")
        return text.replace(old, new, 1)

    return transform


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-root", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--compiler-src", required=True)
    parser.add_argument("--run1", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    r = Runner(args.authority_root, args.revision, args.compiler_src)
    run1 = Path(args.run1).resolve()
    pp = "semantics/projection_profiles.yaml"
    sel = '      - $.invariants[?(@.id=="L9-ASSURANCE-001")]\n'
    # The SV profile selects L9-ASSURANCE-001 too; anchor on the GT contract
    # selector that follows it so each edit lands in the GT profile only.
    gt_tail = (
        "    contracts:\n      selectors:\n"
        '      - $.contracts[?(@.id=="l9.contract/strategic-interaction-assessment@1")]\n'
    )

    base = {
        c: yaml.safe_load((run1 / "requests" / f"gt.{c}.request.yaml").read_text())
        for c in ("vocabulary", "invariants", "contracts")
    }
    r.record(
        "positive_control_invariants_projection",
        "none",
        *r.run_request("project", base["invariants"]),
    )
    r.mutated_projection(
        "profile_selects_sv_invariant",
        "forbidden payload_excludes (invariants)",
        pp,
        profile_edit(
            sel + gt_tail,
            sel + '      - $.invariants[?(@.id=="L9-SV-001")]\n' + gt_tail,
        ),
        "invariants",
    )
    r.mutated_projection(
        "profile_selects_sv_vocabulary_term",
        "forbidden payload_excludes (vocabulary)",
        pp,
        profile_edit(
            "      - $.terms.strategic_interaction_assessment\n",
            "      - $.terms.strategic_interaction_assessment\n"
            "      - $.terms.strategic_value\n",
        ),
        "vocabulary",
    )
    r.mutated_projection(
        "profile_selects_sv_contract",
        "forbidden payload_excludes (contracts)",
        pp,
        profile_edit(
            '      - $.contracts[?(@.id=="l9.contract/strategic-interaction-assessment@1")]\n',
            '      - $.contracts[?(@.id=="l9.contract/strategic-interaction-assessment@1")]\n'
            '      - $.contracts[?(@.id=="l9.contract/strategic-value-assessment@1")]\n',
        ),
        "contracts",
    )
    # Same selections with the payload schema widened to admit them, so the
    # forbidden criterion is exercised on its own rather than masked by the
    # schema layer that rejects them first.
    r.mutated_projection(
        "profile_selects_sv_invariant_with_schema_widened",
        "forbidden payload_excludes (invariants), schema layer bypassed",
        pp,
        profile_edit(
            sel + gt_tail,
            sel + '      - $.invariants[?(@.id=="L9-SV-001")]\n' + gt_tail,
        ),
        "invariants",
        extra=(
            (
                SCHEMA,
                profile_edit(
                    "          - L9-ASSURANCE-001\n",
                    "          - L9-ASSURANCE-001\n          - L9-SV-001\n",
                ),
            ),
        ),
    )
    r.mutated_projection(
        "profile_selects_sv_contract_with_schema_widened",
        "forbidden payload_excludes (contracts), schema layer bypassed",
        pp,
        profile_edit(
            '      - $.contracts[?(@.id=="l9.contract/strategic-interaction-assessment@1")]\n',
            '      - $.contracts[?(@.id=="l9.contract/strategic-interaction-assessment@1")]\n'
            '      - $.contracts[?(@.id=="l9.contract/strategic-value-assessment@1")]\n',
        ),
        "contracts",
        extra=(
            (
                SCHEMA,
                lambda text: text.replace(
                    "        id:\n          const: l9.contract/strategic-interaction-assessment@1\n",
                    "        id:\n          type: string\n",
                    1,
                ).replace(
                    "        applicability:\n          type: object\n          required:\n"
                    "          - trigger\n          - does_not_apply_to\n          - sv_dependency\n",
                    "        applicability:\n          type: object\n          required:\n"
                    "          - trigger\n",
                    1,
                ),
            ),
        ),
    )
    r.mutated_projection(
        "profile_reverts_to_unregistered_forbidden_tokens",
        "PROJECTION-016: undeclared criterion stays unresolved",
        pp,
        profile_edit(
            "  forbidden:\n  - " + FORBIDDEN + "\n",
            "  forbidden:\n  - projection_ranking_or_executing\n"
            "  - claiming_unverified_actor_intent_as_fact\n",
        ),
        "contracts",
    )
    r.mutated_projection(
        "profile_drops_one_governing_invariant",
        "native payload schema min_items 6",
        pp,
        profile_edit(sel + gt_tail, gt_tail),
        "invariants",
    )
    r.mutated_projection(
        "governing_invariant_id_renamed",
        "profile selector resolution",
        "semantics/invariants.yaml",
        profile_edit("- id: L9-EVIDENCE-001\n", "- id: L9-EVIDENCE-001-RENAMED\n"),
        "invariants",
    )
    r.mutated_projection(
        "gt_core_contract_id_renamed",
        "profile selector resolution",
        "semantics/contracts.yaml",
        profile_edit(
            "- id: l9.contract/strategic-interaction-assessment@1\n",
            "- id: l9.contract/strategic-interaction-assessment@9\n",
        ),
        "contracts",
    )
    r.mutated_projection(
        "vocabulary_definition_removed",
        "native payload schema required field",
        "semantics/vocabulary.yaml",
        profile_edit(
            "  deviation_gain:\n    semantic_class:",
            "  deviation_gain:\n    semantic_class_removed:",
        ),
        "vocabulary",
    )
    r.mutated_projection(
        "projection_schema_discriminator_removed",
        "output schema discovery (properties.schema.const)",
        "semantics/strategic_interaction_projection.schema.yaml",
        profile_edit(
            "  schema:\n    const: l9.projection.strategic-planner-interaction/v1\n", ""
        ),
        "invariants",
    )

    req = copy.deepcopy(base["invariants"])
    req["projection_profile"]["digest"] = "sha256:" + "0" * 64
    r.record(
        "profile_digest_mutated", "profile currentness", *r.run_request("project", req)
    )
    req = copy.deepcopy(base["invariants"])
    req["sources"][0]["digest"] = "sha256:" + "1" * 64
    r.record(
        "source_digest_mutated", "source currentness", *r.run_request("project", req)
    )

    comp = yaml.safe_load((run1 / "requests" / "gt.compose.request.yaml").read_text())
    c = copy.deepcopy(comp)
    c["components"] = [x for x in c["components"] if "source_vocabulary" not in x]
    r.record(
        "composition_missing_namespace",
        "composition source_coverage exact",
        *r.run_request("compose", c),
    )
    c = copy.deepcopy(comp)
    c["components"] = [*c["components"], c["components"][0]]
    r.record(
        "composition_duplicate_source",
        "duplicate_source conflict",
        *r.run_request("compose", c),
    )
    c = copy.deepcopy(comp)
    c["composition_profile"]["digest"] = "sha256:" + "2" * 64
    r.record(
        "composition_profile_digest_mutated",
        "composition profile currentness",
        *r.run_request("compose", c),
    )

    art = (
        run1
        / "l9.projection_strategic-planner-interaction_1"
        / "l9.source_invariants_1.projection.json"
    )
    with tempfile.TemporaryDirectory() as tmp:
        doc = json.loads(art.read_text())
        doc["payload"]["invariants"] = doc["payload"]["invariants"][:-1]
        bad = Path(tmp) / "tampered.projection.json"
        bad.write_text(json.dumps(doc))
        r.record(
            "artifact_payload_tampered",
            "verify-projection digest",
            *r.verify(bad),
        )
    r.record(
        "positive_control_verify_untampered_artifact",
        "none",
        *r.verify(art),
    )

    out = {
        "schema": "l9.gt.producer-negative-controls/v1",
        "authority_revision": args.revision,
        "controls": r.results,
        "all_matched": all(x["mechanism_matched"] for x in r.results),
        "count": len(r.results),
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for x in r.results:
        print(
            ("MATCH " if x["mechanism_matched"] else "MISMATCH "),
            x["control"],
            x["exit_code"],
            x["summary"]["typed_failure"],
            x["summary"]["criterion"],
            (x["summary"]["message"] or "")[:120],
            x["summary"]["unresolved_criteria"][:2],
            x["stderr_tail"][-200:] if x["exit_code"] not in (0, 2, 3) else "",
        )
    return 0 if out["all_matched"] else 1


if __name__ == "__main__":
    sys.exit(main())
