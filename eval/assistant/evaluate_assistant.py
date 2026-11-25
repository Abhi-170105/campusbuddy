"""
Evaluate the campus assistant on the 30-question test set.

    python -m eval.assistant.evaluate_assistant            # evaluate with current settings
    python -m eval.assistant.evaluate_assistant --tune     # find the best "I don't know" threshold first
    python -m eval.assistant.evaluate_assistant --embed tfidf --llm none   # fast offline run

Outputs in eval/assistant/:
    results.csv        one row per question: answer, sources, correct, grounded,
                       plus empty human_correct / human_grounded columns for the team to fill
    summary.json       the headline numbers
    threshold_sweep.png (with --tune) accuracy for each possible threshold

SCORING (automatic; the brief also asks for a human check, see results.csv)
    Answerable question:   correct if the answer contains every required fact
                           (e.g. "75%") AND the right document is among the sources.
    Unanswerable question: correct if the assistant says "I don't know".
    Groundedness:          share of the answer's content words that appear in the
                           cited source chunks. 1.0 = every word is backed by a source.
Target from the brief: at least 80% answered correctly or correctly refused.
"""
import argparse
import json
import time
from pathlib import Path

import pandas as pd

from assistant import config
from assistant.generator import content_words
from assistant.rag import Assistant

HERE = Path(__file__).resolve().parent


def load_questions(path=None):
    return json.loads(Path(path or HERE / "questions.json").read_text(encoding="utf-8"))


def is_refusal(answer):
    return answer.lower().startswith("i don't know")


def has_facts(answer, must_include):
    text = " ".join(answer.lower().split())
    return all(any(alt.lower() in text for alt in item.split("|")) for item in must_include)


def groundedness(answer, sources, chunks_by_source):
    words = [w for w in content_words(answer.split(" (")[0]) if not w.startswith("[")]
    if not words:
        return None
    pool = " ".join(chunks_by_source.get((s["source"], s["section"]), s["snippet"]) for s in sources).lower()
    return round(sum(w.strip(".,:") in pool for w in words) / len(words), 3)


def score_one(item, out, chunks_by_source):
    refused = is_refusal(out["answer"])
    if item["answerable"]:
        right_source = any(s["source"] == item["source"] for s in out["sources"])
        correct = (not refused) and has_facts(out["answer"], item["must_include"]) and right_source
    else:
        correct = refused
    grounded = None if refused else groundedness(out["answer"], out["sources"], chunks_by_source)
    return correct, refused, grounded


def run(assistant, questions):
    chunks_by_source = {}
    for c in assistant.chunks:
        key = (c["source"], c["section"])
        chunks_by_source[key] = chunks_by_source.get(key, "") + " " + c["text"]
    rows = []
    for item in questions:
        start = time.time()
        out = assistant.ask(item["question"])
        top = assistant.retrieve(item["question"], 1)
        correct, refused, grounded = score_one(item, out, chunks_by_source)
        rows.append({
            "id": item["id"], "question": item["question"], "answerable": item["answerable"],
            "expected_answer": item["expected_answer"], "answer": out["answer"],
            "sources": "; ".join(f"{s['source']} / {s['section']}" for s in out["sources"]),
            "top_score": top[0]["score"] if top else 0.0, "refused": refused,
            "correct": correct, "grounded": grounded, "seconds": round(time.time() - start, 2),
            "human_correct": "", "human_grounded": "",
        })
    return pd.DataFrame(rows)


def summarise(df, assistant):
    ans, unans = df[df["answerable"]], df[~df["answerable"]]
    g = df["grounded"].dropna()
    return {
        "questions": len(df),
        "accuracy": round(df["correct"].mean(), 3),
        "answerable_correct": f"{int(ans['correct'].sum())}/{len(ans)}",
        "unanswerable_refused": f"{int(unans['correct'].sum())}/{len(unans)}",
        "wrongly_refused": int((ans["refused"]).sum()),
        "groundedness_mean": round(float(g.mean()), 3) if len(g) else None,
        "target_met": bool(df["correct"].mean() >= 0.8),
        "embedder": assistant.embedder.name, "generator": assistant.generator.name,
        "search": assistant.store.backend, "top_k": assistant.top_k, "threshold": assistant.threshold,
        "chunk_words": assistant.chunk_words, "overlap": assistant.overlap, "chunks": len(assistant.chunks),
    }


