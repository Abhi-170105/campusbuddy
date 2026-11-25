# Member 3 results (draft for the final report)

Full system numbers were measured on the laptop with real models on GPU (NVIDIA RTX 3050 Laptop GPU, 4 GB VRAM).
Final settings: Embedder `sentence-transformers/all-MiniLM-L6-v2`, Generator `Qwen/Qwen2.5-1.5B-Instruct`, Search `FAISS`, `top_k=3`, `chunk_words=120` (overlap 30), tuned similarity `threshold=0.2324`. Single inference latency: ~1.95s per query on GPU.

## Event "Who's going?" and recommendations

**Privacy.** A student appears in an attendee list only if they opted in to sharing and
ghost mode is off; missing or unclear settings count as hidden. Unit tests cover every
combination, settings changed after check-in, and a random test with 200 students checked
against every event and every viewer. Deliberately breaking the ghost-mode rule made 4 tests
fail, which shows the tests really guard the rule. No leak was found.

**Recommender.** User-based collaborative filtering (cosine similarity over the
student-event matrix, 10 nearest students). New students with no history get content
matching between event tags and their interests, skills and goals.

**Evaluation.** 25% of all 162 check-ins were hidden, each method recommended 5 events,
repeated over 10 random splits (12 events, 65 synthetic students).

| Method | Hit Rate@5 | Precision@5 |
|---|---|---|
| Collaborative filtering (ours) | 0.916 ± 0.044 | 0.216 ± 0.015 |
| Content-only baseline | 0.894 ± 0.051 | 0.214 ± 0.013 |
| Popularity-only baseline | 0.568 ± 0.079 | 0.128 ± 0.015 |

Collaborative filtering beats the popularity baseline by 61% on Hit Rate@5, meeting the
target. It is level with content-only (the gap is within one standard deviation), so we do
not claim it beats content matching. On synthetic data, profile interests come from the
same tags that drive attendance, which favours content matching; real profiles are less
complete, so CF should gain with real pilot data.
Charts: `eval/events/hit_rate_at_k.png`, `eval/events/precision_at_k.png`.

**Limits.** Synthetic data; only 12 events, so a top-5 list covers 40% of all events.

## Campus assistant (RAG)

**Pipeline.** 18 college documents are split into chunks of ~120 words (30-word overlap),
embedded with sentence-transformers (all-MiniLM-L6-v2) and searched with FAISS (top 3).
If the best match is below a tuned threshold the assistant answers "I don't know".
Otherwise a free Hugging Face model (Qwen2.5-1.5B-Instruct) answers from the retrieved
chunks only and cites them; it can also refuse.

**Test set.** 30 questions: 25 answerable from the documents and 5 that are not
(off-topic, or on-topic but missing, like parking fees). A question counts as correct if
the answer contains the required fact and cites the right document, or, for unanswerable
questions, if the assistant refuses.

| Configuration | Accuracy | Answered correctly | Refused correctly | Groundedness |
|---|---|---|---|---|
| Offline fallback (TF-IDF + extractive) | 93% (28/30) | 24/25 | 4/5 | 1.00 |
| Full system (MiniLM + Qwen2.5) | 100% (30/30) | 25/25 | 5/5 | 0.92 |

Target: at least 80% answered correctly or correctly refused.
Threshold chart: `eval/assistant/threshold_sweep.png`.
Human check: two team members fill `human_correct` and `human_grounded` in
`eval/assistant/results.csv`.

**Limits.** The documents are realistic samples, not the college's real ones. The threshold
is tuned on the same 30 questions it is scored on, so accuracy on new questions will be
somewhat lower.
