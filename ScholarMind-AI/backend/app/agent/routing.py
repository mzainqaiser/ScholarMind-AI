"""Deterministic intent classification and document scoping.
A rule-based router is used on purpose: 3B local models classify unreliably, and rules make routing testable.
Intent names equal tool names, except 'chitchat' and 'verify_missing'."""
import re

_RULES = [  # order matters: first match wins
    ("study_plan", r"study plan|learning plan|revision plan|roadmap|schedule .*(study|learn)|plan (for|to) (study|learn)"),
    ("flashcards", r"flash ?cards?"),
    ("quiz", r"\bquiz\b|\bmcqs?\b|multiple[- ]choice|test me|practice questions|\d+\s+questions?\b|short[- ]answer"),
    ("document_search", r"^(find|search|locate|look up|show me where)\b|where (does|do|is|are)\b.*\b(mention|discuss|say|cover)|which (document|file|page)"),
    ("summarize", r"summar(y|ize|ise)|tl;?dr|overview of|give me the gist"),
    ("notes", r"study notes|revision notes|(make|create|generate|write|prepare|take).{0,25}\bnotes\b"),
    ("compare", r"compar(e|ison)|difference|differ\b|\bversus\b|\bvs\.?\b|contrast|similarit"),
    ("research", r"research|literature|investigate|state of the art|review the evidence|what do my (sources|documents|papers) say"),
]
_CHITCHAT = re.compile(r"^\s*(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening)|what can you do|help)\b[\s\W]*$", re.I)
_MISSING = re.compile(r"can(?:no|')t find|could not find|not (in|found in) (my|the) (documents|files|notes)|isn'?t in my (documents|notes)", re.I)

# Command words stripped before retrieval. NOTE: "learning" is deliberately NOT here - it is part of topics
# such as "supervised learning" and removing it lowered match scores below the relevance threshold.
_NOISE = set("""create generate make write prepare give me my the a an of on about from for with and to in is are what who how why
mcq mcqs quiz quizzes question questions flashcard flashcards flash cards card notes note summarize summarise summary overview
study plan compare comparison difference differences between versus vs uploaded documents document file files please can you
short answer multiple choice find search locate show explain tell all this that these those selected""".split())


def classify_intent(question: str, has_history: bool) -> str:
    q = question.strip()
    if _CHITCHAT.match(q):
        return "chitchat"
    if _MISSING.search(q) and has_history:
        return "verify_missing"
    low = q.lower()
    for name, pattern in _RULES:
        if re.search(pattern, low):
            return name
    return "document_qa"


def topic_query(question: str) -> str:
    """Strip command words so retrieval searches for the topic, not for 'create 10 MCQs'."""
    words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-']*", question) if w.lower() not in _NOISE and not w.isdigit()]
    return " ".join(words)


def build_search_query(question: str, history: list) -> str:
    """Resolve short / pronoun follow-ups using the previous user turn of the same conversation."""
    prev = [m["content"] for m in history if m["role"] == "user"]
    if not prev:
        return question
    n = len(question.split())
    pronoun = re.search(r"\b(it|its|that|this|they|them|those|these|one)\b", question.lower())
    starter = re.match(r"\s*(and|what about|how about|why|how so|can you elaborate|explain more)", question.lower())
    if n <= 5 or starter or (pronoun and n <= 10):
        return f"{prev[-1]} {question}"
    return question


def resolve_docs(question: str, selected_ids: list, all_docs: list) -> list:
    """User selection wins. Otherwise detect documents named in the question (e.g. 'my ml_notes file')."""
    indexed = {d["id"]: d for d in all_docs if d["status"] == "indexed"}
    if selected_ids:
        return [i for i in selected_ids if i in indexed]
    q = question.lower()
    found = []
    for d in indexed.values():
        stem = re.sub(r"\.[a-z0-9]+$", "", d["filename"].lower())
        words = [w for w in re.split(r"[_\-\s.]+", stem) if len(w) >= 3]
        if stem.replace("_", " ") in q or stem in q or (len(words) >= 2 and all(w in q for w in words)):
            found.append(d["id"])
    return found


def parse_options(question: str, forced: dict) -> dict:
    opts = {"count": None, "days": None, "quiz_type": "mcq"}
    m = re.search(r"(\d+)\s*(?:mcqs?|questions?|flash ?cards?|cards?|multiple)", question, re.I)
    if m:
        opts["count"] = int(m.group(1))
    m = re.search(r"(\d+)[- ]?(day|week)", question, re.I)
    if m:
        opts["days"] = int(m.group(1)) * (7 if m.group(2).lower() == "week" else 1)
    if re.search(r"short[- ]answer", question, re.I):
        opts["quiz_type"] = "short"
    opts.update({k: v for k, v in (forced or {}).items() if v is not None})
    opts["count"] = max(1, min(int(opts["count"] or 5), 20))
    opts["days"] = max(1, min(int(opts["days"] or 7), 60))
    return opts
