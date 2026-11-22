"""
Evaluate the event recommender against the two baselines.

Run from the repo root:   python -m eval.events.evaluate_events
Outputs (in eval/events/):
    results.csv            one row per method and K, mean and std over all runs
    hit_rate_at_k.png      chart: Hit Rate@K for the three methods
    precision_at_k.png     chart: Precision@K for the three methods
    cold_start.csv         how well new students are served (content fallback)

HOW THE TEST WORKS (viva version)
    1. Hide 25% of all check-ins. The recommender never sees them.
    2. For every student who still has history AND has hidden check-ins,
       ask each method for its top K events.
    3. Hit Rate@K  = share of students where at least one hidden event is in the top K.
       Precision@K = share of the K recommended events that were really hidden events.
    4. Repeat with 10 different random splits and average, so one lucky split
       cannot decide the result.
    Cold start: students whose every check-in was hidden look like new students.
    For them the system falls back to content matching; we measure that separately.
"""
import argparse
import copy
import random
from pathlib import Path

import pandas as pd

from events.checkins import EventStore
from events.recommend import rank_content, rank_popularity, recommend_events

OUT = Path(__file__).resolve().parent
METHODS = {
    "Collaborative filtering": lambda st, sid, k: [r["event_id"] for r in recommend_events(sid, k, st)],
    "Content-only": rank_content,
    "Popularity-only": rank_popularity,
}


def split(going, rng, test_share):
    rows = sorted(going)
    rng.shuffle(rows)
    n_test = int(round(len(rows) * test_share))
    return set(rows[n_test:]), set(rows[:n_test])


def evaluate(store, ks=(1, 3, 5), runs=10, test_share=0.25, seed=0):
    warm_rows, cold_rows = [], []
    for run in range(runs):
        rng = random.Random(seed + run)
        train, test = split(store.going, rng, test_share)
        st = copy.copy(store)          # shares events/students, own check-ins
        st.going = train
        train_students = {s for s, _ in train}
        hidden = {}
        for s, e in test:
            hidden.setdefault(s, set()).add(e)

        for sid, truth in hidden.items():
            warm = sid in train_students
            for name, rank in METHODS.items():
                # for a "new" student, recommend_events falls back to content by itself
                recs = rank(st, sid, max(ks))
                for k in ks:
                    top = recs[:k]
                    hits = len(set(top) & truth)
                    row = {"run": run, "method": name, "k": k,
                           "hit": int(hits > 0), "precision": hits / k}
                    (warm_rows if warm else cold_rows).append(row)
    return pd.DataFrame(warm_rows), pd.DataFrame(cold_rows)


def summarise(df):
    per_run = df.groupby(["method", "k", "run"])[["hit", "precision"]].mean().reset_index()
    out = per_run.groupby(["method", "k"]).agg(
        hit_rate=("hit", "mean"), hit_rate_std=("hit", "std"),
        precision=("precision", "mean"), precision_std=("precision", "std")).reset_index()
    return out.round(3)


def plot(summary, metric, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"Collaborative filtering": "#2a6fdb", "Content-only": "#e08a1e", "Popularity-only": "#8a8f98"}
    ks = sorted(summary["k"].unique())
    fig, ax = plt.subplots(figsize=(7, 4.2))
    width = 0.26
    for i, (name, color) in enumerate(colors.items()):
        part = summary[summary["method"] == name].set_index("k").loc[ks]
        xs = [x + (i - 1) * width for x in range(len(ks))]
        ax.bar(xs, part[metric], width, yerr=part[f"{metric}_std"], capsize=3, label=name, color=color)
        for x, v in zip(xs, part[metric]):
            ax.text(x, v / 2, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white", fontweight="bold")
    ax.set_xticks(range(len(ks)), [f"K = {k}" for k in ks])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel(title)
    ax.set_title(f"{title}: mean of 10 random splits (error bar = std)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper center")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--test-share", type=float, default=0.25)
    parser.add_argument("--attendance", help="optional CSV, e.g. with pilot check-ins added")
    args = parser.parse_args()

    store = EventStore(attendance_path=args.attendance) if args.attendance else EventStore()
    warm, cold = evaluate(store, runs=args.runs, test_share=args.test_share)
    summary = summarise(warm)
    summary.to_csv(OUT / "results.csv", index=False)
    plot(summary, "hit_rate", "Hit Rate@K", OUT / "hit_rate_at_k.png")
    plot(summary, "precision", "Precision@K", OUT / "precision_at_k.png")
    if len(cold):
        summarise(cold).to_csv(OUT / "cold_start.csv", index=False)

    print(f"{len(store.going)} check-ins, {args.runs} runs, {int(args.test_share * 100)}% hidden each run\n")
    print(summary.to_string(index=False))
    at5 = summary[summary["k"] == 5].set_index("method")
    cf, pop = at5.loc["Collaborative filtering", "hit_rate"], at5.loc["Popularity-only", "hit_rate"]
    verdict = "BEATS" if cf > pop else "does NOT beat"
    print(f"\nCF Hit Rate@5 {cf:.3f} {verdict} popularity {pop:.3f} "
          f"({(cf - pop) / pop * 100:+.0f}%).")
    if len(cold):
        n_cold = len(cold) // (len(METHODS) * 3)
        print(f"Also scored {n_cold} cold-start cases (see cold_start.csv).")


if __name__ == "__main__":
    main()
