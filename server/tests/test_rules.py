"""Tests for the rule booklet."""

from server.detection import RULES, RuleId, detect


def test_every_rule_id_has_an_entry() -> None:
    """Each RuleId maps to exactly one booklet entry with a matching id."""
    assert set(RULES) == set(RuleId)
    assert all(rule.id == rule_id for rule_id, rule in RULES.items())


def test_every_rule_cites_a_source() -> None:
    """Each rule has at least one documentation source with an https link."""
    for rule in RULES.values():
        assert rule.sources, rule.id
        assert all(source.url.startswith("https://") for source in rule.sources)


def test_sites_take_category_and_reason_from_their_rule() -> None:
    """A detected site carries its rule's category and reason unchanged."""
    sites = detect("a = x // 2\nb = round(y)\nprint(*xs)\n")
    assert {site.rule for site in sites} == {
        RuleId.FLOOR_DIVISION,
        RuleId.ROUNDING,
        RuleId.PRINT_STARRED,
    }
    for site in sites:
        rule = RULES[site.rule]
        assert (site.category, site.reason) == (rule.category, rule.reason)
