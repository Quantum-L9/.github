# Release record: BLOCKED

Lane B. Stacked on [Quantum-L9/.github#269](https://github.com/Quantum-L9/.github/pull/269) head `ec3f5c6734530a3a90438a80827ebd8edd876734`.

No in-toto layout, cosign, sigstore, or policy-release signer exists on `.github` main `00500268eb24de29a5e647a447d6f992d609f6f5`. This record does not invent one and does not present an unsigned artifact as a blocking release.

Consumers may pin the candidate head above. They must treat a missing signature as critical UNKNOWN, not as a green skip. The owner admission is also still open: `policies/DECISION_RECORD.md` on that head says the decision-record schema is undefined.

| Field | Value |
| --- | --- |
| policy_id | `quantum-l9.org-invariants` |
| policy_version | `4.1.0` |
| canonical_repository | `Quantum-L9/.github` |
| canonical_path | `policies/ORG_INVARIANTS.yaml` |
| candidate_head | `ec3f5c6734530a3a90438a80827ebd8edd876734` |
| payload_sha256 | `fdb3a6d45af46f237470671b57873557301f1261679d67c352cda5a81661b59c` |
| status | `BLOCKED` |
| blocker | no signer or in-toto layout on the source pin |
