# Strategic Value: six new invariant falsification gates

**Status:** `CANDIDATE_ONLY_NOT_ADMITTED` | **Target baseline:** `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397` | **Donor:** `Quantum-L9/l9-wip#6@fb0ae95620cea0dc3f48aa009056ddb755d69640`.

The original fourteen candidates have been dispositioned separately in [`IRREDUCIBILITY_DISPOSITION.md`](IRREDUCIBILITY_DISPOSITION.md): `SV-001` and `SV-002` remain proposed global invariants; twelve meanings reside conditionally in the model and assessment contract. This review concerns only **six further candidate invariant IDs**, `L9-SV-015..020`, each constrained to an applicable Strategic Value claim.

## Independently executable falsifiers

The six cases are specified in `tests/falsification_cases.json` and run directly with Python's standard library, without any Planner skill, live solver, external data provider, source projection, or GitHub credentials:

```bash
python tests/run_strategic_value_falsifiers.py
python tests/run_strategic_value_falsifiers.py --case SV015
python tests/run_strategic_value_falsifiers.py --case SV016
python tests/run_strategic_value_falsifiers.py --case SV017
python tests/run_strategic_value_falsifiers.py --case SV018
python tests/run_strategic_value_falsifiers.py --case SV019
python tests/run_strategic_value_falsifiers.py --case SV020
python -m unittest discover -s tests -v
```

Each case has an invalid/unsupported **adversarial input**, a **positive control**, an exact expected failure code, and a CLI result. The runner exits nonzero if any negative witness is accepted or any positive control is rejected. It can prove **local contract discriminability only**. It does not establish real-world causality, forecast calibration, model adequacy, numerical provider behavior, or admission.

| Candidate | Executable failure mode | Falsifier | Distinctness from SV-001/SV-002 and existing global law | Owner review disposition |
| --- | --- | --- | --- | --- |
| `L9-SV-015` | Confounded baseline accepted as identified causal effect | `SV015` -> `UNIDENTIFIED_COUNTERFACTUAL` | Comparison inputs alone do not establish causal-world comparability | Pending add vs merge into SV-001 |
| `L9-SV-016` | Counterparty transfers counted toward unauthorized focal utility | `SV016` -> `UNAUTHORIZED_ACTOR_AGGREGATION` | Per-effect deduplication does not define beneficiary/welfare ownership | Pending add |
| `L9-SV-017` | An earlier decision uses a later observation | `SV017` -> `FUTURE_OBSERVATION_LEAK` | Actor uncertainty does not alone enforce policy nonanticipativity | Pending add |
| `L9-SV-018` | Independently scored actions summed despite shared capacity | `SV018` -> `UNJUSTIFIED_JOINT_ADDITIVITY` | Single-effect overlap and joint-action feasibility are different obligations | Pending add |
| `L9-SV-019` | Precise winner asserted across an admissible preference reversal | `SV019` -> `UNSUPPORTED_PRECISE_WINNER` | General Unknown handling lacks the testable decision-flip boundary | Pending add vs specialize existing uncertainty law |
| `L9-SV-020` | Projection PASS plus arithmetic described as independently verified forecast | `SV020` -> `UNSUPPORTED_VERIFIED_METHOD_CLAIM` | Projection provenance cannot attest method execution or applicable model validation | Pending add |

## Required owner admission gates

Review six IDs independently against existing global invariants and domains; reject any that are duplicative or overbroad. The candidate does **not** make false-positive-free falsification of arbitrary real-world numerical claims. After owner review, native `.github` checks and real compiler payload-schema validation must prove the admitted source revisions and projections. A verified execution receipt and applicable, independently reviewable model-validation evidence are required before strong numerical claims, not a universal mathematical proof of empirical model adequacy.

**No remote mutation, PR, release, merge, canonical admission, producer projection, or PASS receipt is claimed.**
