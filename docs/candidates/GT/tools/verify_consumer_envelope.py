#!/usr/bin/env python3
"""Candidate consumer-side verification of a GT+SV assessment envelope.

``schemas/gt_sv_consumer_assessment.candidate.schema.json`` checks shape only: a
syntactically valid ``sha256:`` string authenticates nothing. This verifier
checks what the schema cannot, against producer receipts the consumer holds:

* each semantic-view digest is the ``output.digest`` of a producer receipt for
  exactly that composition, with ``operation: composition`` and ``result: pass``;
* both views were produced at the same canonical repository and revision;
* the numerical result is NOT a projection or composition receipt (semantic
  compilation never executes a valuation or a GT solver), and is a receipt with
  ``operation: numerical_evaluation`` whose inputs name both view digests at the
  same coordinates.

``numerical_evaluation`` is a candidate expectation: no Numerical Reasoning
receipt type is admitted yet, so an evaluated envelope can be verified only once
that owner defines one. This is a candidate consumer check, not a canonical
contract, and grants no authority.
"""

import json
import os
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas/gt_sv_consumer_assessment.candidate.schema.json").read_text()
)
SEMANTIC_OPERATIONS = frozenset({"projection", "composition"})


def _coords(receipt):
    gov = receipt.get("governing_coordinates") or {}
    return gov.get("repository"), gov.get("revision")


def _view(envelope, key, receipts, failures):
    ref, digest = envelope[key]["ref"], envelope[key]["digest"]
    receipt = receipts.get(digest)
    if receipt is None:
        failures.append(f"{key}: no producer receipt outputs {digest}")
        return None
    if receipt.get("operation") != "composition":
        failures.append(f"{key}: receipt operation is {receipt.get('operation')!r}")
    if (
        receipt.get("exact_subject_ref") != ref
        or (receipt.get("output") or {}).get("ref") != ref
    ):
        failures.append(f"{key}: receipt subject does not equal {ref}")
    if receipt.get("result") != "pass":
        failures.append(f"{key}: composition result is {receipt.get('result')!r}")
    return receipt


def verify(envelope, receipts):
    """Return (verdict, failures). ``receipts`` maps output digest -> receipt dict."""
    try:
        jsonschema.validate(envelope, SCHEMA)
    except jsonschema.ValidationError as exc:
        return "invalid", [f"shape: {exc.message}"]
    if envelope["status"] != "evaluated":
        return "not_evaluated", []
    failures = []
    gt = _view(envelope, "gt_semantic_view", receipts, failures)
    sv = _view(envelope, "sv_semantic_view", receipts, failures)
    if gt is not None and sv is not None and _coords(gt) != _coords(sv):
        failures.append(
            f"semantic views at different coordinates: {_coords(gt)} != {_coords(sv)}"
        )
    num = receipts.get(envelope["numerical_result"]["digest"])
    if num is None:
        failures.append("numerical_result: no receipt for referenced digest")
    elif num.get("operation") in SEMANTIC_OPERATIONS:
        failures.append(
            "numerical_result: a semantic projection/composition receipt "
            "does not evidence an executed valuation or GT solver"
        )
    elif num.get("operation") != "numerical_evaluation":
        failures.append(
            f"numerical_result: unrecognised operation {num.get('operation')!r}"
        )
    else:
        used = {i.get("digest") for i in num.get("inputs") or []}
        for key in ("gt_semantic_view", "sv_semantic_view"):
            if envelope[key]["digest"] not in used:
                failures.append(f"numerical_result: inputs omit {key}")
        if gt is not None and _coords(num) != _coords(gt):
            failures.append("numerical_result: coordinates differ from semantic views")
    if envelope["sv_accounting_receipt"]["digest"] not in receipts:
        failures.append("sv_accounting_receipt: no receipt for referenced digest")
    return ("verified" if not failures else "refused"), failures


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 1:
        print("usage: verify_consumer_envelope.py ENVELOPE.json RECEIPT.json...")
        return 2
    base = os.path.realpath(os.getcwd())
    paths = []
    for arg in args:
        resolved = os.path.realpath(arg)
        if os.path.commonpath([base, resolved]) != base:
            print(f"BLOCKED={arg!r} resolves outside the working directory {base}")
            return 2
        paths.append(Path(resolved))
    envelope = json.loads(
        paths[0].read_text()
    )  # NOSONAR S8707: operator CLI path, realpath-confined to the working directory above
    receipts = {}
    for path in paths[1:]:
        receipt = json.loads(
            path.read_text()
        )  # NOSONAR S8707: operator CLI path, realpath-confined to the working directory above
        receipts[(receipt.get("output") or {}).get("digest")] = receipt
    verdict, failures = verify(envelope, receipts)
    print("VERDICT=" + verdict)
    for failure in failures:
        print("FAILURE=" + failure)
    return 0 if verdict in ("verified", "not_evaluated") else 1


if __name__ == "__main__":
    sys.exit(main())
