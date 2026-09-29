# ADR-005: Capability, architecture, and port resolution form one semantic chain

Status: Accepted

## Decision
Desired capabilities resolve into a capability closure. Requirement and capability closure derive architecture obligations. Architecture obligations compose admitted patterns. Architecture then determines required provider-neutral ports.

```text
DesiredCapabilities -> CapabilityClosure -> ArchitectureObligations -> ArchitectureIR -> PortIR
```

Concrete technology selection is prohibited before the semantic requirements and port obligations are known. Provider APIs never define canonical port identity.
