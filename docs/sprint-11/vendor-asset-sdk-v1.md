# Vendor Asset SDK v1

## Purpose

Sprint 11.5 introduces the **Vendor Asset SDK** — a vendor-neutral scaffolding layer that generates deterministic engineering assets and validates them through the Engineering Asset Factory (EAF²).

The SDK does not perform investigations, invoke AI, or persist data. It produces editable YAML and markdown templates that engineers can refine before publishing to the knowledge library.

## Architecture

```text
Vendor
   │
   ▼
Product
   │
   ▼
Template
   │
   ▼
Vendor Asset SDK
   │
   ▼
Engineering Asset Factory
   │
   ▼
Engineering Assets
   │
   ▼
Knowledge Engine
   │
   ▼
Runtime
```

## Package Layout

| Module | Responsibility |
|--------|----------------|
| `vendor_models.py` | Immutable dataclasses for vendors, products, templates, requests, results |
| `vendor_catalog.py` | Pre-registered vendors and products |
| `asset_templates.py` | Six asset type templates with required fields |
| `id_generator.py` | Deterministic `VP-{VENDOR}-{PRODUCT}-{suffix}` IDs |
| `yaml_writer.py` | YAML serialization |
| `markdown_writer.py` | README and asset markdown |
| `vendor_sdk.py` | `VendorAssetSdk` engine |

## Supported Vendors

Cisco, Microsoft, AudioCodes, Genesys, Ribbon, Oracle, Avaya

Vendor definitions only — no vendor-specific investigation logic.

## Supported Products

| Vendor | Products |
|--------|----------|
| Cisco | CUBE, CUCM, Unity Connection, Expressway, CER, IM&P, UCCX, Webex Calling |
| Microsoft | Teams Phone, Direct Routing, Operator Connect, Calling Plans, Teams Rooms |
| AudioCodes | Mediant SBC, OVOC |
| Genesys | Genesys Cloud |
| Ribbon | Ribbon SBC |
| Oracle | Oracle SBC |

## Asset Templates

Each generated asset includes:

- Unique ID
- Vendor and product
- Category and severity
- Symptoms, expected findings, likely causes
- Resolution, rollback, verification steps
- References and related asset IDs
- Metadata (status, tags, timestamps)

Supported types: Incident, Runbook, Verification Guide, Reference, Best Practice, Known Bug.

## Quality Gate

Every generated asset passes EAF² validation with a quality score of **≥ 95 / 100**.

## SDK Usage

```python
from pathlib import Path

from vendor_sdk import AssetGenerationRequest, VendorAssetSdk

sdk = VendorAssetSdk()
request = AssetGenerationRequest(
    vendor="Cisco",
    product="CUCM",
    title="Phone Registration Failure",
    output_dir=Path("output/cucm-registration"),
)
result = sdk.generate_package(request)

assert result.validation_passed
assert all(score >= 95 for score in result.quality_scores.values())
```

Single-asset generation:

```python
incident = sdk.generate_incident(request)
runbook = sdk.generate_runbook(request)
verification = sdk.generate_verification(request)
```

## CLI

```bash
voicepilot sdk vendors
voicepilot sdk products
voicepilot sdk products --vendor Cisco

voicepilot sdk generate incident \
  --vendor Cisco \
  --product CUCM \
  --title "Phone Registration Failure" \
  --output ./output/incident

voicepilot sdk generate runbook \
  --vendor Cisco \
  --product CUCM \
  --title "Phone Registration Failure" \
  --output ./output/runbook

voicepilot sdk generate verification \
  --vendor Cisco \
  --product CUCM \
  --title "Phone Registration Failure" \
  --output ./output/verification

voicepilot sdk generate package \
  --vendor Cisco \
  --product CUCM \
  --title "Phone Registration Failure" \
  --output ./output/package
```

Package generation produces:

- `incident.yaml`
- `runbook.yaml`
- `verification.yaml`
- `reference.yaml`
- `best_practice.yaml`
- `bug.yaml`
- `README.md`

## Related Tests

- [`../../tests/test_vendor_sdk.py`](../../tests/test_vendor_sdk.py)

## Related Documentation

- [`engineering-asset-factory-v1.md`](engineering-asset-factory-v1.md)
- [`../../architecture/part-3-engines/10-vendor-asset-sdk.md`](../../architecture/part-3-engines/10-vendor-asset-sdk.md)
