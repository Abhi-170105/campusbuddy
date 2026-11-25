I'm Member 3 of the CampusBuddy capstone (Samsung Innovation Campus). This repo is open in the IDE. My part is the events module ("Who's going?" + event recommendations) and the campus assistant (RAG chatbot). The code is written and 60 unit tests pass, but it was only tested with offline fallbacks (TF-IDF search and extractive answers). Your job is to finish it on this laptop with the real models, measure it, and get it ready to merge. Work step by step, run every command yourself, and show me the output of each step before moving on.

ABOUT THIS MACHINE
- Windows, Python 3.14, NVIDIA GPU, 16 GB RAM. Use the normal (non-Administrator) terminal.
- Repo root: the folder that contains events/, assistant/, data/, eval/.

MY FILES (only change these)
events/, assistant/, data/events/, data/docs/, eval/events/, eval/assistant/, eval/member3_results.md, requirements-member3.txt.
Do not edit other members' folders (profiles/, matching/, lostfound/, backend/, frontend/, docs/).

DO NOT CHANGE
- The function signatures and return formats: events.checkin, events.attendees, events.recommend_events, events.going_together, assistant.ask. If you think one must change, stop and tell me why.
- The privacy rule in events/checkins.py (is_visible): shown only if share_events is True AND ghost_mode is False. The privacy tests must keep passing.
- The 30 questions in eval/assistant/questions.json. Never edit questions or expected answers to raise the score.

STEPS
1. Check setup: run `python --version`, `nvidia-smi`, `git status`, and `git branch`. Make sure we are on branch member3-events (create it from main if missing).
2. Install: `pip install -r requirements-member3.txt`. For GPU, install the CUDA build of torch that matches nvidia-smi (see pytorch.org "Get started"), then confirm with `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`. If torch or faiss-cpu has no wheel for Python 3.14, create a Python 3.12 virtual environment in .venv and use that instead (do not commit .venv). faiss is optional: the code falls back to numpy automatically.
3. Run `python -m pytest`. All tests must pass (60 or more). Fix any failure before continuing; if a fix would change a function's behaviour, tell me first.
4. Build the real index: `python -m assistant.build_index`. The output must say "Embedder: sentence-transformers" and "Generator: Qwen/Qwen2.5-1.5B-Instruct". If it says tfidf or extractive, find out why (missing package, download failed) and fix it. Check the 3 sample answers make sense.
5. Evaluate: `python -m eval.assistant.evaluate_assistant --tune`. Target: at least 80% accuracy (answered correctly or correctly refused). Show me the summary and every wrong answer.
6. If below 80%, or wrong answers show a clear pattern, tune in this order and re-run step 5 after each change, keeping a small table of settings and accuracy:
   a. top_k 3, 4, 5 (--top-k)
   b. chunk size 80, 120, 200 words (--chunk-words) with overlap about 25% (--overlap)
   c. the system prompt in assistant/generator.py, e.g. to make the model copy exact numbers or refuse more firmly
   d. a bigger model if the GPU has room: set CAMPUSBUDDY_LLM=Qwen/Qwen2.5-3B-Instruct
   Keep the best setting as the default in assistant/config.py and re-run with --tune at the end.
7. Time one ask() call after the model is loaded. If it takes more than 5 seconds on GPU, tell me.
8. Events: run `python -m eval.events.evaluate_events` and confirm collaborative filtering still beats popularity on Hit Rate@5. Then run the notebook eval/events/evaluation.ipynb top to bottom so its outputs are saved.
9. Update the results: fill every "LAPTOP" cell in eval/member3_results.md and the "Results so far" section of assistant/README.md with the real numbers from steps 5 to 8, plus the final settings (models, top_k, chunk size, threshold). Report honestly, including what did not reach the target.
10. Final check: `python -m pytest` again, then `git status`. Make sure assistant/index/, model files, .venv and __pycache__ are NOT staged.
11. Commit and push only my folders:
    git add events assistant data/events data/docs eval/events eval/assistant eval/member3_results.md requirements-member3.txt
    git commit -m "Member 3: real-model evaluation, tuned assistant, results"
    git push -u origin member3-events
    Then tell me to open a Pull Request into main on GitHub.

WHEN YOU FINISH, give me
- The final test count, assistant accuracy (overall, answered, refused), groundedness, and events Hit Rate@5 / Precision@5 for all three methods.
- The final settings you chose and why.
- Anything that still needs a human: filling human_correct / human_grounded in eval/assistant/results.csv, swapping in real college documents, and the three open team questions in events/README.md.

Explain your changes in simple words. I have to defend this work in a viva.
