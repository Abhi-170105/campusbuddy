# data/docs: documents the campus assistant answers from

These 18 files are SAMPLE documents for a fictional college, "Sample Institute of
Technology (SIT)". They exist so the assistant can be built and tested before the
real documents arrive.

To use your college's real documents:
1. Delete the sample files (keep this README).
2. Put real files here: .md, .txt or .pdf (PDF needs `pip install pypdf`).
3. Run `python -m assistant.build_index`.
4. Rewrite eval/assistant/questions.json so the questions match the new documents.

Rules: no personal phone numbers, emails of individuals, or student names.
