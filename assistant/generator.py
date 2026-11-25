"""
Step 4: write the answer from the retrieved chunks.

Two generators:
  - LLMGenerator: a free Hugging Face chat model (default Qwen2.5-1.5B-Instruct) that
    reads the numbered passages and answers in 1-3 sentences, citing [1], [2]...
    It is told to reply "I don't know" when the passages do not contain the answer.
    This is the second safety net after the retrieval threshold.
  - ExtractiveGenerator: no model at all. Picks the sentence from the passages that
    shares the most words with the question. Used when transformers is not
    installed and in tests. Its answers are exact quotes, so it cannot invent facts.
"""
import re

from . import config

STOPWORDS = set("""a an the is are was were be been do does did of to in on at for by with from
and or what when where which who whom how much many can could i my me we our you your it its this
that there their they he she his her as if into about any all per each get need has have had will
would should must may might""".split())

SYSTEM_PROMPT = (
    "You are CampusBuddy, a campus assistant for college students. "
    "Answer the question directly in 1 to 2 sentences using the facts, dates, numbers, and section headings from the passages. "
    "Never respond with just a citation number alone. "
    "Cite the passages you used like [1] or [2]. "
    "If the passages do not contain the answer, reply exactly: I don't know."
)


def content_words(text):
    return [w for w in re.findall(r"[a-z0-9][a-z0-9.:%,-]*", text.lower().replace("’", "'"))
            if w.strip(".,:") not in STOPWORDS]


def _sentences(text):
    # split after . ! ? but not after "Rs." (as in "Rs. 500")
    parts = re.split(r"(?<=[.!?])(?<!Rs\.)\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.split()) >= 3]


def _norm(w):
    w = w.strip(".,:;")
    for suf in ("ing", "es", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


class ExtractiveGenerator:
    name = "extractive"

    def answer(self, question, passages):
        q = {_norm(w) for w in content_words(question)}
        # each sentence also carries its section heading ("Mess timings", "Wi-Fi"),
        # because the heading often says what the sentence is about
        candidates = []
        for rank, p in enumerate(passages):
            heading = p["section"] if p["section"] != p["title"] else ""   # real sub-headings only
            for sent in _sentences(p["text"]):
                candidates.append((rank, sent, {_norm(w) for w in content_words(f"{heading} {sent}")}))
        # A word found in many candidate sentences (like "library" inside the library
        # document) says little; a rare one (like "fine") says a lot. Weight = 1 / count.
        df = {}
        for _, _, words in candidates:
            for w in words:
                df[w] = df.get(w, 0) + 1
        best, best_score = None, 0.0
        for rank, sent, words in candidates:
            overlap = q & words
            score = sum(1 / df[w] for w in overlap) - 0.05 * rank   # prefer higher-ranked passages
            if overlap and score > best_score:
                best, best_score = (sent, rank), score
        if best is None:
            return config.IDK, []
        sent, rank = best
        p = passages[rank]
        # the heading can hold part of the answer (e.g. "Thursday" in a timetable)
        where = p["title"] if p["section"] == p["title"] else f"{p['title']}, {p['section']}"
        return f"{sent} ({where}) [{rank + 1}]", [rank]


class LLMGenerator:
    def __init__(self, model_name):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device).eval()
        self.torch = torch

    def answer(self, question, passages):
        context = "\n\n".join(f"[{i + 1}] ({p['source']}, {p['section']}) {p['text']}"
                              for i, p in enumerate(passages))
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Passages:\n{context}\n\nQuestion: {question}"}]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=160, do_sample=False,
                                      pad_token_id=self.tokenizer.eos_token_id)
        text = self.tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        if not text or text.lower().startswith("i don't know") or text.lower().startswith("i do not know"):
            return config.IDK, []
        cited = sorted({int(n) - 1 for n in re.findall(r"\[(\d+)\]", text) if 0 < int(n) <= len(passages)})
        return text, cited or list(range(len(passages)))


def make_generator(choice=None):
    choice = choice or config.LLM
    if choice == "none":
        return ExtractiveGenerator()
    model = config.DEFAULT_LLM if choice == "auto" else choice
    try:
        return LLMGenerator(model)
    except Exception as err:
        if choice != "auto":
            raise
        print(f"[assistant] LLM unavailable ({type(err).__name__}); using extractive answers.")
        return ExtractiveGenerator()
