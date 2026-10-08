# Semantic Foundation v3.15.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor admits the L9 repository class and populates the canonical repository registry. Since v3.6.0 the two ledgers `semantics/repository_classes.yaml` and `semantics/repository_registry.yaml` have been registered canonical sources (`l9.source/repository-classes@1`, `l9.source/repository-registry@1`) whose content was an explicit Unknown: each named its coordinate so that projection source classes `repository_classes` and `repository_registry` resolved to one registered ledger, and admitted nothing. Downstream consumers that must derive L9 corpus membership from organization law, the memory plane's repository-corpus projection first among them, had no canonical membership authority to project from.

v3.15.0 closes that Unknown by explicit decision. It admits exactly one RepositoryClass, `l9.repository-class/l9@1`, declares the derived memory-namespace view over it, and registers an explicit census of 32 repositories, each assigned that class. Nothing in this release infers a class or a membership from a repository name, prefix, hosting organization, shape, ProductKind or birth profile: every member is a member because it is listed, and the validator pins the list.

## Bounded delta

- `semantics/repository_classes.yaml`: the placeholder is replaced by the admitted class catalog. It carries the global rules that make repository class explicit and never inferred, the `does_not_own` boundary, the three class statuses, exactly one admitted class (`l9`, id `l9.repository-class/l9@1`, status `current`, `organization_membership: l9`) with its canonical-authority-consumption, projection, identity-materialization, memory and governance obligations, the resolution rule (exactly one `class_ref` resolved through the registry, unresolved or unadmitted class fails closed), and one derived view `l9.repository-view/memory-namespace-l9@1` that selects the l9 class over lifecycles `current`, `superseded` and `retired` and outputs namespace `l9` with `authority_class: derived`, preserving `id`, `coordinate`, `lifecycle` and `class_ref`. `catalog_status.admitted_classes` lists the one admitted class.
- `semantics/repository_registry.yaml`: the placeholder is replaced by the populated registry. It keeps `class_catalog_ref: l9.repository-classes/global@1`, the registry laws (explicit identity, case-sensitive provider-scoped coordinate, immutable id, exactly one `class_ref`, the `current` / `superseded` / `retired` lifecycle, no inferred membership or class, no runtime, ingestion, memory or credential state, non-authoritative generated views), and admits exactly 32 repositories, every one `provider: github`, `organization: Quantum-L9`, `lifecycle: current`, `class_ref: l9.repository-class/l9@1`.
- `scripts/validate-semantics.py`: adds RC-023, the repository class / repository registry closure, with a fail-closed negative-case batch. RC-023 pins the class identity and its memory obligation, the derived view's selector and output, and the exact 32 registry ids and case-sensitive GitHub coordinates.
- `docs/semantic-foundation/v3.15.0/`: this release record.

No other canonical ledger changes. No ledger derives from the two repository ledgers, so no derivation digest is refreshed.

## Non-goals

v3.15.0 adds no invariant, contract, schema, semantic source, authority coordinate, ProductKind, vocabulary term, receipt family or ADR. The canonical ledgers that own this question already exist and are registered; the release fills them. It admits no class other than `l9`: an auxiliary or external-fork class, which earlier design candidates carried, is not needed by this admission and would be a separate explicit decision. It admits no repository outside the 32 listed; in particular `Gate_SDK`, `Constellation.Gate`, `Cognitive.Engine.Graphs`, `Enrichment.Inference.Engine` and `golden-repo` are not admitted here, and a historical candidate entry is not current authority. It does not touch repository birth mechanics, `policies/repo-classes.yml`, seed distribution, or any downstream repository, and it creates no memory record, ingestion state or runtime binding: how the memory plane projects and consumes the derived view is downstream work governed by the view's `authority_class: derived`.

## Authority

`Quantum-L9/.github` owns organization-level repository identity and classification. RepositoryClass is an organization-governance classification; it is orthogonal to ProductKind and birth profile and transfers no domain semantic ownership, execution authority or runtime state. The memory obligation of the l9 class binds membership to the resolved class (`membership_source: resolved_repository_class`); content selection stays with the memory plane, content authority stays with each source repository, and the memory representation is derived, never repository authority. A consumer may not independently add or remove members.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.14.0/` (admission contract / authority-model requirement closure). That release record is unchanged, as is `docs/semantic-foundation/v3.13.0/`.
