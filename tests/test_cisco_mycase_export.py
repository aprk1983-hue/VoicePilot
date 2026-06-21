"""Tests for the Cisco MyCase PDF Export Assistant."""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = REPO_ROOT / "tools" / "cisco_mycase_export"


def _load_export_module() -> ModuleType:
    path = TOOL_DIR / "export_cases.py"
    spec = importlib.util.spec_from_file_location("cisco_mycase_export", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["cisco_mycase_export"] = module
    spec.loader.exec_module(module)
    return module


export_cases = _load_export_module()


def _mock_page_with_controls(
    controls: list[tuple[str, bool]],
    *,
    frames: list[MagicMock] | None = None,
) -> MagicMock:
    """Build a Playwright page mock with visible controls."""
    page = MagicMock()
    control_mocks: list[MagicMock] = []

    for text, visible in controls:
        control = MagicMock()
        control.is_visible.return_value = visible
        control.inner_text.return_value = text
        control.text_content.return_value = text
        control_mocks.append(control)

    controls_locator = MagicMock()
    controls_locator.count.return_value = len(control_mocks)
    controls_locator.nth.side_effect = lambda index: control_mocks[index]

    def _locator(selector: str) -> MagicMock:
        if selector == export_cases.CONTROL_SELECTOR:
            return controls_locator
        fallback = MagicMock()
        fallback.count.return_value = 0
        return fallback

    page.locator.side_effect = _locator
    page.content.return_value = "<html><body>Case page</body></html>"
    page.url = "https://example.test/case/6991234567"
    page.title.return_value = "Case Detail"
    page.inner_text.return_value = "Case page body"
    page.frames = frames or []
    page.main_frame = page
    page.wait_for_load_state.return_value = None
    page.wait_for_timeout.return_value = None
    return page


def _mock_frame_with_controls(controls: list[tuple[str, bool]]) -> MagicMock:
    frame = _mock_page_with_controls(controls)
    frame.url = "https://example.test/iframe/case"
    return frame


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    output_dir = tmp_path / "exports" / "cisco_mycase"
    output_dir.mkdir(parents=True)
    return output_dir


class TestParseCaseList:
    def test_parse_csv_case_list(self, tmp_path: Path) -> None:
        case_list = tmp_path / "SCMCaseList.csv"
        case_list.write_text(
            "Case Number,Title,Status\n"
            "6991234567,Phone issue,Open\n"
            "6991234568,SIP trunk,Closed\n"
            "6991234567,Duplicate row,Open\n",
            encoding="utf-8",
        )

        case_numbers = export_cases.parse_case_list(case_list)

        assert case_numbers == ["6991234567", "6991234568"]

    def test_parse_csv_with_bom(self, tmp_path: Path) -> None:
        case_list = tmp_path / "cases.csv"
        case_list.write_bytes(
            b"\xef\xbb\xbfCase #,Subject\n"
            b"6881111111,Registration failure\n"
        )

        assert export_cases.parse_case_list(case_list) == ["6881111111"]

    def test_parse_xlsx_case_list(self, tmp_path: Path) -> None:
        openpyxl = pytest.importorskip("openpyxl")
        from openpyxl import Workbook

        case_list = tmp_path / "SCMCaseList.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Case Number", "Title"])
        sheet.append(["6992222222", "Direct Routing"])
        sheet.append(["6993333333", "License"])
        workbook.save(case_list)

        assert export_cases.parse_case_list(case_list) == ["6992222222", "6993333333"]
        assert openpyxl is not None

    def test_parse_case_list_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            export_cases.parse_case_list(tmp_path / "missing.csv")


class TestResumeBehavior:
    def test_skip_already_downloaded_case(self, tmp_output: Path) -> None:
        manifest = export_cases.ExportManifest(
            case_list="SCMCaseList.csv",
            output_dir=str(tmp_output),
        )
        pdf_path = export_cases.pdf_path_for_case(tmp_output, "6991234567")
        pdf_path.write_bytes(b"%PDF-1.4")

        assert export_cases.should_skip_case(
            "6991234567",
            tmp_output,
            manifest,
            resume=True,
        )
        assert not export_cases.should_skip_case(
            "6991234567",
            tmp_output,
            manifest,
            resume=False,
        )

    def test_resume_does_not_skip_failed_without_pdf(self, tmp_output: Path) -> None:
        manifest = export_cases.ExportManifest(
            case_list="SCMCaseList.csv",
            output_dir=str(tmp_output),
        )
        export_cases.record_manifest_entry(
            manifest,
            export_cases.ExportManifestEntry(
                case_number="6991234567",
                status="failed",
                error="Export button not found",
            ),
        )

        assert not export_cases.should_skip_case(
            "6991234567",
            tmp_output,
            manifest,
            resume=True,
        )


