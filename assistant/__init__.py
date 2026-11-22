"""Campus assistant (Member 3): answers questions from the college documents in data/docs/.

Contract used by the backend:
    assistant.ask(question) -> {"answer": str, "sources": [{"source", "section", "score", "snippet"}]}
When the documents do not contain the answer, "answer" is "I don't know..." and sources is [].
"""
_assistant = None


def get_assistant():
    """Build the assistant once (loads models and the index), then reuse it."""
    global _assistant
    if _assistant is None:
        from .rag import Assistant
        _assistant = Assistant()
    return _assistant


def ask(question):
    return get_assistant().ask(question)


__all__ = ["ask", "get_assistant"]
