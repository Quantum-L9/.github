# Release record: BLOCKED

Lane B. Stacked on [Quantum-L9/.github#269](https://github.com/Quantum-L9/.github/pull/269) head `fe4084ca80909f2a40e78bf8e5bc89a54753f45b`.

GitHub OIDC can attest the policy bytes. That attestation is not this release. `policies/admission-trust.yaml` on that head has no owner key, and `policies/ADMISSION.yaml` does not exist. This record does not invent a key and does not present a pull-request attestation as a default-branch release.

| Field | Value |
| --- | --- |
| policy_id | `quantum-l9.org-invariants` |
| policy_version | `4.1.0` |
| canonical_repository | `Quantum-L9/.github` |
| canonical_path | `policies/ORG_INVARIANTS.yaml` |
| candidate_head | `fe4084ca80909f2a40e78bf8e5bc89a54753f45b` |
| payload_sha256 | `fdb3a6d45af46f237470671b57873557301f1261679d67c352cda5a81661b59c` |
| status | `BLOCKED` |
| blocker | owner trust root is empty and no default-branch admitted release exists |
