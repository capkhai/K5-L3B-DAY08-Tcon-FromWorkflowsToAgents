"""Document the reference weakness through trace evidence, not just status."""

import json
from pathlib import Path

from lab8.db import connect, init_store
from lab8.shapes.swarm_reference import run_claim
from tests.conftest import CLAIMS, WORLD


def test_swarm_t02_trace_explains_seed_dependent_delay_override(tmp_path):
    """The known miss must be traceable; the stored order stays authoritative.

    This characterizes the supplied reference, not the desired refund policy.
    Each seed gets a fresh database so an earlier refund cannot affect it.
    """
    for seed, status, amount in ((11, "denied", 0), (55, "resolved", 20000)):
        store = tmp_path / f"swarm-evidence-{seed}.sqlite"
        init_store(store, WORLD, CLAIMS).close()

        result = run_claim("C-002", seed=seed, store_path=str(store))
        trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
        events = trace["events"]
        kinds = [event["kind"] for event in events]
        investigation = next(event["payload"] for event in events if event["kind"] == "investigator")
        quote = next(event["payload"] for event in events if event["kind"] == "quote")
        overrides = [event["payload"] for event in events if event["kind"] == "model_override"]

        assert trace["run_id"] == result.run_id
        assert investigation["lookup_order"]["order"]["delay_days"] == 2
        assert investigation["lookup_order"]["order"]["damage_verified"] is False
        assert result.status == status
        assert result.proposal_amount == quote["amount_vnd"] == amount

        if seed == 55:
            assert overrides == [{"delay_days": 5}]
            assert kinds.index("investigator") < kinds.index("model_override") < kinds.index("quote")
        else:
            assert overrides == []

        # The override affects the in-memory decision, not the original DB row.
        conn = connect(store)
        try:
            order = conn.execute("SELECT delay_days FROM orders WHERE order_id = ?", ("O-202",)).fetchone()
            assert order["delay_days"] == 2
        finally:
            conn.close()
