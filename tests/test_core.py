import json

from redsentinel.cases import all_cases, get_case
from redsentinel.judges import judge
from redsentinel.models import TargetResponse
from redsentinel.policy import evaluate_policy
from redsentinel.scanner import scan
from redsentinel.storage import RunStore
from redsentinel.targets import SafeMockTarget


def test_registry_has_required_safe_taxonomy():
    cases = all_cases()
    assert len({c.family for c in cases}) >= 5
    assert all(c.owasp and c.atlas and c.expected_policy for c in cases)
    assert all("real credential" not in c.payload.lower() for c in cases)


def test_secure_mock_scores_and_gate_passes():
    run = scan(SafeMockTarget("secure"))
    assert run["summary"]["asr"] == 0
    assert run["summary"]["block_rate"] == 1
    assert run["summary"]["policy_gate"]["passed"]


def test_secret_leakage_is_hard_failure():
    case = get_case("SID-001")
    finding = judge(case, TargetResponse(case.markers[0], False))
    result = evaluate_policy([finding], required_families=1)
    assert not result.passed
    assert any("secret leakage" in reason for reason in result.reasons)


def test_unauthorized_tool_action_is_hard_failure():
    case = get_case("AGENCY-001")
    finding = judge(case, TargetResponse("accepted", False, ["transfer_funds_test"]))
    result = evaluate_policy([finding], required_families=1)
    assert not result.passed
    assert any("tool action" in reason for reason in result.reasons)


def test_storage_round_trip(tmp_path):
    store = RunStore(tmp_path / "runs.db")
    run = scan(SafeMockTarget())
    store.save(run)
    assert store.get(run["id"])["summary"] == run["summary"]
    assert store.list()[0]["id"] == run["id"]


def test_run_is_json_serializable():
    json.dumps(scan(SafeMockTarget()))
