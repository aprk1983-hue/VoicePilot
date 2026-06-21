"""Tests for the Vendor Asset SDK."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from asset_factory import EngineeringAssetFactory
from cli.voicepilot_cli import (
    main,
    run_sdk_generate,
    run_sdk_products,
    run_sdk_vendors,
)
from vendor_sdk import (
    AssetGenerationRequest,
    MIN_QUALITY_SCORE,
    ProductDefinition,
    VendorAssetSdk,
    VendorDefinition,
    VendorSdkError,
)
from vendor_sdk.yaml_writer import load_asset_yaml


def _package_request(**overrides: object) -> AssetGenerationRequest:
    data = {
        "vendor": "Cisco",
        "product": "CUCM",
        "title": "Phone Registration Failure",
    }
    data.update(overrides)
    return AssetGenerationRequest(**data)  # type: ignore[arg-type]


class TestVendorRegistration:
    def test_pre_registered_vendors(self) -> None:
        sdk = VendorAssetSdk()
        names = {vendor.name for vendor in sdk.list_vendors()}
        assert names == {
            "Avaya",
            "AudioCodes",
            "Cisco",
            "Genesys",
            "Microsoft",
            "Oracle",
            "Ribbon",
        }

    def test_register_vendor(self) -> None:
        sdk = VendorAssetSdk()
        vendor = VendorDefinition("acme", "Acme", "ACME", "Acme test vendor")
        sdk.register_vendor(vendor)
        assert any(item.name == "Acme" for item in sdk.list_vendors())

    def test_vendor_statistics(self) -> None:
        sdk = VendorAssetSdk()
        stats = sdk.vendor_statistics()
        assert stats.vendor_count == 7
        assert stats.product_count == 18
        assert "Cisco" in stats.vendors


class TestProductRegistration:
    def test_pre_registered_cisco_products(self) -> None:
        sdk = VendorAssetSdk()
        products = sdk.list_products("Cisco")
        names = {product.name for product in products}
        assert "CUCM" in names
        assert "CUBE" in names
        assert "Webex Calling" in names

    def test_register_product(self) -> None:
        sdk = VendorAssetSdk()
        vendor = VendorDefinition("acme", "Acme", "ACME", "Acme test vendor")
        sdk.register_vendor(vendor)
        product = ProductDefinition(
            "acme-widget",
            "acme",
            "Widget",
            "WIDGET",
            "GENERAL",
            "Acme widget",
        )
        sdk.register_product(product)
        products = sdk.list_products("Acme")
        assert len(products) == 1
        assert products[0].name == "Widget"

    def test_register_product_unknown_vendor_raises(self) -> None:
        sdk = VendorAssetSdk()
        product = ProductDefinition("orphan", "missing", "Orphan", "ORPHAN")
        with pytest.raises(VendorSdkError, match="Unknown vendor"):
            sdk.register_product(product)

    def test_unknown_vendor_raises(self) -> None:
        sdk = VendorAssetSdk()
        with pytest.raises(VendorSdkError, match="Unknown vendor"):
            sdk.list_products("NotAVendor")


class TestPackageGeneration:
    def test_generate_package_returns_six_assets(self) -> None:
        sdk = VendorAssetSdk()
        result = sdk.generate_package(_package_request())
        assert len(result.assets) == 6
        assert result.validation_passed is True

    def test_generate_package_unique_ids(self) -> None:
        sdk = VendorAssetSdk()
        result = sdk.generate_package(_package_request())
        asset_ids = [str(asset["asset_id"]) for asset in result.assets]
        assert len(asset_ids) == len(set(asset_ids))
        assert asset_ids[0] == "VP-CISCO-CUCM-000001"
        assert "VP-CISCO-CUCM-RB-001" in asset_ids
        assert "VP-CISCO-CUCM-VG-001" in asset_ids
        assert "VP-CISCO-CUCM-REF-001" in asset_ids
        assert "VP-CISCO-CUCM-BP-001" in asset_ids
        assert "VP-CISCO-CUCM-BUG-001" in asset_ids

    def test_generate_package_quality_scores(self) -> None:
        sdk = VendorAssetSdk()
        result = sdk.generate_package(_package_request())
        assert result.quality_scores
        assert all(score >= MIN_QUALITY_SCORE for score in result.quality_scores.values())

    def test_generate_package_relationships(self) -> None:
        sdk = VendorAssetSdk()
        result = sdk.generate_package(_package_request())
        build_results = EngineeringAssetFactory().build_batch(
            list(result.assets),
            source="vendor-sdk-test",
        )
        relationships = EngineeringAssetFactory().build_relationships(
            [item.asset for item in build_results]
        )
        assert len(relationships) >= 5
        incident = next(asset for asset in result.assets if asset["asset_type"] == "INCIDENT")
        related = set(incident["related_asset_ids"])
        assert "VP-CISCO-CUCM-RB-001" in related
        assert "VP-CISCO-CUCM-VG-001" in related

    def test_generate_package_writes_files(self, tmp_path: Path) -> None:
        sdk = VendorAssetSdk()
        request = _package_request(output_dir=tmp_path / "cucm-package")
        result = sdk.generate_package(request)
        assert result.readme_path is not None
        assert result.readme_path.exists()
        assert len(result.yaml_files) == 6
        for path in result.yaml_files:
            assert path.exists()
            loaded = load_asset_yaml(path)
            assert loaded["asset_id"]
            assert loaded["vendor"] == "Cisco"
            assert loaded["product"] == "CUCM"


class TestSingleAssetGeneration:
    @pytest.mark.parametrize(
        ("method_name", "asset_type", "filename"),
        [
            ("generate_incident", "INCIDENT", "incident.yaml"),
            ("generate_runbook", "RUNBOOK", "runbook.yaml"),
            ("generate_verification", "VERIFICATION_GUIDE", "verification.yaml"),
            ("generate_reference", "REFERENCE", "reference.yaml"),
            ("generate_best_practice", "BEST_PRACTICE", "best_practice.yaml"),
            ("generate_bug_reference", "BUG", "bug.yaml"),
        ],
    )
    def test_single_asset_generation(
        self,
        method_name: str,
        asset_type: str,
        filename: str,
        tmp_path: Path,
    ) -> None:
        sdk = VendorAssetSdk()
        request = _package_request(output_dir=tmp_path / method_name)
        generator = getattr(sdk, method_name)
        result = generator(request)
        assert len(result.assets) == 1
        assert result.assets[0]["asset_type"] == asset_type
        assert result.validation_passed is True
        assert result.quality_scores
        assert all(score >= MIN_QUALITY_SCORE for score in result.quality_scores.values())
        assert len(result.yaml_files) == 1
        assert result.yaml_files[0].name == filename


class TestYamlValidity:
    def test_generated_yaml_is_valid(self, tmp_path: Path) -> None:
        sdk = VendorAssetSdk()
        request = _package_request(output_dir=tmp_path / "yaml-check")
        result = sdk.generate_package(request)
        for path in result.yaml_files:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            assert isinstance(payload, dict)
            assert payload["asset_id"]
            assert payload["title"]
            assert payload["vendor"]
            assert payload["product"]


class TestFactoryValidation:
    def test_factory_build_batch_passes(self) -> None:
        sdk = VendorAssetSdk()
        result = sdk.generate_package(_package_request())
        build_results = EngineeringAssetFactory().build_batch(
            list(result.assets),
            source="vendor-sdk-test",
        )
        assert all(item.validation.valid for item in build_results)
        assert all(item.quality.score >= MIN_QUALITY_SCORE for item in build_results)


class TestCli:
    def test_cli_vendors(self) -> None:
        output: list[str] = []
        assert run_sdk_vendors(output.append) == 0
        text = "\n".join(output)
        assert "Cisco" in text
        assert "Total vendors: 7" in text

    def test_cli_products(self) -> None:
        output: list[str] = []
        assert run_sdk_products(output.append, vendor="Cisco") == 0
        text = "\n".join(output)
        assert "CUCM" in text

    def test_cli_products_all(self) -> None:
        output: list[str] = []
        assert run_sdk_products(output.append) == 0
        assert "Total products: 18" in "\n".join(output)

    def test_cli_generate_package(self, tmp_path: Path) -> None:
        output: list[str] = []
        request = _package_request(output_dir=tmp_path / "cli-package")
        assert run_sdk_generate("package", output.append, request) == 0
        text = "\n".join(output)
        assert "Validation: PASS" in text
        assert (tmp_path / "cli-package" / "README.md").exists()

    def test_main_sdk_commands(self, tmp_path: Path) -> None:
        assert main(["sdk", "vendors"]) == 0
        assert main(["sdk", "products", "--vendor", "Cisco"]) == 0
        assert (
            main(
                [
                    "sdk",
                    "generate",
                    "package",
                    "--vendor",
                    "Cisco",
                    "--product",
                    "CUCM",
                    "--title",
                    "Phone Registration Failure",
                    "--output",
                    str(tmp_path / "main-package"),
                ]
            )
            == 0
        )
        assert (tmp_path / "main-package" / "incident.yaml").exists()

    def test_main_generate_incident(self, tmp_path: Path) -> None:
        assert (
            main(
                [
                    "sdk",
                    "generate",
                    "incident",
                    "--vendor",
                    "Microsoft",
                    "--product",
                    "Teams Phone",
                    "--title",
                    "One-way audio",
                    "--output",
                    str(tmp_path / "incident"),
                ]
            )
            == 0
        )
        assert (tmp_path / "incident" / "incident.yaml").exists()
