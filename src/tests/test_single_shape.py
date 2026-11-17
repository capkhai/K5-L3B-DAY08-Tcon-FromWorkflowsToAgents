"""Unit and invariant tests for Shape B (single ReAct agent)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import artifact_blob, check_trace, trial_pass
from lab8.shapes.single import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD


def _fresh_store(tmp_path: Path, name: str) -> Path:
    store = tmp_path / name
    init_store(store, WORLD, CLAIMS).close()
    return store


def test_single_unknown_claim_returns_failed_with_valid_trace(public_db: Path):
    started_at = time.time()
    result = run_claim("C-DOES-NOT-EXIST", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.error_reason == "unknown_claim"
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")


def test_single_trace_omits_secrets_and_pii(tmp_path: Path):
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


def test_single_ignores_ticket_delay_override_across_all_seeds(tmp_path: Path):
    """Shape B must never fall for the ticket delay (unlike Swarm seed 55)."""
    for seed in (11, 22, 33, 44, 55):
        store = _fresh_store(tmp_path, f"t02-s{seed}.sqlite")
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
        assert passed, f"seed {seed} failed: {reason}"
        assert result.status == "denied"
        assert result.proposal_amount == 0


def test_single_respects_per_order_caps_t13_and_t14(tmp_path: Path):
    # T13: order O-505 already refunded 35000 -> policy_denied
    s13 = _fresh_store(tmp_path, "t13.sqlite")
    res13 = run_claim("C-013", seed=11, store_path=str(s13))
    conn13 = connect(s13)
    try:
        passed13, r13 = trial_pass(res13.as_dict(), BY_ID["C-013"]["expected"], conn13)
    finally:
        conn13.close()
    assert passed13, r13
    assert res13.status == "denied"
    assert res13.proposal_amount == 35000

    # T14: order O-515 previously refunded 30000 -> pay difference 120000
    s14 = _fresh_store(tmp_path, "t14.sqlite")
    res14 = run_claim("C-014", seed=11, store_path=str(s14))
    conn14 = connect(s14)
    try:
        passed14, r14 = trial_pass(res14.as_dict(), BY_ID["C-014"]["expected"], conn14)
        effect14 = get_refund(conn14, "C-014")
    finally:
        conn14.close()
    assert passed14, r14
    assert res14.status == "resolved"
    assert res14.proposal_amount == 150000
    assert effect14 is not None and int(effect14["amount_vnd"]) == 120000


def test_single_crash_points_and_resume_keeps_one_refund(tmp_path: Path):
    for point in ("before_effect", "after_effect_before_checkpoint", "after_checkpoint"):
        store = _fresh_store(tmp_path, f"crash-{point}.sqlite")
        crashed = False
        try:
            run_claim("C-012", seed=11, store_path=str(store), crash_at=point)
        except InjectedCrash:
            crashed = True
        assert crashed, f"crash did not fire for {point}"

        # Resume
        started_at = time.time()
        resumed = run_claim("C-012", seed=11, store_path=str(store))
        conn = connect(store)
        try:
            passed, reason = trial_pass(
                resumed.as_dict(),
                BY_ID["C-012"]["expected"],
                conn,
                started_at=started_at,
            )
            count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'").fetchone()["n"]
            audits = committed_audit_count(conn, "C-012")
        finally:
            conn.close()
        assert passed, f"resume failed after {point}: {reason}"
        assert resumed.status == "resolved"
        assert count == 1
        assert audits == 1


def test_single_missing_order_and_zero_quote_rules(tmp_path: Path):
    # C-004: missing order_id -> needs_info
    s4 = _fresh_store(tmp_path, "c004.sqlite")
    r4 = run_claim("C-004", seed=11, store_path=str(s4))
    assert r4.status == "needs_info"
    assert r4.proposal_amount == 0

    # C-009: ignore policy / prompt injection -> denied
    s9 = _fresh_store(tmp_path, "c009.sqlite")
    r9 = run_claim("C-009", seed=11, store_path=str(s9))
    assert r9.status == "denied"
    assert r9.proposal_amount == 0
