"""The R2 variant rejects the ticket override without changing the reference."""

from lab8.db import connect, init_store
from lab8.metrics import trial_pass
from lab8.shapes.swarm_reference import run_claim as reference
from research.swarm_verified import run_claim as verified
from tests.conftest import BY_ID, CLAIMS, WORLD


def test_r2_disabling_override_corrects_t02_and_keeps_model_calls(tmp_path):
    outcomes = {}
    calls = {}
    for name, runner in (("reference", reference), ("verified", verified)):
        store = tmp_path / f"r2-{name}.sqlite"
        init_store(store, WORLD, CLAIMS).close()
        result = runner("C-002", seed=55, store_path=str(store))
        conn = connect(store)
        try:
            outcomes[name] = trial_pass(result.as_dict(), BY_ID["C-002"]["expected"], conn)[0]
        finally:
            conn.close()
        calls[name] = result.model_calls
    assert outcomes == {"reference": False, "verified": True}
    assert calls["reference"] == calls["verified"] == 3
