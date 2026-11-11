#!/usr/bin/env python3
"""Run the admission skill's downstream stage on the v3.36.0 candidate; admits nothing.

This calls `downstream()` from `.claude/skills/l9-projection-admission/scripts/
check_admission_closure.py` unchanged: the real `l9-semantic-compiler-engine`
producer projects and composes every profile of the subject twice at this
checkout's HEAD, `verify_admission_evidence.verify_outputs` re-verifies every
emitted byte against the authority tree and runs the negative controls, and
the two runs are compared byte for byte.

It does not call the gate's `evaluate()`, which also shells out to
`make validate check test`; those gates run separately (CI owns `make test`).
The verdict ceiling for a candidate is a rehearsal: DOWNSTREAM_USABLE needs
admission and HEAD == main. Wording: "rehearsal PASS at <sha>, not admitted".

    python3 docs/candidates/domain-projection-architecture-v1/tools/run_downstream_rehearsal.py \
        --compiler-src <clean l9-semantic-compiler-engine checkout> \
        --compiler-revision <sha> --output-root <new scratch directory> [--emit]

`--emit` writes `evidence/downstream/report.json` (machine-local paths
replaced) and copies the run-1 outputs, without the gate's own requests,
to `evidence/downstream/run-1/`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACK = ROOT / "docs/candidates/domain-projection-architecture-v1"
SCRIPTS = ROOT / ".claude/skills/l9-projection-admission/scripts"


def _scrub(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, dict):
        return {k: _scrub(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, replacements) for v in value]
    if isinstance(value, str):
        for old, new in replacements.items():
            value = value.replace(old, new)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--compiler-src", type=Path, required=True)
    parser.add_argument("--compiler-revision", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--subject", type=Path, default=PACK / "evidence/subject.json")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(SCRIPTS))
    import check_admission_closure as gate

    subject = (
        gate.load_subject(args.subject)
        if hasattr(gate, "load_subject")
        else json.loads(args.subject.read_text("utf-8"))
    )
    output_root = args.output_root.resolve()
    compiler = args.compiler_src.resolve()
    report = gate.downstream(
        ROOT, compiler, output_root, subject, args.compiler_revision
    )
    report = _scrub(
        report,
        {
            str(output_root): "<output-root>",
            str(compiler): "<compiler-src>",
            str(ROOT): "<authority-checkout>",
        },
    )
    report = {
        "schema": "l9.candidate-evidence/domain-projection-downstream-rehearsal-v1",
        "admission": "not_granted",
        "wording": f"rehearsal {report.get('status')} at {report.get('revision')}, not admitted",
        "verdict_ceiling": "rehearsal; DOWNSTREAM_USABLE requires ADMITTED and HEAD == main",
        "gate_function": ".claude/skills/l9-projection-admission/scripts/check_admission_closure.py#downstream",
        "subject_file": str(args.subject.resolve().relative_to(ROOT)),
        "downstream": report,
    }
    text = json.dumps(report, indent="\t", sort_keys=True) + "\n"
    print(json.dumps({k: report[k] for k in ("wording", "admission")}, indent=1))
    print(
        json.dumps(
            {
                k: v
                for k, v in report["downstream"].items()
                if k in ("status", "revision", "reason")
            },
            indent=1,
        )
    )
    if args.emit:
        out = PACK / "evidence/downstream"
        if out.exists():
            shutil.rmtree(out)
        (out / "run-1").mkdir(parents=True)
        (out / "report.json").write_text(text, "utf-8")
        run = output_root / "run-1"
        for path in sorted(
            p
            for p in run.rglob("*")
            if p.is_file() and "requests" not in p.relative_to(run).parts
        ):
            target = out / "run-1" / path.relative_to(run)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        print(
            f"emitted {sum(1 for p in (out / 'run-1').rglob('*') if p.is_file())} run-1 files and report.json"
        )
    return 0 if report["downstream"].get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
