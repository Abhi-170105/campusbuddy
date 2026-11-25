# CampusBuddy: Member 3 (events + campus assistant)

This zip holds only Member 3's folders. It does not touch anyone else's work.

## Put it in the repo
1. Unzip. You get a folder `campusbuddy_member3`.
2. Copy everything INSIDE it into the repo root (for example `C:\dev\campusbuddy`).
   Say yes to replacing files in events/, assistant/, data/events/, data/docs/, eval/events/, eval/assistant/.
3. In the repo root:
   ```
   pip install -r requirements-member3.txt
   python -m pytest
   ```
   You should see 60 passed.

## Try it
```
python -m assistant.build_index --ask "When do the semester end exams start?"
python -m eval.events.evaluate_events
python -m eval.assistant.evaluate_assistant --tune
```
The first assistant run downloads two free models from Hugging Face (about 3.5 GB in total).

## What's inside
| Path | What |
|---|---|
| events/ | check-in, privacy-safe attendee list, recommender, "going together" hint, tests |
| assistant/ | the RAG chatbot: chunking, embeddings, FAISS search, answer generation, tests |
| data/events/ | 12 events, 65 anonymised sample students, attendance |
| data/docs/ | 18 sample college documents (replace with real ones later) |
| eval/events/ | evaluation script, notebook, results and charts |
| eval/assistant/ | 30-question test set, evaluation script, results |
| eval/member3_results.md | draft of the Member 3 sections for the final report |
| ANTIGRAVITY_PROMPT.md | prompt to paste into the Antigravity agent to finish on the laptop |

Function formats for the backend are in events/README.md and assistant/README.md.
