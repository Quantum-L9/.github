# ADR-006: Technology binds after semantic resolution

Status: Accepted

## Decision
Technology intent is declared through `technology_profiles.yaml`; provider facts remain in `technology_capabilities.yaml`; concrete realizations remain in `binding_catalog.yaml`. Binding is admissible only when required capabilities are supported by registered provider facts and applicable compatibility contracts.

```text
RequiredPortCapabilities subset_of ProviderCapabilities
```

Unknown provider capability fails closed. Provider choice does not transfer semantic ownership or alter semantic identity. Preferences may optimize only among compatible realizations.