class TestExportManifest:
    def test_generate_export_manifest(self, tmp_output: Path) -> None:
        manifest = export_cases.build_manifest(
            case_list=Path("SCMCaseList.xlsx"),
            output_dir=tmp_output,
        )
        export_cases.record_manifest_entry(
            manifest,
            export_cases.ExportManifestEntry(
                case_number="6991234567",
                status="success",
                pdf_path=str(tmp_output / "6991234567.pdf"),
            ),
        )
        export_cases.record_manifest_entry(
            manifest,
            export_cases.ExportManifestEntry(
                case_number="6991234568",
                status="failed",
                html_path=str(tmp_output / "6991234568.html"),
                screenshot_path=str(tmp_output / "6991234568.png"),
                error="Export button not found",
            ),
        )

        manifest_path = export_cases.manifest_path(tmp_output)
        export_cases.save_manifest(manifest, manifest_path)

        loaded = export_cases.load_manifest(manifest_path)
        assert loaded is not None
        assert loaded.entries["6991234567"].status == "success"
        assert loaded.entries["6991234568"].status == "failed"
        assert loaded.entries["6991234568"].error == "Export button not found"

        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert payload["case_list"].endswith("SCMCaseList.xlsx")
        assert "6991234567" in payload["entries"]


class TestFailureLogging:
    def test_failure_entry_when_export_button_missing(self, tmp_output: Path) -> None:
        page = _mock_page_with_controls([("Close Case", True)])

        def _write_screenshot(*, path: str, full_page: bool) -> None:
            Path(path).write_bytes(b"png")

        page.screenshot.side_effect = _write_screenshot
        logger = logging.getLogger("test.cisco_mycase_export")

        entry = export_cases.export_case_with_browser(
            page,
            case_number="6991234567",
            output_dir=tmp_output,
            case_url_template="https://example.test/case/{case_number}",
            logger=logger,
            export_retry_count=1,
            case_load_wait_ms=0,
        )

        assert entry.status == "failed"
        assert entry.error is not None
        assert entry.debug_dump is not None
        assert entry.debug_dump["url"] == "https://example.test/case/6991234567"
        assert "Export control not found" in entry.error
        assert Path(entry.html_path).exists()
        assert Path(entry.screenshot_path).exists()
        page.screenshot.assert_called_once()

    def test_success_entry_on_download(self, tmp_output: Path) -> None:
        page = _mock_page_with_controls([("Export", True)])

        download = MagicMock()
        download_manager = MagicMock()
        download_manager.__enter__.return_value = download_manager
        download_manager.__exit__.return_value = None
        download_manager.value = download
        page.expect_download.return_value = download_manager

        logger = logging.getLogger("test.cisco_mycase_export.success")
        entry = export_cases.export_case_with_browser(
            page,
            case_number="6999999999",
            output_dir=tmp_output,
            case_url_template="https://example.test/case/{case_number}",
            logger=logger,
            export_retry_count=1,
            case_load_wait_ms=0,
        )

        assert entry.status == "success"
        assert entry.pdf_path == str(tmp_output / "6999999999.pdf")
        download.save_as.assert_called_once_with(str(tmp_output / "6999999999.pdf"))
        page.locator(export_cases.CONTROL_SELECTOR).nth(0).click.assert_called_once()
        page.expect_download.assert_called_once()


class TestHelpers:
    def test_normalize_case_number(self) -> None:
        assert export_cases.normalize_case_number(" 6991234567 ") == "6991234567"
        assert export_cases.normalize_case_number(6991234567.0) == "6991234567"
        assert export_cases.normalize_case_number("") is None

    def test_build_case_url(self) -> None:
        url = export_cases.build_case_url(
            "6991234567",
            "https://mycase.example/case/{case_number}",
        )
        assert url == "https://mycase.example/case/6991234567"


