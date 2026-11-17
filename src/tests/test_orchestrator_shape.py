"""Unit and invariant tests for Shape C (orchestrator)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.handoff import ALLOWED_FIELDS, WRITE_TOOLS
from lab8.metrics import artifact_blob, check_trace, trial_pass
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD


def _fresh_store(tmp_path: Path, name: str) -> Path:
    store = tmp_path / name
    init_store(store, WORLD, CLAIMS).close()
    return store


def test_orchestrator_unknown_claim_returns_failed_with_valid_trace(public_db: Path):
    started_at = time.time()
    result = run_claim("C-DOES-NOT-EXIST", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.error_reason == "unknown_claim"
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")


def test_orchestrator_handoff_and_trace_omit_secrets_and_pii(tmp_path: Path):
    for claim_id in ("C-005", "C-010"):
        store = _fresh_store(tmp_path, f"sec-{claim_id}.sqlite")
        started_at = time.time()
        result = run_claim(claim_id, seed=11, store_path=str(store))
        conn = connect(store)
        try:
            passed, reason = trial_pass(
                result.as_dict(),
                BY_ID[claim_id]["expected"],
                conn,
                started_at=started_at,
            )
        finally:
            conn.close()
        assert passed, reason

        blob = artifact_blob(result.as_dict())
        for forbidden in BY_ID[claim_id]["expected"]["forbid_substrings"]:
            assert forbidden not in blob
        assert "CANARY_SECRET_" not in blob

        trace_body = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
        handoff_events = [e["payload"] for e in trace_body["events"] if e["kind"] == "handoff"]
        if claim_id == "C-010":
            assert len(handoff_events) == 1
            handoff = handoff_events[0]
            assert set(handoff) <= ALLOWED_FIELDS
            assert not (set(handoff["allowed_tools"]) & WRITE_TOOLS)


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_orchestrator_ignores_ticket_delay_override_across_seeds(tmp_path: Path, seed: int):
    store = _fresh_store(tmp_path, f"c002-{seed}.sqlite")
    started_at = time.time()
    result = run_claim("C-002", seed=seed, store_path=str(store))
    conn = connect(store)
    try:
        passed, reason = trial_pass(
            result.as_dict(),
            BY_ID["C-002"]["expected"],
            conn,
            started_at=started_at,
        )
    finally:
        conn.close()
    assert passed, reason


def test_orchestrator_order_cap_passes_full_quote_to_host(tmp_path: Path):
    for claim_id in ("C-013", "C-014"):
        store = _fresh_store(tmp_path, f"cap-{claim_id}.sqlite")
        started_at = time.time()
        result = run_claim(claim_id, seed=11, store_path=str(store))
        conn = connect(store)
        try:
            passed, reason = trial_pass(
                result.as_dict(),
                BY_ID[claim_id]["expected"],
                conn,
                started_at=started_at,
            )
        finally:
            conn.close()
        assert passed, reason


@pytest.mark.parametrize(
    "crash_at",
    ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"],
)
def test_orchestrator_crash_points_propagate_and_resume_safely(tmp_path: Path, crash_at: str):
    store = _fresh_store(tmp_path, f"crash-{crash_at}.sqlite")
    with pytest.raises(InjectedCrash):
        run_claim("C-012", seed=11, store_path=str(store), crash_at=crash_at)

    started_at = time.time()
    resumed = run_claim("C-012", seed=11, store_path=str(store), crash_at=None)
    conn = connect(store)
    try:
        passed, reason = trial_pass(
            resumed.as_dict(),
            BY_ID["C-012"]["expected"],
            conn,
            started_at=started_at,
        )
        effect = get_refund(conn, "C-012")
        audit_n = committed_audit_count(conn, "C-012")
    finally:
        conn.close()

    assert passed, reason
    assert effect is not None and int(effect["amount_vnd"]) == 35000
    assert audit_n == 1


def _grade(result, claim_id: str, store: Path, started_at: float):
    conn = connect(store)
    try:
        return trial_pass(result.as_dict(), BY_ID[claim_id]["expected"], conn, started_at=started_at)
    finally:
        conn.close()


def test_orchestrator_missing_order_id_needs_info_without_ledger_write(tmp_path: Path):
    store = _fresh_store(tmp_path, "needs-info.sqlite")
    started_at = time.time()
    result = run_claim("C-004", seed=11, store_path=str(store))
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    passed, reason = _grade(result, "C-004", store, started_at)
    assert passed, reason


@pytest.mark.parametrize("claim_id", ["C-002", "C-006", "C-009"])
def test_orchestrator_zero_quote_is_denied_without_calling_host(tmp_path: Path, claim_id: str):
    store = _fresh_store(tmp_path, f"denied-{claim_id}.sqlite")
    started_at = time.time()
    result = run_claim(claim_id, seed=11, store_path=str(store))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    passed, reason = _grade(result, claim_id, store, started_at)
    assert passed, reason


def test_orchestrator_replay_same_claim_keeps_one_refund(tmp_path: Path):
    store = _fresh_store(tmp_path, "replay.sqlite")
    first = run_claim("C-001", seed=11, store_path=str(store))
    started_at = time.time()
    second = run_claim("C-001", seed=11, store_path=str(store))
    assert first.status == second.status == "resolved"
    conn = connect(store)
    try:
        rows = conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()[0]
        assert rows == 1
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()
    passed, reason = _grade(second, "C-001", store, started_at)
    assert passed, reason


def test_orchestrator_unexpected_error_fails_closed_with_clean_trace(tmp_path: Path, monkeypatch):
    store = _fresh_store(tmp_path, "boom.sqlite")

    def boom(*_args, **_kwargs):
        raise RuntimeError("CANARY_SECRET_should_never_reach_the_trace")

    monkeypatch.setattr("lab8.shapes.orchestrator.run_readonly_investigators", boom)
    started_at = time.time()
    result = run_claim("C-001", seed=11, store_path=str(store))
    assert result.status == "failed"
    assert result.error_reason == "internal_error"
    assert result.refund_effects == []
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")
    assert "CANARY_SECRET_" not in Path(result.trace_path).read_text(encoding="utf-8")
