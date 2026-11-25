"""Build (or rebuild) the search index and try a few questions.

    python -m assistant.build_index
    python -m assistant.build_index --ask "When do exams start?"
"""
import argparse

from .rag import Assistant


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ask", action="append", help="question to try (can repeat)")
    p.add_argument("--embed", help="tfidf, auto, or a sentence-transformers model")
    p.add_argument("--llm", help="none, auto, or a Hugging Face model")
    args = p.parse_args()

    a = Assistant(embed=args.embed, llm=args.llm)
    print(f"{'Built' if a.built else 'Loaded'} index: {a.n_docs} documents, {len(a.chunks)} chunks")
    print(f"Embedder: {a.embedder.name} | Search: {a.store.backend} | Generator: {a.generator.name} "
          f"| top_k={a.top_k} | threshold={a.threshold}")
    for q in args.ask or ["When do the semester end exams start?", "What is the library fine?",
                          "Who won the IPL in 2025?"]:
        out = a.ask(q)
        print(f"\nQ: {q}\nA: {out['answer']}")
        for s in out["sources"]:
            print(f"   - {s['source']} / {s['section']} (score {s['score']})")


if __name__ == "__main__":
    main()