def tune_threshold(assistant, questions):
    """Answer everything once with threshold 0, then work out the accuracy every
    threshold would give, without asking the model again."""
    saved = assistant.threshold
    assistant.threshold = 0.0
    df = run(assistant, questions)
    assistant.threshold = saved
    candidates = sorted({0.0} | {round(s + 1e-4, 4) for s in df["top_score"]})
    sweep = []
    for th in candidates:
        refused_now = (df["top_score"] < th) | df["refused"]
        ok = (df["answerable"] & ~refused_now & df["correct"]) | (~df["answerable"] & refused_now)
        sweep.append({"threshold": th, "accuracy": ok.mean()})
    sweep = pd.DataFrame(sweep).reset_index(drop=True)
    best_acc = sweep["accuracy"].max()
    # Several ranges of thresholds can give the best accuracy. Take the WIDEST range
    # and use its middle, so a small change in scores does not flip answers.
    ranges, start = [], None
    for i, row in sweep.iterrows():
        if row["accuracy"] == best_acc and start is None:
            start = row["threshold"]
        if start is not None and (i + 1 == len(sweep) or sweep.loc[i + 1, "accuracy"] != best_acc):
            end = sweep.loc[i + 1, "threshold"] if i + 1 < len(sweep) else row["threshold"] + 0.05
            ranges.append((start, end))
            start = None
    lo, hi = max(ranges, key=lambda r: r[1] - r[0])
    th = round((lo + hi) / 2, 4)
    _plot_sweep(sweep, th)
    return th, best_acc


def _plot_sweep(sweep, chosen):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.step(sweep["threshold"], sweep["accuracy"], where="post", color="#2a6fdb")
    ax.axvline(chosen, color="#e08a1e", ls="--", label=f"chosen = {chosen:.3f}")
    ax.axhline(0.8, color="#8a8f98", ls=":", label="target 80%")
    ax.set_xlabel("\"I don't know\" threshold (retrieval similarity)")
    ax.set_ylabel("Accuracy on 30 questions")
    ax.set_ylim(0, 1.02)
    ax.set_title("Too low: answers what it can't. Too high: refuses what it can.")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(HERE / "threshold_sweep.png", dpi=150)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tune", action="store_true", help="find and save the best threshold first")
    p.add_argument("--embed")
    p.add_argument("--llm")
    p.add_argument("--top-k", type=int)
    p.add_argument("--chunk-words", type=int)
    p.add_argument("--overlap", type=int)
    p.add_argument("--threshold", type=float)
    p.add_argument("--questions")
    args = p.parse_args()

    assistant = Assistant(embed=args.embed, llm=args.llm, top_k=args.top_k, threshold=args.threshold,
                          chunk_words=args.chunk_words, overlap=args.overlap)
    questions = load_questions(args.questions)

    if args.tune:
        th, acc = tune_threshold(assistant, questions)
        assistant.threshold = th
        (assistant.index_dir / "tuned.json").write_text(
            json.dumps({"embedder": assistant.embedder.name, "threshold": th}))
        print(f"Tuned threshold: {th:.4f} (expected accuracy {acc:.0%}). Saved; ask() uses it from now on.")

    df = run(assistant, questions)
    summary = summarise(df, assistant)
    df.to_csv(HERE / "results.csv", index=False)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1))

    wrong = df[~df["correct"]]
    print(f"\nAccuracy {summary['accuracy']:.0%} ({int(df['correct'].sum())}/{len(df)}) | "
          f"answerable {summary['answerable_correct']} | refused correctly {summary['unanswerable_refused']} | "
          f"groundedness {summary['groundedness_mean']}")
    print(f"Target (80%) {'MET' if summary['target_met'] else 'NOT met'}.  "
          f"[{summary['embedder']} + {summary['generator']}, top_k={summary['top_k']}, "
          f"threshold={summary['threshold']}]")
    if len(wrong):
        print("\nWrong answers:")
        for _, r in wrong.iterrows():
            print(f"  {r['id']} {r['question']}\n      got: {r['answer'][:150]}")


if __name__ == "__main__":
    main()
