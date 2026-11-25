# assistant/ : campus assistant chatbot (Member 3)

Answers questions from the college documents in `data/docs/`, cites its sources,
and says "I don't know" instead of guessing.

## Function the backend calls
```python
import assistant
assistant.ask("When do the semester end exams start?")
# {"answer": "The Semester End Examinations (SEE) start on 7 December 2026 ... [1]",
#  "sources": [{"source": "academic_calendar.md", "section": "Key dates", "score": 0.61, "snippet": "..."}]}
assistant.ask("Who won the IPL?")
# {"answer": "I don't know. I couldn't find this in the college documents.", "sources": []}
```
The first call loads the models (slow, about 10 to 60 seconds); later calls are fast.
The backend should call `assistant.get_assistant()` once at startup.

## How it works (RAG = retrieval-augmented generation)
1. **Chunk** (`documents.py`): split each document by heading, then into ~120-word pieces with 30 words of overlap.
2. **Embed** (`embedder.py`): turn each chunk into a vector with sentence-transformers `all-MiniLM-L6-v2`.
3. **Index** (`vector_store.py`): store vectors in FAISS; find the top 3 chunks closest to the question.
4. **Safety net 1**: if the best match is below the threshold, answer "I don't know".
5. **Generate** (`generator.py`): a free Hugging Face model (`Qwen2.5-1.5B-Instruct`) answers using ONLY those chunks and cites them.
6. **Safety net 2**: the model is told to say "I don't know" when the chunks do not contain the answer.

The index is saved in `assistant/index/` (not committed) and rebuilt automatically when documents change.

## Fallbacks (so it always runs)
| If missing | Used instead |
|---|---|
| sentence-transformers / no internet for the download | TF-IDF word matching |
| transformers / torch | Extractive answer: the best-matching sentence, quoted exactly |
| faiss | numpy search (same results) |

## Settings (environment variables)
`CAMPUSBUDDY_EMBED` (`auto`, `tfidf`, or a model), `CAMPUSBUDDY_LLM` (`auto`, `none`, or a model),
`CAMPUSBUDDY_TOP_K`, `CAMPUSBUDDY_CHUNK_WORDS`, `CAMPUSBUDDY_CHUNK_OVERLAP`, `CAMPUSBUDDY_THRESHOLD`.
Example for a slower PC: `set CAMPUSBUDDY_LLM=Qwen/Qwen2.5-0.5B-Instruct`.

## Commands
```
python -m assistant.build_index                      # build the index and try 3 questions
python -m assistant.build_index --ask "Where is the lost and found?"
python -m eval.assistant.evaluate_assistant --tune   # tune the threshold, score the 30 questions
python -m pytest assistant/tests
```

## Results so far
- **Offline fallback (TF-IDF + extractive):** 28/30 = 93% (24/25 answered, 4/5 refused, groundedness 1.00).
- **Full system on laptop GPU (all-MiniLM-L6-v2 + Qwen2.5-1.5B-Instruct):** 30/30 = 100% (25/25 answered, 5/5 refused, groundedness 0.92, tuned threshold = 0.2324, top_k = 3, chunk_words = 120, overlap = 30). Warm inference latency: ~1.95s per query on NVIDIA RTX 3050 Laptop GPU. Target (80%) met.
Caveat for the report: the threshold is tuned on the same 30 questions it is scored on,
so the real-world number will be somewhat lower.

## Using real college documents
Replace the sample files in `data/docs/` (see its README), rewrite `eval/assistant/questions.json`,
then run the evaluation with `--tune` again.
