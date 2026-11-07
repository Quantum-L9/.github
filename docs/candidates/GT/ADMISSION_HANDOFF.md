# Two-stage .github handoff

**This archive is a candidate. It makes NO GitHub changes and does NOT admit canonical law.**

## Stage 1: GT-alone readiness

1. Freeze exact review PR #212 head and its unchanged canonical main parent; the binder in this archive is pinned to PR #212 head `85531616cee2da94bbb7154418a78537549a4d76` and must fail on drift.
2. Review one proposed GT invariant and twelve GT-only vocabulary definitions against canonical owners and independent evidence; remove any redundant meaning.
3. Inspect `overlays/contracts_gt_core.yaml`, `overlays/projection_profile_additions.yaml`, `overlays/composition_profile_additions.yaml`, and the two `semantics/*.schema.yaml` candidates.
4. The local application script may prepare Stage 1 files on a clean pinned checkout. It never grants admission, pushes, or opens PRs.
5. Run actual `.github` native validators, schema inventory and declared selector-language replay on the exact proposed successor, plus semantic integrity audit and separate authority approval.
6. Verify producer-validated source and composed projection receipts and a real Strategic Planner consumer binding before claiming live consumption.

## Stage 2: GT + SV dependent composition

1. First prove SV's `l9.strategic.value@1`, `l9.contract/strategic-value-assessment@1`, and `l9.projection/strategic-planner-value@1` are admitted at one exact canonical revision.
2. Rebind the authority and apply `overlays/contracts_sv_dependent.yaml` in a **separately authorized successor**. The local preparation script deliberately does not add this dependent contract at Stage 1.
3. The derived GT+SV assessment references one independently computed SV assessment and one GT assessment at comparable coordinates. `schemas/gt_sv_consumer_assessment.candidate.schema.json` is a provisional consumer-envelope proposal, not a registered owner-emitted runtime schema.
4. The compiler composes each profile separately using source-class namespacing: GT (3 sources), SV (5 sources). The generic `l9.compose/consumer-view@1` deep-merge mode is **not** a cross-profile numerical or semantic-unification engine and may conflict on shared source fields. The consumer references both independently verified composed semantic views; the Numerical Reasoning owner then computes one canonical SV valuation over response-conditioned scenarios.
5. Strictly test passive-world equality, a flipped action ranking, repeated effects already booked in SV, joint dependence, incompatible units/horizon, altered model revision, action infeasibility and unsupported equilibrium claims.
6. Confirm consumer selection and authorization remain with the Strategic Planner / applicable strategic authority.

## Structural proof versus native evidence

Local checks in this archive validate YAML/JSON shapes, selector closure on the proposed records, contract relationships and synthetic counterexamples. They do **not** validate the exact current canonical repository's production compiler, the target's full semantic closure, real projection bytes, numerical provider execution, model calibration, formal admission, publication, or downstream deployment.

## PR #212 alignment gate
See `PR212_ALIGNMENT.md`: exact PR head, nine doc blob IDs, repaired canonical `strategic_commitment` collision, and the unchanged main semantic sources. The two GT YAML payload schemas now require PR212-compatible types, but their full owner-native compiler proof remains outstanding.
