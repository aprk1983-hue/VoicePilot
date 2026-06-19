# VoicePilot Plugins

Plugins extend VoicePilot Core with vendor-specific investigation assets and optional providers.

## Architecture

```
┌─────────────────────────────────────────┐
│           VoicePilot Core               │
│  runtime · domain · application         │
└───────────────────┬─────────────────────┘
                    │ SDK contracts
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   plugins/    third-party   marketplace
   (official)   plugins       (future)
```

## Plugin Directory Structure

```
plugins/
  <plugin-name>/
    manifest.yaml          # Required — plugin metadata and entry points
    README.md
    playbooks/             # Optional — .vpb.yaml DSL playbooks
    parsers/               # Optional — future parser modules
    knowledge/             # Optional — future knowledge packs
```

## How Plugins Load (Future)

1. Core scans `plugins/` (and configured extra paths)
2. Reads `manifest.yaml` into `PluginManifest`
3. Instantiates `VoicePilotPlugin` implementation
4. Registers `PlaybookProvider` paths with `PlaybookLoader`
5. Binds playbooks to cases via `PlaybookEngine`

**Current sprint:** manifest + file layout only; dynamic loader is TODO.

## Official Plugins

| Plugin | Path | Status |
|--------|------|--------|
| Cisco Voice | `plugins/cisco/` | MVP — VP-CUBE-0001 |

## Third-Party Plugins

Third-party plugins use the same SDK contracts. They should:

- Never modify `core/` source
- Declare capabilities explicitly in `manifest.yaml`
- Keep playbooks as `.vpb.yaml` per [DSL spec](../docs/dsl/voicepilot-dsl.md)
- Respect evidence-first investigation rules

## Marketplace Concept (Future)

- Certified plugin bundles with version compatibility matrix
- Customer-private plugin registries for air-gapped deployments
- Capability-based discovery: "I need CUBE outbound playbooks"
- Revenue share model for partner-authored plugins

## Related

- [SDK](../sdk/README.md)
- [Cisco plugin](cisco/README.md)
- [DSL specification](../docs/dsl/voicepilot-dsl.md)
