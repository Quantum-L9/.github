# Authority resolution

| Question | Resolution | Source |
|---|---|---|
| Who owns the target class | Canonical global semantics; `Quantum-L9/.github` owns them and its repository owner holds `target_class_authority`. | `semantics/authority_model.yaml` |
| What admits a release | An explicit decision record (an ADR) plus the release status flip, effective at the `main` commit that merges them. | `authority_model.yaml#admission_rules`; precedent ADR-025 / v3.28.0 (Quantum-L9/.github#211) |
| Owner decisions D1–D5 | Approved by the repository owner, 2026-11-08, in session `session_017xwbxytavCYavKdhRr9a6n`. | `docs/candidates/SV/evidence/admission/owner-decision.yaml` |
| Admission act | "I approve. Admit formally and close it out", same session, 2026-11-08, after the qualified subject was bound (#222 head `c4c4a1d`, `semantics/` tree `251bb3d`). | ADR-029 **Status** and **Subject** |
| Where `required_provenance` gets its meaning (D2) | Catalog declaration `composition_profiles.yaml#provenance_constraints` (`l9.provenance-constraint` v1) plus compiler criteria; the compiler creates no authority. R1 contingency not invoked. | ADR-029 Decision 2; RC-033; compiler #33 |
| What admission covers | The v3.32.0 delta only. v3.29.0, v3.30.0 and v3.31.0 stay merged candidates. | ADR-029 Subject |
| Merge authority | Operator instruction in the same session; `ops/config/merge-authority.json` enforcement `disabled` (Cursor-Governance CANONICAL_LAW §6.2.16). | `merge-ledger.yaml` |

Nothing in this directory sets `approved: true`, flips a status, or accepts an ADR on its own. Each of those happened in the ADR-029 admission commit (`5c7fcc5`) under the owner's instruction, and it took effect at `64d8b85`.
