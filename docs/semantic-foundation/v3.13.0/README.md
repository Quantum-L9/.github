# Semantic Foundation v3.13.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor declares the canonical authority coordinate `l9.authority/product-admission`. `ProductTopology.admission.authority_ref` is a required `semantic_ref`, and product topologies already name this coordinate there, but no canonical ledger declared it. Every such reference was unresolved.

The coordinate names an authority role. It does not change the meaning of product admission. The decision stays with `applicable_target_class_authority` for the exact subject admitted.

## Bounded delta

- Adds one declaration to `semantics/authority_model.yaml`: `product_admission_authority` (`id: l9.authority/product-admission`), between `product_topology_authority` and `product_manifest_authority`. It is decided by `applicable_target_class_authority`, and its subjects are an exact ProductTopology or an exact product release. It inherits the existing global admission requirements and the existing `admission_rules` and `escalation_rules`, and it forbids self-admission. It implies none of the following: publication, runtime admission, runtime availability, capability invocation authorization, implementation conformance or consumer compatibility.
- Adds `$.product_admission_authority`, `$.admission_rules` and `$.escalation_rules` to the `authority_model` source of `l9.projection/stage-product-topology@1`, so ProductTopology intake receives the declaration and the law it inherits.
- Adds RC-021 to `scripts/validate-semantics.py`. RC-021 is a closure check for this exact coordinate, with a negative-case batch that fails closed.

## Non-goals

v3.13.0 adds no ledger, schema, invariant, contract, receipt family, vocabulary term, ADR or authority class. It does not redefine product admission, change the ProductTopology schema, ProductKind law, identity model, lifecycle model or node archetypes, or create a runtime admission authority. It modifies no downstream consumer. Consumers bind to the coordinate in separate work.

## Authority

`Quantum-L9/.github` owns the global authority model and the meaning of this role. It does not admit products by owning the role. The actual admission decision for an exact subject belongs to the applicable target-class authority (`authority_model.yaml#admission_rules`). The Semantic Compiler does not admit products (`authority_model.yaml#compiler_authority`).

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.12.0/` (Graphiti/Zep technology admission). That release record is unchanged.
