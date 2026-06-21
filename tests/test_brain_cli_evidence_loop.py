"""Tests for Brain CLI evidence loop across separate CLI processes."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from brain.brain_store import BrainSessionStore, sanitize_case_for_storage
from cli.voicepilot_cli import (
    run_brain_list,
    run_brain_next,
    run_brain_replay,
    run_brain_start,
    run_brain_status,
    run_brain_upload,
)
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = "VP-CUBE-0001"
SAMPLE_EVIDENCE = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "sample_evidence"
    / "parser"
    / "show_sip_ua_status_disabled.txt"
)


@pytest.fixture
def session_store(tmp_path: Path) -> BrainSessionStore:
    return BrainSessionStore(root=tmp_path / "sessions")


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    return engine


def _fresh_runtime() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    return engine


class TestBrainCliEvidenceLoop:
    def test_brain_start_creates_persisted_session(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        output: list[str] = []
        assert (
            run_brain_start(
                PLAYBOOK_ID,
                output.append,
                engine=runtime_engine,
                session_store=session_store,
            )
            == 0
        )
        text = "\n".join(output)
        assert "Brain session started" in text
        assert "Next Requested Evidence:" in text

        sessions = session_store.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].playbook == PLAYBOOK_ID

    def test_persisted_session_loads_across_simulated_cli_calls(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        start_output: list[str] = []
        run_brain_start(
            PLAYBOOK_ID,
            start_output.append,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id

        fresh = _fresh_runtime()
        status_output: list[str] = []
        assert (
            run_brain_status(
                session_id,
                status_output.append,
                engine=fresh,
                session_store=session_store,
            )
            == 0
        )
        assert session_id in "\n".join(status_output)

    def test_upload_accepts_evidence_file_and_records_command(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        run_brain_start(
            PLAYBOOK_ID,
            lambda _line: None,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id
        command = "show sip-ua status"

        fresh = _fresh_runtime()
        output: list[str] = []
        assert (
            run_brain_upload(
                session_id,
                command,
                SAMPLE_EVIDENCE,
                output.append,
                engine=fresh,
                session_store=session_store,
            )
            == 0
        )
        text = "\n".join(output)
        assert "Evidence uploaded" in text
        assert command in text

        session, case = session_store.load(session_id)
        assert any(
            item.source.command == command for item in case.evidence if item.source.command
        )
        assert any("Evidence uploaded:" in entry.summary for entry in session.journey)

    def test_next_advances_pipeline_after_upload(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        run_brain_start(
            PLAYBOOK_ID,
            lambda _line: None,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id

        fresh = _fresh_runtime()
        run_brain_upload(
            session_id,
            "show sip-ua status",
            SAMPLE_EVIDENCE,
            lambda _line: None,
            engine=fresh,
            session_store=session_store,
        )

        next_runtime = _fresh_runtime()
        output: list[str] = []
        assert (
            run_brain_next(
                session_id,
                output.append,
                engine=next_runtime,
                session_store=session_store,
            )
            == 0
        )
        text = "\n".join(output)
        assert "Brain advanced" in text
        assert "Top Hypothesis:" in text

        session, _case = session_store.load(session_id)
        assert session.current_quality_score is not None

    def test_status_works_from_persisted_session(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        run_brain_start(
            PLAYBOOK_ID,
            lambda _line: None,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id

        output: list[str] = []
        assert (
            run_brain_status(
                session_id,
                output.append,
                engine=_fresh_runtime(),
                session_store=session_store,
            )
            == 0
        )
        text = "\n".join(output)
        assert "Brain Status" in text
        assert "Next Requested Evidence:" in text

    def test_replay_includes_uploaded_command(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        run_brain_start(
            PLAYBOOK_ID,
            lambda _line: None,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id
        command = "show sip-ua status"

        fresh = _fresh_runtime()
        run_brain_upload(
            session_id,
            command,
            SAMPLE_EVIDENCE,
            lambda _line: None,
            engine=fresh,
            session_store=session_store,
        )

        output: list[str] = []
        assert (
            run_brain_replay(
                session_id,
                output.append,
                engine=_fresh_runtime(),
                session_store=session_store,
            )
            == 0
        )
        assert f"Evidence uploaded: {command}" in "\n".join(output)

    def test_list_shows_persisted_sessions(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        run_brain_start(
            PLAYBOOK_ID,
            lambda _line: None,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id

        output: list[str] = []
        assert (
            run_brain_list(
                output.append,
                engine=_fresh_runtime(),
                session_store=session_store,
            )
            == 0
        )
        text = "\n".join(output)
        assert "Session | Case | Playbook | Stage | Confidence | Quality | Completed" in text
        assert session_id in text

    def test_invalid_session_gives_clear_error(self, session_store: BrainSessionStore) -> None:
        output: list[str] = []
        code = run_brain_status(
            "BRN-does-not-exist",
            output.append,
            engine=_fresh_runtime(),
            session_store=session_store,
        )
        assert code == 1
        assert "Brain session not found: BRN-does-not-exist" in "\n".join(output)

    def test_no_secrets_are_stored(
        self,
        runtime_engine: RuntimeEngine,
        session_store: BrainSessionStore,
    ) -> None:
        run_brain_start(
            PLAYBOOK_ID,
            lambda _line: None,
            engine=runtime_engine,
            session_store=session_store,
        )
        session_id = session_store.list_sessions()[0].session_id
        session, case = session_store.load(session_id)
        case = replace(
            case,
            metadata={
                **case.metadata,
                "api_key": "super-secret-value",
                "normal_field": "safe",
            },
        )
        session_store.save(session, case)

        json_text = session_store.root.joinpath(f"{session_id}.json").read_text(encoding="utf-8")
        pkl_bytes = session_store.root.joinpath(f"{session_id}.case.pkl").read_bytes()
        assert "super-secret-value" not in json_text
        assert b"super-secret-value" not in pkl_bytes

        reloaded_session, reloaded_case = session_store.load(session_id)
        assert "api_key" not in reloaded_case.metadata
        assert reloaded_case.metadata.get("normal_field") == "safe"
        assert reloaded_session.session_id == session_id


class TestBrainStoreSanitization:
    def test_sanitize_case_for_storage_removes_sensitive_keys(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        case = runtime_engine.case_manager.load_case(session.case_id)
        case.metadata["password"] = "hidden"
        case.metadata["notes"] = "visible"
        sanitized = sanitize_case_for_storage(case)
        assert "password" not in sanitized.metadata
        assert sanitized.metadata["notes"] == "visible"
