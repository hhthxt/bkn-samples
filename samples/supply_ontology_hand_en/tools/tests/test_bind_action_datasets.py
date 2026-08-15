from bind_action_datasets import build_bindings, run_bind


def test_build_bindings_qualifies_schema_and_uses_kn_id():
    mapping = {"bindings": [{"object_type_id": "supply_ontology_hand_mon_task", "dataset": "sc_plan_monitor_task"}]}
    assert build_bindings(mapping, kn_id="supply_ontology_hand_en", schema="public") == [
        {"kn_id": "supply_ontology_hand_en", "object_type_id": "supply_ontology_hand_mon_task", "dataset": "public.sc_plan_monitor_task"}
    ]


def test_build_bindings_expands_schema_placeholder():
    mapping = {"bindings": [{"object_type_id": "ot1", "dataset": "${ACTION_DATASET_SCHEMA}.sc_pr_decision"}]}
    assert build_bindings(mapping, kn_id="supply_ontology_hand_en", schema="public")[0]["dataset"] == "public.sc_pr_decision"


def test_dry_run_does_not_update_object_type():
    calls = []
    report = run_bind(
        {"openbkn": {"kn_id": "supply_ontology_hand_en"}, "database": {"schema": "public"}},
        {"bindings": [{"object_type_id": "ot1", "dataset": "sc_plan_monitor_task"}]},
        dry_run=True,
        run_cmd=lambda args: calls.append(args),
    )
    assert report["ok"] is True
    assert calls == []
