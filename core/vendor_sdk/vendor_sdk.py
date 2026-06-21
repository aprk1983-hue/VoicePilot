"""Vendor Asset SDK — scaffold and validate engineering assets."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from asset_factory import EngineeringAssetFactory
from engineering_assets.asset_types import EngineeringAssetType
from vendor_sdk.asset_templates import MIN_QUALITY_SCORE, PACKAGE_ASSET_TYPES, TEMPLATE_BY_TYPE
from vendor_sdk.id_generator import build_asset_id, slugify_title
from vendor_sdk.markdown_writer import format_asset_markdown, format_package_readme
from vendor_sdk.vendor_catalog import (
    PRODUCT_BY_NAME,
    PRODUCT_BY_SLUG,
    PRODUCTS,
    VENDOR_BY_ID,
    VENDOR_BY_NAME,
    VENDOR_BY_SLUG,
    VENDORS,
)
from vendor_sdk.vendor_models import (
    AssetBlueprint,
    AssetGenerationRequest,
    AssetGenerationResult,
    ProductDefinition,
    VendorDefinition,
    VendorStatistics,
)
from vendor_sdk.yaml_writer import write_asset_yaml


class VendorSdkError(ValueError):
    """Raised when SDK input is invalid."""


class VendorAssetSdk:
    """Vendor-neutral engineering asset scaffolding and validation."""

    def __init__(self, *, factory: EngineeringAssetFactory | None = None) -> None:
        self._factory = factory or EngineeringAssetFactory()
        self._vendors: dict[str, VendorDefinition] = dict(VENDOR_BY_ID)
        self._products: dict[str, ProductDefinition] = {
            product.product_id: product for product in PRODUCTS
        }

    def register_vendor(self, vendor: VendorDefinition) -> None:
        """Register a vendor definition."""
        self._vendors[vendor.vendor_id] = vendor

    def register_product(self, product: ProductDefinition) -> None:
        """Register a product under a vendor."""
        if product.vendor_id not in self._vendors:
            raise VendorSdkError(f"Unknown vendor: {product.vendor_id}")
        self._products[product.product_id] = product

    def list_vendors(self) -> tuple[VendorDefinition, ...]:
        """Return registered vendors sorted by name."""
        return tuple(sorted(self._vendors.values(), key=lambda item: item.name))

    def list_products(self, vendor: str | None = None) -> tuple[ProductDefinition, ...]:
        """Return registered products, optionally filtered by vendor."""
        vendor_def = self._resolve_vendor(vendor) if vendor else None
        products = [
            product
            for product in self._products.values()
            if vendor_def is None or product.vendor_id == vendor_def.vendor_id
        ]
        return tuple(sorted(products, key=lambda item: (item.vendor_id, item.name)))

    def vendor_statistics(self) -> VendorStatistics:
        """Return aggregate catalog statistics."""
        products_by_vendor: dict[str, list[str]] = {}
        for product in self._products.values():
            products_by_vendor.setdefault(product.vendor_id, []).append(product.name)
        return VendorStatistics(
            vendor_count=len(self._vendors),
            product_count=len(self._products),
            vendors=tuple(vendor.name for vendor in self.list_vendors()),
            products_by_vendor={
                vendor_id: tuple(sorted(names))
                for vendor_id, names in sorted(products_by_vendor.items())
            },
        )

    def generate_incident(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate one incident asset."""
        return self._generate_single(request, EngineeringAssetType.INCIDENT)

    def generate_runbook(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate one runbook asset."""
        return self._generate_single(request, EngineeringAssetType.RUNBOOK)

    def generate_verification(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate one verification guide asset."""
        return self._generate_single(request, EngineeringAssetType.VERIFICATION_GUIDE)

    def generate_reference(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate one reference asset."""
        return self._generate_single(request, EngineeringAssetType.REFERENCE)

    def generate_best_practice(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate one best practice asset."""
        return self._generate_single(request, EngineeringAssetType.BEST_PRACTICE)

    def generate_bug_reference(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate one known bug reference asset."""
        return self._generate_single(request, EngineeringAssetType.BUG)

    def generate_package(self, request: AssetGenerationRequest) -> AssetGenerationResult:
        """Generate a full incident package with related assets."""
        vendor = self._resolve_vendor(request.vendor)
        product = self._resolve_product(request.vendor, request.product)
        blueprint = self._build_blueprint(vendor, product, request)
        assets = tuple(
            self._build_asset_dict(
                asset_type=asset_type,
                request=request,
                vendor=vendor,
                product=product,
                blueprint=blueprint,
            )
            for asset_type in PACKAGE_ASSET_TYPES
        )
        return self._finalize_generation(request, blueprint, assets)

    def generate_markdown_documentation(
        self,
        result: AssetGenerationResult,
    ) -> str:
        """Render markdown documentation for generated assets."""
        sections = [format_package_readme(result), ""]
        for asset in result.assets:
            sections.append(format_asset_markdown(asset))
        return "\n".join(sections).strip() + "\n"

    def _generate_single(
        self,
        request: AssetGenerationRequest,
        asset_type: EngineeringAssetType,
    ) -> AssetGenerationResult:
        vendor = self._resolve_vendor(request.vendor)
        product = self._resolve_product(request.vendor, request.product)
        blueprint = self._build_blueprint(vendor, product, request)
        all_assets = tuple(
            self._build_asset_dict(
                asset_type=package_type,
                request=request,
                vendor=vendor,
                product=product,
                blueprint=blueprint,
            )
            for package_type in PACKAGE_ASSET_TYPES
        )
        build_results = self._factory.build_batch(list(all_assets), source="vendor-sdk")
        quality_scores = {
            result.asset.asset_id: result.quality.score for result in build_results
        }
        validation_passed = all(result.validation.valid for result in build_results) and all(
            score >= MIN_QUALITY_SCORE for score in quality_scores.values()
        )
        requested = next(
            asset for asset in all_assets if asset["asset_type"] == asset_type.value
        )

        yaml_files: list[Path] = []
        readme_path: Path | None = None
        output_dir = request.output_dir
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            template = TEMPLATE_BY_TYPE[asset_type]
            path = output_dir / template.filename_suffix
            write_asset_yaml(path, requested)
            yaml_files.append(path)

        return AssetGenerationResult(
            blueprint=blueprint,
            assets=(requested,),
            yaml_files=tuple(yaml_files),
            readme_path=readme_path,
            quality_scores=quality_scores,
            validation_passed=validation_passed,
            generated_at=datetime.now(timezone.utc),
        )

    def _finalize_generation(
        self,
        request: AssetGenerationRequest,
        blueprint: AssetBlueprint,
        assets: tuple[dict[str, Any], ...],
    ) -> AssetGenerationResult:
        build_results = self._factory.build_batch(list(assets), source="vendor-sdk")
        quality_scores = {
            result.asset.asset_id: result.quality.score for result in build_results
        }
        validation_passed = all(result.validation.valid for result in build_results)
        validation_passed = validation_passed and all(
            score >= MIN_QUALITY_SCORE for score in quality_scores.values()
        )

        yaml_files: list[Path] = []
        readme_path: Path | None = None
        output_dir = request.output_dir
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            for asset in assets:
                template = TEMPLATE_BY_TYPE[EngineeringAssetType(str(asset["asset_type"]))]
                path = output_dir / template.filename_suffix
                write_asset_yaml(path, asset)
                yaml_files.append(path)
            readme_path = output_dir / "README.md"
            interim = AssetGenerationResult(
                blueprint=blueprint,
                assets=assets,
                yaml_files=tuple(yaml_files),
                readme_path=readme_path,
                quality_scores=quality_scores,
                validation_passed=validation_passed,
                generated_at=datetime.now(timezone.utc),
            )
            readme_path.write_text(format_package_readme(interim), encoding="utf-8")

        return AssetGenerationResult(
            blueprint=blueprint,
            assets=assets,
            yaml_files=tuple(yaml_files),
            readme_path=readme_path,
            quality_scores=quality_scores,
            validation_passed=validation_passed,
            generated_at=datetime.now(timezone.utc),
        )

    def _build_blueprint(
        self,
        vendor: VendorDefinition,
        product: ProductDefinition,
        request: AssetGenerationRequest,
        asset_types: tuple[EngineeringAssetType, ...] | None = None,
    ) -> AssetBlueprint:
        types = asset_types or PACKAGE_ASSET_TYPES
        asset_ids = {
            asset_type.value: build_asset_id(
                vendor.slug,
                product.slug,
                asset_type,
                request.sequence,
            )
            for asset_type in types
        }
        return AssetBlueprint(
            package_key=slugify_title(request.title),
            vendor=vendor,
            product=product,
            title=request.title,
            asset_ids=asset_ids,
            related_asset_ids=tuple(asset_ids.values()),
        )

    def _build_asset_dict(
        self,
        *,
        asset_type: EngineeringAssetType,
        request: AssetGenerationRequest,
        vendor: VendorDefinition,
        product: ProductDefinition,
        blueprint: AssetBlueprint,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        asset_id = blueprint.asset_ids[asset_type.value]
        category = request.category or product.default_category
        summary = request.summary or f"{request.title} affecting {vendor.name} {product.name}."
        related_ids = [item for item in blueprint.related_asset_ids if item != asset_id]

        base: dict[str, Any] = {
            "asset_id": asset_id,
            "title": self._title_for_type(request.title, asset_type),
            "asset_type": asset_type.value,
            "category": category,
            "vendor": vendor.name,
            "product": product.name,
            "version": "1.0",
            "summary": summary,
            "description": summary,
            "status": "DRAFT",
            "severity": request.severity,
            "tags": [vendor.slug.lower(), product.slug.lower(), "vendor-sdk"],
            "references": list(request.references)
            or [f"{vendor.name} {product.name} product documentation"],
            "related_asset_ids": related_ids,
            "confidence": 0.95,
            "created_at": now,
            "updated_at": now,
            "symptoms": list(request.symptoms) or self._default_symptoms(request.title),
            "expected_findings": list(request.expected_findings)
            or self._default_findings(request.title),
            "expected_hypotheses": list(request.likely_causes)
            or self._default_causes(request.title),
            "known_causes": list(request.likely_causes) or self._default_causes(request.title),
            "known_resolution": list(request.resolution) or self._default_resolution(request.title),
            "recommended_actions": list(request.resolution) or self._default_resolution(request.title),
            "verification_steps": list(request.verification_steps)
            or self._default_verification_steps(request.title),
            "rollback_steps": list(request.rollback) or self._default_rollback(request.title),
            "required_evidence": self._default_required_evidence(product.name),
        }
        return self._apply_type_overrides(base, asset_type, request.title)

    def _apply_type_overrides(
        self,
        base: dict[str, Any],
        asset_type: EngineeringAssetType,
        title: str,
    ) -> dict[str, Any]:
        if asset_type == EngineeringAssetType.RUNBOOK:
            base["recommended_actions"] = list(base["recommended_actions"]) or [
                f"Follow remediation steps for {title}",
            ]
            base["rollback_steps"] = list(base["rollback_steps"]) or [
                "Restore previous configuration from change record",
            ]
        elif asset_type == EngineeringAssetType.VERIFICATION_GUIDE:
            base["required_evidence"] = list(base["required_evidence"])
            base["verification_steps"] = list(base["verification_steps"]) or [
                f"Collect verification output for {title}",
                "Compare results against expected baseline",
            ]
        elif asset_type == EngineeringAssetType.REFERENCE:
            base["references"] = list(base["references"]) + [
                f"{base['vendor']} official documentation for {base['product']}",
            ]
        elif asset_type == EngineeringAssetType.BEST_PRACTICE:
            base["recommended_actions"] = [
                f"Apply best practice guidance for {title}",
                "Document outcome in change record",
            ]
        elif asset_type == EngineeringAssetType.BUG:
            base["known_causes"] = list(base["known_causes"]) or [
                f"Vendor defect affecting {title}",
            ]
            base["known_resolution"] = list(base["known_resolution"]) or [
                "Apply vendor fix or documented workaround",
            ]
        return base

    def _title_for_type(self, title: str, asset_type: EngineeringAssetType) -> str:
        suffix = {
            EngineeringAssetType.INCIDENT: "Incident",
            EngineeringAssetType.RUNBOOK: "Runbook",
            EngineeringAssetType.VERIFICATION_GUIDE: "Verification Guide",
            EngineeringAssetType.REFERENCE: "Reference",
            EngineeringAssetType.BEST_PRACTICE: "Best Practice",
            EngineeringAssetType.BUG: "Known Bug",
        }[asset_type]
        return f"{title} — {suffix}"

    def _default_symptoms(self, title: str) -> list[str]:
        return [
            f"Users report symptoms consistent with {title}",
            "Service degradation observed during troubleshooting window",
        ]

    def _default_findings(self, title: str) -> list[str]:
        slug = slugify_title(title).replace("-", "_")
        return [f"{slug}_detected", "service_degraded"]

    def _default_causes(self, title: str) -> list[str]:
        return [
            f"Misconfiguration related to {title}",
            "Recent change in affected component",
        ]

    def _default_resolution(self, title: str) -> list[str]:
        return [
            f"Validate configuration for {title}",
            "Execute linked runbook and verification guide",
        ]

    def _default_verification_steps(self, title: str) -> list[str]:
        return [
            f"Verify service restored after remediation for {title}",
            "Confirm no new errors in monitoring or logs",
        ]

    def _default_rollback(self, title: str) -> list[str]:
        return [f"Restore previous baseline if remediation for {title} fails validation"]

    def _default_required_evidence(self, product_name: str) -> list[str]:
        return [
            f"Collect {product_name} diagnostic output",
            "Capture configuration excerpt relevant to the issue",
        ]

    def _resolve_vendor(self, vendor: str) -> VendorDefinition:
        key = vendor.strip().lower()
        if key in VENDOR_BY_ID:
            return self._vendors[VENDOR_BY_ID[key].vendor_id]
        if key in VENDOR_BY_NAME:
            return self._vendors[VENDOR_BY_NAME[key].vendor_id]
        if key in VENDOR_BY_SLUG:
            return self._vendors[VENDOR_BY_SLUG[key].vendor_id]
        for registered in self._vendors.values():
            if registered.name.lower() == key or registered.slug.lower() == key:
                return registered
        raise VendorSdkError(f"Unknown vendor: {vendor}")

    def _resolve_product(self, vendor: str, product: str) -> ProductDefinition:
        vendor_def = self._resolve_vendor(vendor)
        product_key = product.strip().lower()
        vendor_key = vendor_def.name.lower()

        candidate = PRODUCT_BY_NAME.get((vendor_key, product_key))
        if candidate is not None:
            return self._products[candidate.product_id]

        candidate = PRODUCT_BY_SLUG.get((vendor_def.slug.lower(), product_key))
        if candidate is not None:
            return self._products[candidate.product_id]

        for registered in self._products.values():
            if registered.vendor_id != vendor_def.vendor_id:
                continue
            if registered.name.lower() == product_key or registered.slug.lower() == product_key:
                return registered
        raise VendorSdkError(f"Unknown product {product!r} for vendor {vendor_def.name}")
