from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_executive_handbook_has_business_story_and_verification_evidence():
    handbook = (ROOT / "docs" / "handbook.html").read_text(encoding="utf-8")

    required_markers = (
        'lang="zh-CN"',
        "供应链智能决策 Sample",
        'id="executive-summary"',
        'id="business-story"',
        'id="scenarios"',
        'id="data-foundation"',
        'id="knowledge-network"',
        'id="capability-map"',
        'id="validation"',
        'id="release-boundary"',
        "openbkn-hand-import-guide_cn.md",
        "agent-operation-guide.md",
        "agent-scenario-kn-capability-design_cn.md",
        "OpenBKN",
    )

    for marker in required_markers:
        assert marker in handbook
