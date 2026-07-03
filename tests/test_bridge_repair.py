from diagnostics.bridge_repair import BridgeRepairAdvisor


def test_bridge_repair_advisor_maps_profile_crosstalk():
    advisor = BridgeRepairAdvisor()
    hint = advisor.advise("profile-cross-talk")
    assert "LARKSUITE_CLI_CONFIG_DIR" in hint.action
    assert not advisor.can_auto_apply(hint)


def test_bridge_repair_advisor_allows_safe_jsonl_drift_logging():
    advisor = BridgeRepairAdvisor()
    assert advisor.can_auto_apply(advisor.advise("jsonl-drift"))
