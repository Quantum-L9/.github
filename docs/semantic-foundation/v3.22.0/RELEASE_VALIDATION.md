# Release Validation v3.22.0

Candidate status: **additive successor candidate**.

## RC-030 Architecture intelligence closure

RC-030 proves:

- **Profiles and pins:**
  - `l9.projection/architecture-intelligence@1` exists once; it is consumer-class for `l9-global-architect`, is `successor_of` the observer, emits `l9.projection.architecture-intelligence/v1`, and forbids exactly the three categories. The whole entry is pinned by canonical-JSON sha256 `f4dfd0599742efb66de16d545a2c903a32fd3318d307c419ef51e89933fafec4`.
  - `l9.compose/architecture-intelligence@1` exists once, composes exactly that profile, and emits `l9.composed-projection.architecture-intelligence/v1`. It is pinned at `7b40fe358e3f1496a19389742874de622040fe124cb5139b8343680108df09c1`.
- **Forbidden categories:** every forbidden category has a declared `payload_excludes` or `source_authority` criterion over declared source classes in `l9.forbidden-constraint` v1, and PROJECTION-016 is declared.
- **Schemas:** each output schema is defined by exactly one registered artifact schema. The composed schema requires exactly the declared source classes in declaration order. Each namespace requires and types exactly the sections its source's selectors produce.
- **Placement strategies:** the composition contract declares `deep_merge` and `source_class_namespace` exactly. Every composition profile selects exactly one of them, and only `source_class_namespace` takes `composes`.

The negative batch proves fail-closed behavior at the intended field for **17** cases:
- profile deleted, changed in place, or its successor dropped;
- a forbidden category undefined, given the retired `selection_closure`, or given an undeclared source class;
- criterion language changed; PROJECTION-016 removed;
- composition profile deleted, retargeted, or falling back to deep merge;
- consumer-view given `composes`; the namespace strategy loosened;
- composed schema dropping a namespace, adding one, drifting a section set, or being unregistered.

## Existing closure

SC-001 to SC-010 and RC-001 to RC-029 are unchanged and pass.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.22.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
