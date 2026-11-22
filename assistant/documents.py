"""
Step 1 of the pipeline: read the documents and cut them into chunks.

Why chunks? A whole document is too long to embed well and too long to give the
LLM. Small pieces (about 120 words) let us find exactly the paragraph that answers
the question. Pieces overlap a little (30 words) so a fact on a boundary is not
cut in half.

Each chunk remembers its source file and section heading, so answers can cite them.
"""
import re

from . import config


def load_documents(docs_dir=None):
    """Return [{"source": file name, "title": first heading, "text": full text}]."""
    docs_dir = docs_dir or config.DOCS_DIR
    docs = []
    for path in sorted(docs_dir.iterdir()):
        if path.name.lower() == "readme.md" or path.name.startswith("."):
            continue
        if path.suffix.lower() in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif path.suffix.lower() == ".pdf":
            text = _read_pdf(path)
        else:
            continue
        if text.strip():
            title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.strip()), path.stem)
            docs.append({"source": path.name, "title": title, "text": text})
    return docs


def _read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"Skipping {path.name}: run `pip install pypdf` to read PDFs")
        return ""
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def _sections(text):
    """Split on markdown headings. Returns [(heading, body)]."""
    sections, heading, lines = [], "", []
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            if any(l.strip() for l in lines):
                sections.append((heading, "\n".join(lines).strip()))
            heading, lines = m.group(1).strip(), []
        else:
            lines.append(line)
    if any(l.strip() for l in lines):
        sections.append((heading, "\n".join(lines).strip()))
    return sections


def chunk_documents(docs, chunk_words=None, overlap=None):
    """Return [{"id", "source", "title", "section", "text"}]."""
    chunk_words = chunk_words or config.CHUNK_WORDS
    overlap = config.CHUNK_OVERLAP if overlap is None else overlap
    step = max(chunk_words - overlap, 1)
    chunks = []
    for doc in docs:
        for section, body in _sections(doc["text"]):
            words = body.split()
            for start in range(0, max(len(words) - overlap, 1), step):
                piece = " ".join(words[start:start + chunk_words])
                if not piece:
                    continue
                chunks.append({"id": len(chunks), "source": doc["source"], "title": doc["title"],
                               "section": section or doc["title"], "text": piece})
    return chunks


def text_for_embedding(chunk):
    """Add the document title and section to the chunk text. A chunk that says
    'Dinner: 7:30 pm' is much easier to find when it also says 'Hostel Rules, Mess timings'."""
    return f"{chunk['title']}. {chunk['section']}. {chunk['text']}"
