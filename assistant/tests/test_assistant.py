"""Tests for the campus assistant. They use TF-IDF and extractive answers, so they
run in seconds with no model download. Run: python -m pytest assistant/tests"""
import json

import pytest

from assistant import config
from assistant.documents import chunk_documents, load_documents
from assistant.rag import Assistant

DOCS = {
    "library.md": "# Central Library\n\n## Borrowing\nEach student can borrow up to 4 books at a time.\n"
                  "The fine for late return is Rs. 2 per day per book.\n\n## Timings\n"
                  "The library is open from 8:00 am to 8:00 pm on weekdays.",
    "hostel.md": "# Hostel Rules\n\n## Mess timings\nDinner: 7:30 pm to 9:00 pm.\n"
                 "Breakfast: 7:15 am to 9:00 am.",
    "README.md": "# This file must be ignored\nSecret readme text about rockets.",
}


@pytest.fixture
def docs_dir(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    for name, text in DOCS.items():
        (d / name).write_text(text, encoding="utf-8")
    return d


@pytest.fixture
def bot(docs_dir, tmp_path):
    return Assistant(docs_dir=docs_dir, index_dir=tmp_path / "index", embed="tfidf", llm="none",
                     threshold=0.05)


# ---------- documents and chunks ----------

def test_readme_is_not_indexed(docs_dir):
    assert {d["source"] for d in load_documents(docs_dir)} == {"library.md", "hostel.md"}


def test_chunks_keep_source_and_section(docs_dir):
    chunks = chunk_documents(load_documents(docs_dir), chunk_words=50, overlap=10)
    assert {c["section"] for c in chunks} >= {"Borrowing", "Timings", "Mess timings"}
    assert all(c["source"] in DOCS for c in chunks)


def test_long_sections_are_split_with_overlap():
    doc = {"source": "x.md", "title": "X", "text": "# X\n" + " ".join(f"w{i}" for i in range(250))}
    chunks = chunk_documents([doc], chunk_words=100, overlap=20)
    assert len(chunks) == 3
    assert all(len(c["text"].split()) <= 100 for c in chunks)
    assert chunks[0]["text"].split()[-20:] == chunks[1]["text"].split()[:20]   # the overlap


# ---------- ask() ----------

def test_answer_has_fact_and_source(bot):
    out = bot.ask("What is the fine for returning a book late?")
    assert "Rs. 2" in out["answer"]
    assert out["sources"][0]["source"] == "library.md"
    assert set(out["sources"][0]) == {"source", "section", "score", "snippet"}


def test_section_heading_helps(bot):
    assert "7:30" in bot.ask("When is dinner in the hostel mess?")["answer"]


@pytest.mark.parametrize("q", ["Who won the football world cup?", "", "   "])
def test_off_topic_or_empty_says_i_dont_know(bot, q):
    assert bot.ask(q) == {"answer": config.IDK, "sources": []}


def test_high_threshold_refuses(docs_dir, tmp_path):
    strict = Assistant(docs_dir=docs_dir, index_dir=tmp_path / "i2", embed="tfidf", llm="none", threshold=0.99)
    assert strict.ask("What is the library fine?")["answer"] == config.IDK


def test_model_refusal_returns_no_sources(bot):
    class Refuses:
        name = "fake"
        def answer(self, q, passages):
            return config.IDK, []
    bot.generator = Refuses()
    assert bot.ask("What is the library fine?") == {"answer": config.IDK, "sources": []}


def test_extractive_answers_only_quote_the_documents(bot):
    out = bot.ask("How many books can I borrow?")
    sentence = out["answer"].split(" (")[0]
    assert sentence in DOCS["library.md"]          # exact quote, nothing invented


# ---------- index caching ----------

def test_index_is_saved_and_reused(docs_dir, tmp_path):
    a = Assistant(docs_dir=docs_dir, index_dir=tmp_path / "ix", embed="tfidf", llm="none")
    b = Assistant(docs_dir=docs_dir, index_dir=tmp_path / "ix", embed="tfidf", llm="none")
    assert a.built and not b.built
    assert json.loads((tmp_path / "ix" / "meta.json").read_text())["documents"] == 2


def test_index_rebuilds_when_a_document_changes(docs_dir, tmp_path):
    Assistant(docs_dir=docs_dir, index_dir=tmp_path / "ix", embed="tfidf", llm="none")
    (docs_dir / "sports.md").write_text("# Sports\nThe gym is free for all students.", encoding="utf-8")
    c = Assistant(docs_dir=docs_dir, index_dir=tmp_path / "ix", embed="tfidf", llm="none", threshold=0.05)
    assert c.built
    assert c.ask("Is the gym free?")["sources"][0]["source"] == "sports.md"


def test_tuned_threshold_is_used(docs_dir, tmp_path):
    ix = tmp_path / "ix"
    ix.mkdir()
    (ix / "tuned.json").write_text(json.dumps({"embedder": "tfidf", "threshold": 0.123}))
    assert Assistant(docs_dir=docs_dir, index_dir=ix, embed="tfidf", llm="none").threshold == 0.123


# ---------- the real project data ----------

def test_at_least_15_real_documents():
    assert len(load_documents()) >= 15


def test_question_set_is_valid():
    qs = json.loads((config.ROOT / "eval" / "assistant" / "questions.json").read_text(encoding="utf-8"))
    sources = {d["source"] for d in load_documents()}
    assert len(qs) == 30 and len({q["id"] for q in qs}) == 30
    assert sum(not q["answerable"] for q in qs) >= 5
    for q in qs:
        if q["answerable"]:
            assert q["source"] in sources and q["must_include"]


def test_contract_function_importable():
    import assistant
    assert callable(assistant.ask)