class TestSaveAsPdfDetection:
    @pytest.mark.parametrize(
        "label",
        [
            "Save As PDF",
            "Save as PDF",
            "save as pdf",
            "Save PDF",
            "Download PDF",
            "Print",
            "Export",
        ],
    )
    def test_matches_export_label(self, label: str) -> None:
        assert export_cases.matches_export_label(label)

    def test_find_save_as_pdf_control_directly(self) -> None:
        page = _mock_page_with_controls([("Save As PDF", True)])
        match = export_cases.find_export_button(page)
        assert match is not None
        _context, control = match
        assert export_cases.matches_export_label(export_cases._control_text(control))

    def test_find_save_as_pdf_inside_actions_menu(self, monkeypatch: pytest.MonkeyPatch) -> None:
        page = MagicMock()
        menu_trigger = MagicMock()
        save_control = MagicMock()
        calls = {"direct": 0}

        def fake_find_direct(_context: MagicMock) -> MagicMock | None:
            calls["direct"] += 1
            if calls["direct"] == 1:
                return None
            return save_control

        monkeypatch.setattr(export_cases, "find_direct_export_control", fake_find_direct)
        monkeypatch.setattr(export_cases, "find_menu_trigger_control", lambda _context: menu_trigger)
        monkeypatch.setattr(export_cases, "iter_search_contexts", lambda _page: [_page])

        match = export_cases.find_export_button(page)

        assert match is not None
        _context, control = match
        assert control is save_control
        menu_trigger.click.assert_called_once()
        page.wait_for_timeout.assert_called_once_with(500)


class TestIframeAndRetryBehavior:
    def test_find_export_control_inside_iframe(self) -> None:
        page = _mock_page_with_controls([])
        iframe = _mock_frame_with_controls([("Save As PDF", True)])
        page.frames = [iframe]

        match = export_cases.find_export_button(page)

        assert match is not None
        context, control = match
        assert context is iframe
        assert export_cases.matches_export_label(export_cases._control_text(control))

    def test_find_export_button_with_retries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        page = MagicMock()
        attempts = {"count": 0}

        def fake_find_export_button(_page: MagicMock) -> tuple[MagicMock, MagicMock] | None:
            attempts["count"] += 1
            if attempts["count"] < 3:
                return None
            return page, MagicMock()

        monkeypatch.setattr(export_cases, "find_export_button", fake_find_export_button)

        match = export_cases.find_export_button_with_retries(
            page,
            retry_count=5,
            retry_delay_ms=0,
        )

        assert match is not None
        assert attempts["count"] == 3


class TestUrlTemplateDiscovery:
    def test_infer_case_url_template(self) -> None:
        template = export_cases.infer_case_url_template(
            "https://mycase.cloudapps.cisco.com/case/detail/6991234567/view",
            "6991234567",
        )
        assert template == "https://mycase.cloudapps.cisco.com/case/detail/{case_number}/view"

    def test_discover_case_url_template_from_frame(self) -> None:
        page = MagicMock()
        page.url = "https://mycase.cloudapps.cisco.com/home"
        frame = MagicMock()
        frame.url = "https://mycase.cloudapps.cisco.com/case/detail/6991234567/view"
        page.frames = [frame]

        template = export_cases.discover_case_url_template(page, "6991234567")

        assert "{case_number}" in template
        assert "6991234567" not in template


class TestDebugPause:
    def test_debug_pause_on_failure(self, tmp_output: Path) -> None:
        page = _mock_page_with_controls([("Close Case", True)])

        def _write_screenshot(*, path: str, full_page: bool) -> None:
            Path(path).write_bytes(b"png")

        page.screenshot.side_effect = _write_screenshot
        prompts: list[str] = []

        def fake_input(prompt: str = "") -> str:
            prompts.append(prompt)
            return ""

        entry = export_cases.export_case_with_browser(
            page,
            case_number="6991234567",
            output_dir=tmp_output,
            case_url_template="https://example.test/case/{case_number}",
            logger=logging.getLogger("test.cisco_mycase_export.debug_pause"),
            debug_pause_on_failure=True,
            input_func=fake_input,
            export_retry_count=1,
            case_load_wait_ms=0,
        )

        assert entry.status == "failed"
        assert prompts
        assert "Press Enter to continue" in prompts[0]
