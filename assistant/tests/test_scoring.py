"""Tests for the evaluation script's scoring rules."""
from eval.assistant.evaluate_assistant import has_facts, is_refusal, score_one

from assistant import config


def test_has_facts_accepts_alternatives():
    assert has_facts("You need at least 75 percent attendance.", ["75%|75 percent"])
    assert not has_facts("You need good attendance.", ["75%|75 percent"])


def test_refusal_detected():
    assert is_refusal(config.IDK)
    assert not is_refusal("The fine is Rs. 2.")


def test_unanswerable_correct_only_when_refused():
    item = {"answerable": False}
    assert score_one(item, {"answer": config.IDK, "sources": []}, {})[0]
    assert not score_one(item, {"answer": "Rs. 500", "sources": []}, {})[0]


def test_answerable_needs_fact_and_right_source():
    item = {"answerable": True, "must_include": ["500"], "source": "exam_rules.md"}
    src = [{"source": "exam_rules.md", "section": "Revaluation", "snippet": "fee is Rs. 500"}]
    assert score_one(item, {"answer": "The fee is Rs. 500.", "sources": src}, {})[0]
    wrong_src = [dict(src[0], source="library.md")]
    assert not score_one(item, {"answer": "The fee is Rs. 500.", "sources": wrong_src}, {})[0]
