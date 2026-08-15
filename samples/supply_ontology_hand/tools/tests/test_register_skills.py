from __future__ import annotations


def test_register_skills_dry_run_lists_three_local_skills():
    import register_skills

    result = register_skills.run(apply=False)

    assert result["mode"] == "dry_run"
    assert [item["name"] for item in result["skills"]] == [
        "demand-fulfillment-capacity-analysis",
        "demand-fulfillment-requirement-coverage-analysis",
        "production-schedule-backward-planning_supply_ontology_hand",
    ]


def test_register_skills_updates_existing_and_registers_missing(monkeypatch):
    import register_skills

    calls: list[list[str]] = []

    def fake_cli(args):
        calls.append(args)
        if args == ["skill", "list"]:
            return {"data": [{"name": "demand-fulfillment-capacity-analysis", "skill_id": "existing-1"}]}
        if args[:2] == ["skill", "register"]:
            return {"skill_id": f"new-{len(calls)}"}
        return {}

    monkeypatch.setattr(register_skills, "run_cli", fake_cli)

    result = register_skills.run(apply=True)

    assert result["skills"][0]["operation"] == "updated"
    assert [item["operation"] for item in result["skills"][1:]] == ["registered", "registered"]
    assert ["skill", "update-package", "existing-1", str(register_skills.SKILLS_DIR / "demand-fulfillment-capacity-analysis")] in calls
    assert ["skill", "set-status", "existing-1", "published"] in calls
