
## 1. Python backend — `app.py`

```python
"""MRIIRS AURA - Artificial University Response Assistant.
A curated university FAQ retrieval chatbot using lightweight NLP.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import re
import unicodedata
from typing import Dict, List, Tuple, Optional

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "knowledge_base.json"
BRAND = "MRIIRS AURA"
FULL_FORM = "Artificial University Response Assistant"
MAX_QUESTION_LENGTH = 500

STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being",
    "do", "does", "did", "can", "could", "would", "should", "will", "may", "might",
    "i", "we", "you", "they", "he", "she", "it", "my", "our", "your", "their",
    "me", "us", "them", "this", "that", "these", "those", "what", "which", "who",
    "whom", "where", "when", "why", "please", "tell", "give", "show", "about",
    "some", "any", "more", "much", "many", "the", "of", "for", "to", "in", "on",
    "at", "by", "with", "from", "and", "or", "as", "per", "into", "there", "here",
    "have", "has", "had", "get", "know", "want", "need", "like", "details", "information"
}

# Normalise common variations without erasing important terms such as "not".
SYNONYMS = {
    "admissions": "admission", "apply": "admission", "applied": "admission", "applying": "admission",
    "application": "admission", "applications": "admission", "registration": "admission",
    "fees": "fee", "tuition": "fee", "charges": "fee", "cost": "fee", "price": "fee",
    "program": "programme", "programs": "programme", "course": "programme", "courses": "programme",
    "subject": "subjects", "syllabi": "syllabus", "curricula": "curriculum",
    "exam": "examination", "exams": "examination", "tests": "examination", "test": "examination",
    "marksheet": "marksheet", "grades": "marks", "scores": "marks",
    "hostels": "hostel", "dorm": "hostel", "accommodation": "hostel", "residence": "hostel",
    "buses": "bus", "transportation": "transport", "placement": "placements", "jobs": "job",
    "internships": "internship", "labs": "laboratory", "laboratories": "laboratory",
    "scholarships": "scholarship", "concession": "scholarship", "waiver": "scholarship",
    "eligibilities": "eligibility", "criteria": "criterion", "documents": "document",
    "locations": "location", "addresses": "address", "emails": "email", "phones": "phone",
    "rechecking": "revaluation", "recheck": "revaluation", "reassess": "reassessment",
    "mca": "mca", "bcom": "bcom", "b.com": "bcom", "mrnat": "mrnat", "aura": "aura",
}

SYNONYM_PHRASES = {
    "master of computer applications": "mca",
    "manav rachna international institute of research and studies": "mriirs",
    "student portal": "erp",
    "student login": "erp",
    "fee structure": "fee structure",
    "date sheet": "datesheet",
    "date-sheet": "datesheet",
    "computer applications": "computer application",
    "career development centre": "crcdc",
    "career development center": "crcdc",
    "corporate relations and career development centre": "crcdc",
    "anti ragging": "antiragging",
    "anti-ragging": "antiragging",
    "naac a++": "naac a++",
}


def load_knowledge_base() -> List[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Knowledge base not found: {DATA_FILE}")
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not data:
        raise ValueError("knowledge_base.json must contain a non-empty list")
    required = {"id", "category", "q", "a", "keywords", "aliases", "source_name", "source_url"}
    for index, item in enumerate(data, start=1):
        missing = required - set(item)
        if missing:
            raise ValueError(f"FAQ record {index} is missing: {', '.join(sorted(missing))}")
    return data

FAQS = load_knowledge_base()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", " and ")
    # Keep common degree abbreviations as single, searchable tokens.
    text = re.sub(r"\bb\s*\.?\s*com\b", " bcom ", text)
    text = re.sub(r"\bb\s*\.?\s*sc\b", " bsc ", text)
    text = re.sub(r"\bb\s*\.?\s*a\b", " ba ", text)
    text = re.sub(r"\bb\s*\.?\s*ca\b", " bca ", text)
    text = re.sub(r"\bb\s*\.?\s*tech\b", " btech ", text)
    for phrase, replacement in SYNONYM_PHRASES.items():
        text = text.replace(phrase, replacement)
    text = re.sub(r"[^a-z0-9+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> List[str]:
    words = normalize_text(text).split()
    result = []
    for word in words:
        if len(word) <= 1 or word in STOP_WORDS:
            continue
        result.append(SYNONYMS.get(word, word))
    return result


def build_search_text(item: dict) -> str:
    # Search only titles, aliases and curated keywords. Long answer prose is excluded
    # because it can create false matches from incidental words.
    return " ".join([item["q"], " ".join(item.get("aliases", [])),
                     " ".join(item.get("keywords", [])), item.get("category", "")])


DOC_TOKENS = [tokenize(build_search_text(item)) for item in FAQS]
DOC_FREQ = Counter(token for tokens in DOC_TOKENS for token in set(tokens))
AVG_DOC_LEN = sum(len(tokens) for tokens in DOC_TOKENS) / max(1, len(DOC_TOKENS))
N_DOCS = len(DOC_TOKENS)


def idf(term: str) -> float:
    # Positive smoothed IDF. Rare discriminative terms receive more weight.
    return math.log(1.0 + (N_DOCS - DOC_FREQ.get(term, 0) + 0.5) / (DOC_FREQ.get(term, 0) + 0.5))


def bm25_score(query_tokens: List[str], doc_tokens: List[str], k1: float = 1.5, b: float = 0.72) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    frequencies = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0
    for term in set(query_tokens):
        tf = frequencies.get(term, 0)
        if not tf:
            continue
        term_idf = idf(term)
        denominator = tf + k1 * (1 - b + b * doc_len / max(1.0, AVG_DOC_LEN))
        score += term_idf * (tf * (k1 + 1)) / denominator
    return score


def phrase_bonus(query: str, item: dict) -> float:
    q = normalize_text(query)
    candidates = [normalize_text(item["q"])] + [normalize_text(x) for x in item.get("aliases", [])]
    for candidate in candidates:
        if candidate and (q == candidate or (len(candidate) >= 12 and candidate in q)):
            return 1.25 if q == candidate else 0.85
    return 0.0


def score_item(query: str, q_tokens: List[str], item: dict, index: int) -> float:
    docs = DOC_TOKENS[index]
    q_set = set(q_tokens)
    d_set = set(docs)
    overlap = q_set & d_set
    if not overlap:
        return 0.0

    bm25 = bm25_score(q_tokens, docs)
    coverage = len(overlap) / max(1, len(q_set))
    weighted_coverage = sum(idf(t) for t in overlap) / max(0.001, sum(idf(t) for t in q_set))
    # Exact programme/entity anchors disambiguate short questions such as "MCA fee".
    anchor_bonus = 0.0
    qn = normalize_text(query)
    title = normalize_text(item["q"])
    for anchor in ("mca", "bca", "btech", "mba", "mriirs", "mrnat", "erp", "hostel", "scholarship", "placement"):
        if anchor in q_set and anchor in docs:
            anchor_bonus += 0.38
    exact = phrase_bonus(query, item)
    # BM25 is scaled to keep a stable interpretation of thresholds across query lengths.
    return (0.48 * min(bm25 / 5.0, 1.4) + 0.30 * weighted_coverage
            + 0.12 * coverage + exact + anchor_bonus)


def find_answer(question: str) -> Tuple[Optional[dict], float, List[dict]]:
    q_tokens = tokenize(question)
    if not q_tokens:
        return None, 0.0, []
    q_set = set(q_tokens)

    # Questions about live daily class timetables are not in the verified dataset.
    # Do not let a shared programme name accidentally retrieve a fee or duration answer.
    q_norm = normalize_text(question)
    timetable_phrases = (
        "class timing", "class timings", "lecture timing", "lecture timings",
        "daily timetable", "class timetable", "time table", "timetable",
        "what time do classes", "when are classes held", "daily class schedule"
    )
    if any(phrase in q_norm for phrase in timetable_phrases):
        return None, 0.0, []

    # A bare programme name is an overview request, not a fee or duration query.
    if q_set in ({"mca"}, {"mriirs"}, {"aura"}) or {"mriirs", "aura"}.issubset(q_set):
        wanted = ("Does MRIIRS offer an MCA programme?" if "mca" in q_set else
                  ("What can MRIIRS AURA help me with?" if "aura" in q_set else "What is MRIIRS?"))
        found = next(item for item in FAQS if item["q"] == wanted)
        related = [x for x in FAQS if x["category"] == found["category"] and x["id"] != found["id"]][:3]
        return found, 1.0, related

    # If the user names a specific degree and asks for its fee, only answer when
    # that degree has a matching fee record. Never borrow another programme's fee.
    degree_anchors = {"mca", "bca", "btech", "mba", "bba", "bcom", "bsc", "bds"}
    candidate_pool = list(enumerate(FAQS))
    if "fee" in q_set and (q_set & degree_anchors):
        requested = q_set & degree_anchors
        matching_fee = []
        for idx, item in enumerate(FAQS):
            dt = set(tokenize(build_search_text(item)))
            if "fee" in dt and requested.issubset(dt):
                matching_fee.append((idx, item))
        if not matching_fee:
            return None, 0.0, []
        # A programme-specific fee query is only ranked against fee records for
        # that exact programme, not against its duration or unrelated FAQs.
        candidate_pool = matching_fee

    # Route revaluation/reassessment wording to records whose question or aliases
    # explicitly describe that process, not a broad examinations overview.
    process_anchors = q_set & {"revaluation", "reassessment", "verification"}
    if process_anchors:
        process_pool = []
        for idx, item in candidate_pool:
            title_alias_text = " ".join([item["q"], " ".join(item.get("aliases", []))])
            title_alias_tokens = set(tokenize(title_alias_text))
            if process_anchors & title_alias_tokens:
                process_pool.append((idx, item))
        if process_pool:
            candidate_pool = process_pool

    ranked = []
    for idx, item in candidate_pool:
        score = score_item(question, q_tokens, item, idx)
        if score > 0:
            ranked.append((score, item))
    ranked.sort(key=lambda row: row[0], reverse=True)
    if not ranked:
        return None, 0.0, []

    best_score, best_item = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0
    # Require meaningful overlap and prefer a clearly separated result. Very broad
    # queries are mapped to explicit topic-overview records where possible.
    min_score = 0.48 if len(set(q_tokens)) <= 2 else 0.52
    has_anchor = bool(set(q_tokens) & {"mca", "mriirs", "mrnat", "erp", "hostel", "scholarship", "placement", "admission"})
    if best_score < min_score or (len(set(q_tokens)) >= 4 and best_score - second_score < 0.025 and not has_anchor):
        return None, best_score, [item for _, item in ranked[:3]]
    suggestions = [item for _, item in ranked[1:5] if item["category"] == best_item["category"]]
    if len(suggestions) < 2:
        suggestions = [item for _, item in ranked[1:4]]
    return best_item, best_score, suggestions[:3]


FALLBACK = (
    "I don't have a verified answer for that exact question in my current MRIIRS knowledge base, "
    "so I don't want to guess. Try adding the programme name, academic year, semester or office "
    "you are asking about. You can also use the official MRIIRS website for the latest notices: "
    "https://manavrachna.edu.in/mriirs/\n\n"
    "I can currently help with admissions, MCA eligibility and curriculum, fee structure, "
    "scholarships, academic calendar, examinations, campus facilities, transport, placements, "
    "student welfare and contact information."
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "brand": BRAND, "full_form": FULL_FORM,
                    "faq_count": len(FAQS), "category_count": len({x['category'] for x in FAQS}),
                    "engine": "BM25-style weighted FAQ retrieval with alias and phrase matching"})


@app.route("/api/categories")
def categories():
    return jsonify(sorted({item["category"] for item in FAQS}))


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("message", "")).strip()
    if not question:
        return jsonify({"error": "Please enter a question so AURA can help."}), 400
    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify({"error": f"Please keep your question under {MAX_QUESTION_LENGTH} characters."}), 400

    item, score, suggestions = find_answer(question)
    if item:
        return jsonify({
            "answer": item["a"], "matched_question": item["q"],
            "category": item["category"], "match": "strong" if score >= 0.72 else "relevant",
            "source_name": item["source_name"], "source_url": item["source_url"],
            "last_verified": item.get("last_verified", ""),
            "suggestions": [x["q"] for x in suggestions]
        })

    # Return nearby question suggestions, but never substitute their answers.
    return jsonify({"answer": FALLBACK, "matched_question": None, "category": "Not matched",
                    "match": "none", "source_name": "Official MRIIRS website",
                    "source_url": "https://manavrachna.edu.in/mriirs/",
                    "suggestions": [x["q"] for x in suggestions[:3]] or [
                        "What is the eligibility for the two-year MCA programme?",
                        "How do I apply for admission to MRIIRS?",
                        "Where can I find the latest MRIIRS fee structure?"
                    ]})


@app.route("/api/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    vote = data.get("vote")
    if vote not in ("up", "down"):
        return jsonify({"error": "Invalid feedback."}), 400
    # Demo acknowledgement only: no names, message content or personal records are stored.
    return jsonify({"status": "received", "message": "Thank you. Your feedback helps improve this project."})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

```

## 2. HTML interface — `templates/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="MRIIRS AURA - Artificial University Response Assistant, a university FAQ chatbot mini project.">
  <title>MRIIRS AURA | Artificial University Response Assistant</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<div class="ambient ambient-blue"></div><div class="ambient ambient-red"></div>
<div class="app-shell">
  <aside class="sidebar" id="sidebar">
    <div class="brand">
      <div class="brand-mark"><span>A</span><i></i></div>
      <div><div class="brand-name">MRIIRS <span>AURA</span></div><div class="brand-sub">ARTIFICIAL UNIVERSITY RESPONSE ASSISTANT</div></div>
      <button class="mobile-close" id="closeSidebar" aria-label="Close menu">×</button>
    </div>
    <button class="new-chat" id="newChat"><span>＋</span> New conversation</button>
    <div class="side-label">EXPLORE TOPICS</div>
    <nav class="topic-nav" id="topicNav">
      <button class="topic active" data-topic="All"><span class="topic-icon">✦</span> All topics <b>⌁</b></button>
      <button class="topic" data-topic="Admissions"><span class="topic-icon red">↗</span> Admissions</button>
      <button class="topic" data-topic="Fees & Scholarships"><span class="topic-icon blue">₹</span> Fees & scholarships</button>
      <button class="topic" data-topic="Programmes"><span class="topic-icon">⌘</span> Programmes</button>
      <button class="topic" data-topic="Academics"><span class="topic-icon blue">▤</span> Academics</button>
      <button class="topic" data-topic="Examinations"><span class="topic-icon red">◷</span> Examinations</button>
      <button class="topic" data-topic="Campus Facilities"><span class="topic-icon blue">⌂</span> Campus facilities</button>
      <button class="topic" data-topic="Placements & Careers"><span class="topic-icon">↗</span> Placements & careers</button>
      <button class="topic" data-topic="Student Support"><span class="topic-icon red">♡</span> Student support</button>
      <button class="topic" data-topic="Contact & Help"><span class="topic-icon blue">◎</span> Contact & help</button>
    </nav>
    <div class="sidebar-bottom">
      <div class="mini-status"><span class="pulse"></span><div><b>AURA system operational</b><small>Curated FAQ engine · Ready</small></div></div>
      <div class="sidebar-foot">ACADEMIC AI PROJECT <span>•</span> 2026</div>
    </div>
  </aside>
  <main class="main">
    <header class="topbar">
      <button class="menu-btn" id="menuBtn" aria-label="Open menu">☰</button>
      <div class="crumb">MRIIRS <span>/</span> <b>AURA</b></div>
      <div class="top-right"><span class="secure"><i></i> STUDENT PROJECT DEMO</span><div class="avatar">AI</div></div>
    </header>
    <section class="workspace">
      <div class="hero" id="hero">
        <div class="eyebrow"><span class="eyebrow-dot"></span> YOUR CAMPUS, CONNECTED</div>
        <h1>Meet AURA.<br><span>Knowledge, connected.</span></h1>
        <p class="hero-copy"><b>MRIIRS AURA</b> — Artificial University Response Assistant. A smarter guide to university information, built to give specific answers with source links instead of guessing.</p>
        <div class="hero-meta"><span class="spark">✦</span> NLP-POWERED FAQ RETRIEVAL <span class="meta-line"></span><span>AVAILABLE 24 / 7</span></div>
      </div>
      <div class="chat-panel">
        <div class="chat-head"><div class="bot-ident"><div class="bot-orb"><span>✦</span></div><div><b>MRIIRS AURA</b><small><i class="online-dot"></i> Artificial University Response Assistant</small></div></div><button class="clear-btn" id="clearChat" title="Clear conversation">↻ <span>Reset chat</span></button></div>
        <div class="messages" id="messages" aria-live="polite">
          <div class="message-row bot-row">
            <div class="msg-avatar">✦</div><div class="message-content"><div class="message bot-message">Hello! I'm <b>MRIIRS AURA</b> — Artificial University Response Assistant.<br><br>Ask a specific question about admissions, MCA eligibility, course subjects, fees, scholarships, examinations, transport, campus facilities or placements. I use a curated university knowledge base and show the source used for each answer. If I cannot verify something, I will say so rather than guess.</div><div class="msg-time">JUST NOW <span>·</span> AURA</div></div>
          </div>
        </div>
        <div class="suggestions-wrap" id="suggestionsWrap"><div class="suggestion-label">QUICK START <span>— SELECT A QUESTION</span></div>
          <div class="suggestions" id="suggestions">
            <button class="suggestion" data-question="What is the eligibility for the two-year MCA programme?"><span class="s-icon red">↗</span> MCA eligibility <span class="arrow">↗</span></button>
            <button class="suggestion" data-question="What is the MCA fee at MRIIRS?"><span class="s-icon blue">₹</span> MCA fee details <span class="arrow">↗</span></button>
            <button class="suggestion" data-question="How do I apply for admission to MRIIRS?"><span class="s-icon">⌘</span> Admission process <span class="arrow">↗</span></button>
            <button class="suggestion" data-question="What facilities are available on the MRIIRS campus?"><span class="s-icon blue">⌂</span> Campus facilities <span class="arrow">↗</span></button>
          </div>
        </div>
        <form class="composer" id="chatForm">
          <div class="input-wrap"><span class="input-spark">✧</span><input id="messageInput" autocomplete="off" maxlength="500" placeholder="Ask AURA a specific question about MRIIRS..." aria-label="Type your question"><span class="char-count" id="charCount">0/500</span><button class="send-btn" type="submit" aria-label="Send message">➤</button></div>
          <div class="composer-foot"><span><kbd>↵</kbd> to send <span class="foot-divider">·</span> <kbd>Esc</kbd> close menu</span><span>Curated answers · Official source links</span></div>
        </form>
      </div>
      <footer class="page-footer"><span>© 2026 MRIIRS AURA <i>•</i> STUDENT MINI PROJECT</span><span><a href="https://manavrachna.edu.in/mriirs/" target="_blank" rel="noopener">OFFICIAL MRIIRS WEBSITE ↗</a><span class="footer-divider">·</span> <span class="disclaimer">Academic prototype · Verify current notices</span></span></footer>
    </section>
  </main>
</div>
<div class="toast" id="toast"></div>
<script src="{{ url_for('static', filename='app.js') }}"></script>
</body></html>
```

## 3. CSS theme — `static/style.css`

```css
:root{--bg:#07090e;--panel:#0d111a;--panel2:#111725;--line:#202838;--muted:#8490a5;--text:#f3f6fc;--blue:#287bff;--blue2:#55a1ff;--red:#ff3d50;--font:'DM Sans',sans-serif;--display:'Space Grotesk',sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;overflow-x:hidden}.ambient{position:fixed;pointer-events:none;filter:blur(100px);opacity:.14;border-radius:50%;z-index:0}.ambient-blue{width:380px;height:380px;background:#146cff;top:-160px;left:28%}.ambient-red{width:300px;height:300px;background:#ff243d;right:-170px;top:45%;opacity:.09}
.app-shell{position:relative;z-index:1;display:flex;min-height:100vh}.sidebar{width:258px;flex:0 0 258px;background:rgba(9,12,19,.94);border-right:1px solid #1a2230;padding:27px 17px 18px;display:flex;flex-direction:column;min-height:100vh}.brand{display:flex;align-items:center;gap:11px;padding:0 8px 31px}.brand-mark{height:37px;width:37px;border-radius:11px;background:linear-gradient(140deg,#236fff,#123c9a);display:grid;place-items:center;font:700 22px var(--display);position:relative;box-shadow:0 5px 22px #1455d955}.brand-mark i{position:absolute;width:7px;height:7px;border-radius:50%;background:var(--red);right:-2px;top:-2px;border:2px solid #090c13}.brand-name{font:700 17px var(--display);letter-spacing:.2px}.brand-name span{color:var(--blue2)}.brand-sub{font-size:8px;letter-spacing:1.5px;color:#78849a;margin-top:3px}.new-chat{height:43px;border:1px solid #244c8d;background:linear-gradient(100deg,#10254a,#111827);color:#dceaff;border-radius:9px;text-align:left;padding:0 13px;font:600 12px var(--font);cursor:pointer;transition:.2s}.new-chat:hover{border-color:var(--blue);transform:translateY(-1px)}.new-chat span{font-size:19px;color:#67aaff;margin-right:9px;vertical-align:-2px}.side-label,.suggestion-label{font-size:9px;letter-spacing:1.5px;color:#69758b;font-weight:700}.side-label{margin:32px 9px 13px}.topic-nav{display:grid;gap:4px}.topic{border:0;background:transparent;color:#9ba7ba;border-radius:7px;text-align:left;padding:10px 10px;font:500 11.5px var(--font);cursor:pointer;display:flex;align-items:center;gap:10px;transition:.18s}.topic:hover{background:#141c2a;color:#fff}.topic.active{background:#142342;color:#eaf2ff;box-shadow:inset 2px 0 #3686ff}.topic b{margin-left:auto;color:#5c9dff}.topic-icon{width:20px;height:20px;border-radius:6px;display:grid;place-items:center;background:#17202d;color:#c1d0e6;font-size:12px}.topic-icon.red{color:#ff6d7c;background:#2a171f}.topic-icon.blue{color:#69aaff;background:#14243d}.sidebar-bottom{margin-top:auto}.mini-status{border:1px solid #1e2a38;background:#0e151e;padding:12px;border-radius:9px;display:flex;align-items:center;gap:10px}.pulse,.online-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#36d69b;box-shadow:0 0 9px #36d69b88}.mini-status b{font-size:10px;display:block;font-weight:600}.mini-status small{display:block;color:#7c899c;font-size:9px;margin-top:4px}.sidebar-foot{font-size:8px;letter-spacing:1.1px;color:#586579;margin:18px 4px 0}.sidebar-foot span{color:var(--red);padding:0 5px}.main{flex:1;min-width:0}.topbar{height:68px;border-bottom:1px solid #1b2330;display:flex;align-items:center;justify-content:space-between;padding:0 5.1%;background:#090c13c9}.crumb{font-size:11px;color:#748197;letter-spacing:.2px}.crumb span{padding:0 10px;color:#39465b}.crumb b{color:#d9e2f1;font-weight:600}.top-right{display:flex;align-items:center;gap:17px}.secure{font-size:8px;letter-spacing:1px;color:#8290a4}.secure i{display:inline-block;width:6px;height:6px;background:#31d49a;border-radius:50%;margin-right:6px}.avatar{height:29px;width:29px;border-radius:9px;display:grid;place-items:center;background:#162b4e;border:1px solid #244a7e;color:#8fc0ff;font:700 10px var(--display)}.workspace{max-width:1000px;margin:0 auto;padding:45px 38px 20px;min-height:calc(100vh - 68px);display:flex;flex-direction:column}.hero{margin:2px 0 28px}.eyebrow{font-size:9px;letter-spacing:1.8px;font-weight:700;color:#9aa8bc;display:flex;align-items:center;gap:8px}.eyebrow-dot{height:6px;width:6px;background:var(--red);border-radius:2px;box-shadow:0 0 12px #ff3d50}.hero h1{font:600 clamp(36px,5vw,53px)/1.08 var(--display);letter-spacing:-2.6px;margin:16px 0 11px}.hero h1 span{background:linear-gradient(90deg,#5ba8ff 0%,#287bff 48%,#ff5266 100%);-webkit-background-clip:text;background-clip:text;color:transparent}.hero-copy{color:#9ba7b9;font-size:12px;line-height:1.8;max-width:515px;margin:0}.hero-meta{display:flex;align-items:center;gap:9px;font-size:8px;letter-spacing:1.15px;color:#69788e;margin-top:19px}.spark{color:#69aaff;font-size:13px}.meta-line{width:32px;height:1px;background:#34445d}.chat-panel{border:1px solid #222c3b;background:linear-gradient(145deg,rgba(15,20,30,.97),rgba(10,14,22,.98));border-radius:13px;overflow:hidden;box-shadow:0 20px 70px #0005;display:flex;flex-direction:column;min-height:455px;max-height:590px}.chat-head{height:61px;border-bottom:1px solid #202a38;display:flex;align-items:center;justify-content:space-between;padding:0 20px;flex-shrink:0}.bot-ident{display:flex;align-items:center;gap:10px}.bot-orb{height:32px;width:32px;border-radius:10px;background:linear-gradient(145deg,#164caa,#112b57);border:1px solid #2864b4;display:grid;place-items:center;color:#a7d1ff;font-size:16px;box-shadow:0 0 19px #1e6be933}.bot-ident b{font-size:11px;display:block}.bot-ident small{display:block;color:#7f8da1;font-size:9px;margin-top:4px}.online-dot{width:5px;height:5px;margin-right:4px}.clear-btn{border:1px solid #273345;border-radius:6px;background:#101722;color:#8d9bb0;padding:7px 9px;font-size:10px;cursor:pointer}.clear-btn:hover{color:#fff;border-color:#45618a}.messages{padding:20px 22px 12px;overflow-y:auto;flex:1;min-height:155px;scrollbar-width:thin;scrollbar-color:#2b3c54 transparent}.message-row{display:flex;gap:10px;margin-bottom:17px;align-items:flex-start;animation:rise .25s ease}.msg-avatar{height:25px;width:25px;flex:0 0 25px;border-radius:8px;background:#142d55;color:#80baff;display:grid;place-items:center;font-size:12px;border:1px solid #234a7b}.message-content{max-width:min(78%,620px)}.message{font-size:11px;line-height:1.75;padding:12px 14px;border-radius:3px 10px 10px 10px}.bot-message{background:#151d2a;border:1px solid #263449;color:#d4deec}.bot-message b{color:#fff}.user-row{justify-content:flex-end}.user-row .message-content{display:flex;flex-direction:column;align-items:flex-end}.user-message{background:linear-gradient(120deg,#174d9b,#153b79);border:1px solid #2867b7;color:#f1f7ff;border-radius:10px 3px 10px 10px}.user-row .msg-avatar{order:2;background:#3a1822;border-color:#74303c;color:#ff8290}.msg-time{font-size:8px;letter-spacing:.7px;color:#627087;margin:6px 2px 0}.user-row .msg-time{text-align:right}.answer-meta{display:flex;gap:8px;align-items:center;font-size:8px;color:#7792b4;margin-top:8px}.confidence{color:#63cda7}.feedback{display:flex;gap:6px;margin-top:8px}.feedback button{background:transparent;border:1px solid #2a3545;border-radius:5px;color:#8090a5;padding:4px 7px;font-size:10px;cursor:pointer}.feedback button:hover{border-color:#4d83c9;color:#bcdcff}.typing{display:flex;gap:4px;padding:15px}.typing span{height:5px;width:5px;border-radius:50%;background:#72aaff;animation:bounce .8s infinite alternate}.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}.suggestions-wrap{padding:10px 22px 14px;border-top:1px solid #1d2735;flex-shrink:0}.suggestion-label{margin-bottom:10px;font-size:8px}.suggestion-label span{color:#46556d;font-weight:500}.suggestions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.suggestion{background:#101722;border:1px solid #263246;border-radius:7px;padding:9px 10px;text-align:left;color:#c4cfdf;font:500 10px var(--font);cursor:pointer;display:flex;align-items:center;gap:8px;transition:.2s}.suggestion:hover{border-color:#3676c6;background:#132039;transform:translateY(-1px)}.s-icon{height:21px;width:21px;display:grid;place-items:center;border-radius:5px;background:#1a2536;color:#91bfff}.s-icon.red{background:#2b1821;color:#ff7584}.s-icon.blue{background:#142846;color:#75b5ff}.arrow{margin-left:auto;color:#62748e}.composer{padding:0 22px 13px;flex-shrink:0}.input-wrap{height:47px;border:1px solid #34445c;background:#0b111b;border-radius:8px;display:flex;align-items:center;padding:0 8px 0 13px;transition:.2s}.input-wrap:focus-within{border-color:#327be0;box-shadow:0 0 0 3px #1c5eb01a}.input-spark{font-size:16px;color:#6caeff;margin-right:10px}.input-wrap input{background:transparent;border:0;outline:0;color:#eef4ff;font:11px var(--font);flex:1;min-width:0}.input-wrap input::placeholder{color:#65738a}.char-count{font-size:8px;color:#526078;margin:0 10px}.send-btn{height:31px;width:34px;border:0;border-radius:6px;background:linear-gradient(135deg,#287bff,#1552bd);color:white;font-size:14px;cursor:pointer;box-shadow:0 3px 12px #1764d744;transition:.2s}.send-btn:hover{transform:translateY(-1px);filter:brightness(1.15)}.send-btn:disabled{opacity:.45;cursor:wait}.composer-foot{display:flex;justify-content:space-between;color:#65738a;font-size:8px;margin-top:8px}.composer-foot kbd{border:1px solid #344052;border-radius:3px;padding:1px 4px;font:8px var(--font);color:#aab7c9}.foot-divider{padding:0 5px;color:#3d4c61}.page-footer{display:flex;justify-content:space-between;gap:12px;margin-top:auto;padding-top:23px;color:#56647a;font-size:8px;letter-spacing:.8px}.page-footer i{font-style:normal;color:var(--red);padding:0 5px}.page-footer a{color:#789ac6;text-decoration:none}.page-footer a:hover{color:#9cc8ff}.footer-divider{padding:0 7px;color:#3b4b62}.disclaimer{letter-spacing:.2px;color:#59667b}.toast{position:fixed;bottom:22px;left:50%;transform:translate(-50%,15px);opacity:0;background:#172338;border:1px solid #34547e;color:#dcecff;padding:10px 16px;border-radius:7px;font-size:11px;z-index:10;transition:.25s;pointer-events:none}.toast.show{opacity:1;transform:translate(-50%,0)}.menu-btn,.mobile-close{display:none}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}@keyframes bounce{to{transform:translateY(-5px);opacity:.5}}
@media(max-width:850px){.sidebar{width:230px;flex-basis:230px}.workspace{padding:36px 25px 18px}.page-footer{font-size:7px}}
@media(max-width:650px){.sidebar{position:fixed;z-index:20;left:-270px;top:0;bottom:0;width:258px;transition:left .25s;box-shadow:15px 0 50px #0008}.sidebar.open{left:0}.mobile-close{display:block;margin-left:auto;background:transparent;border:0;color:#aab8ca;font-size:22px}.menu-btn{display:block;background:transparent;border:0;color:#b5c2d4;font-size:17px;margin-right:12px}.topbar{justify-content:flex-start;padding:0 17px;height:59px}.top-right{margin-left:auto}.secure{font-size:7px}.workspace{padding:30px 15px 15px}.hero h1{font-size:42px}.hero-copy{font-size:11px}.chat-panel{min-height:500px;max-height:calc(100vh - 330px)}.chat-head{padding:0 13px}.messages{padding:16px 13px}.suggestions-wrap{padding:10px 13px}.composer{padding:0 13px 12px}.suggestions{grid-template-columns:1fr}.suggestion{padding:8px}.page-footer{flex-direction:column;line-height:1.8}.message-content{max-width:88%}.crumb{font-size:10px}}

/* AURA refinements: preserve the original black / electric-blue / red visual identity. */
.bot-message{white-space:pre-line;font-size:12px;line-height:1.85}
.bot-message a{color:#75b5ff;text-decoration:underline;text-underline-offset:2px;overflow-wrap:anywhere}
.answer-meta{flex-wrap:wrap}
.answer-meta .confidence{font-weight:700;letter-spacing:.35px}
.answer-source{font-size:9px;color:#91a2ba;margin-top:7px;line-height:1.6}
.answer-source a{color:#75b5ff;text-decoration:none}
.answer-source a:hover{text-decoration:underline}
.answer-updated{color:#687991;margin-left:7px}
.feedback{margin-top:9px}
.message-content{min-width:0}
@media(max-width:650px){.brand-sub{font-size:7px;letter-spacing:.8px}.hero-meta{flex-wrap:wrap}}

```

## 4. Browser logic — `static/app.js`

```javascript
const form=document.getElementById('chatForm'), input=document.getElementById('messageInput'), messages=document.getElementById('messages'), sendBtn=form.querySelector('.send-btn'), charCount=document.getElementById('charCount'), suggestionsWrap=document.getElementById('suggestionsWrap'), toast=document.getElementById('toast');
let busy=false;
function timeNow(){return new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}).toUpperCase()}
function scrollBottom(){messages.scrollTop=messages.scrollHeight}
function toastMsg(msg){toast.textContent=msg;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2300)}
function appendTextWithLinks(node,text){
 const urlRegex=/(https?:\/\/[^\s]+)/g;let last=0;
 text.replace(urlRegex,(raw,index)=>{node.append(document.createTextNode(text.slice(last,index)));const clean=raw.replace(/[.,)]$/,'');const a=document.createElement('a');a.href=clean;a.textContent=clean;a.target='_blank';a.rel='noopener noreferrer';node.append(a);if(clean.length<raw.length)node.append(document.createTextNode(raw.slice(clean.length)));last=index+raw.length;return raw;});
 node.append(document.createTextNode(text.slice(last)));
}
function addMessage(text,who,meta=null){
 const row=document.createElement('div');row.className=`message-row ${who==='user'?'user-row':'bot-row'}`;
 const avatar=document.createElement('div');avatar.className='msg-avatar';avatar.textContent=who==='user'?'YOU':'✦';
 const content=document.createElement('div');content.className='message-content';
 const bubble=document.createElement('div');bubble.className=`message ${who==='user'?'user-message':'bot-message'}`;
 if(who==='bot')appendTextWithLinks(bubble,text);else bubble.textContent=text;
 content.append(bubble);
 const stamp=document.createElement('div');stamp.className='msg-time';stamp.textContent=`${timeNow()} · ${who==='user'?'YOU':'MRIIRS AURA'}`;content.append(stamp);
 if(meta){
  const line=document.createElement('div');line.className='answer-meta';
  const match=document.createElement('span');match.className='confidence';match.textContent=meta.match==='strong'?'● STRONG TOPIC MATCH':meta.match==='relevant'?'● RELEVANT MATCH':'● NOT IN KNOWLEDGE BASE';
  const cat=document.createElement('span');cat.textContent=meta.category||'General';line.append(match,cat);content.append(line);
  if(meta.source_url){const src=document.createElement('div');src.className='answer-source';src.append(document.createTextNode('Source: '));const a=document.createElement('a');a.href=meta.source_url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=meta.source_name||'Official MRIIRS page';src.append(a);if(meta.last_verified){const updated=document.createElement('span');updated.className='answer-updated';updated.textContent=`· reviewed ${meta.last_verified}`;src.append(updated)}content.append(src)}
  if(meta.match!=='none'){
   const fb=document.createElement('div');fb.className='feedback';
   const yes=document.createElement('button');yes.type='button';yes.textContent='👍 Helpful';yes.addEventListener('click',()=>sendFeedback('up'));
   const no=document.createElement('button');no.type='button';no.textContent='👎 Not helpful';no.addEventListener('click',()=>sendFeedback('down'));
   fb.append(yes,no);content.append(fb);
  }
 }
 row.append(avatar,content);messages.append(row);scrollBottom();
}
function showTyping(){const row=document.createElement('div');row.id='typingRow';row.className='message-row bot-row';row.innerHTML='<div class="msg-avatar">✦</div><div class="message-content"><div class="message bot-message typing"><span></span><span></span><span></span></div></div>';messages.append(row);scrollBottom()}
async function sendFeedback(vote){try{await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vote})});toastMsg('Thanks for your feedback!')}catch(e){toastMsg('Feedback could not be sent.')}}
function addSuggestions(items){if(!items||!items.length)return;const wrap=document.createElement('div');wrap.className='message-row bot-row';const spacer=document.createElement('div');spacer.className='msg-avatar';spacer.style.visibility='hidden';const list=document.createElement('div');list.className='message-content';const label=document.createElement('div');label.className='answer-source';label.textContent='Related questions';list.append(label);items.forEach(q=>{const b=document.createElement('button');b.className='feedback';b.style.display='inline-block';b.style.margin='5px 5px 0 0';b.style.padding='7px 9px';b.textContent=q;b.addEventListener('click',()=>ask(q));list.append(b)});wrap.append(spacer,list);messages.append(wrap);scrollBottom()}
async function ask(question){if(busy)return;const q=question.trim();if(!q)return;busy=true;sendBtn.disabled=true;addMessage(q,'user');input.value='';charCount.textContent='0/500';suggestionsWrap.style.display='none';showTyping();
 try{const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})});const data=await res.json();document.getElementById('typingRow')?.remove();if(!res.ok)throw new Error(data.error||'Request failed');addMessage(data.answer,'bot',data);addSuggestions(data.suggestions)}catch(err){document.getElementById('typingRow')?.remove();addMessage('I could not connect to the AURA service. Check that the Flask server is running, then refresh this page.','bot');}finally{busy=false;sendBtn.disabled=false;input.focus()}}
form.addEventListener('submit',e=>{e.preventDefault();ask(input.value)});
input.addEventListener('input',()=>charCount.textContent=`${input.value.length}/500`);
document.querySelectorAll('.suggestion').forEach(b=>b.addEventListener('click',()=>ask(b.dataset.question)));
document.getElementById('clearChat').addEventListener('click',resetChat);
document.getElementById('newChat').addEventListener('click',resetChat);
function resetChat(){messages.innerHTML='';addMessage('Hello! I am MRIIRS AURA — Artificial University Response Assistant. Ask a specific question about admissions, programmes, fees, academics, examinations, campus facilities, placements or student support. I will show the source for each matched answer and will not guess when information is missing.','bot');suggestionsWrap.style.display='';toastMsg('Conversation reset.')}
document.getElementById('topicNav').addEventListener('click',e=>{const btn=e.target.closest('.topic');if(!btn)return;document.querySelectorAll('.topic').forEach(x=>x.classList.remove('active'));btn.classList.add('active');const topic=btn.dataset.topic;if(topic==='All'){resetChat();return}ask(`Give me the main information about ${topic} at MRIIRS`) });
document.getElementById('menuBtn').addEventListener('click',()=>document.getElementById('sidebar').classList.add('open'));
document.getElementById('closeSidebar').addEventListener('click',()=>document.getElementById('sidebar').classList.remove('open'));
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.getElementById('sidebar').classList.remove('open')});
fetch('/api/health').then(r=>r.json()).then(d=>console.info(`${d.brand} (${d.full_form}) ready: ${d.faq_count} curated FAQs`)).catch(()=>{});

```

## 5. Automated tests — `test_chatbot.py`

```python
import unittest
import app as chatbot

class AuraTests(unittest.TestCase):
    def setUp(self):
        self.client = chatbot.app.test_client()

    def ask(self, question):
        response = self.client.post('/api/chat', json={'message': question})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_homepage_brand(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRIIRS AURA', response.data)
        self.assertIn(b'Artificial University Response Assistant', response.data)

    def test_health_reports_full_form_and_faq_count(self):
        data = self.client.get('/api/health').get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['brand'], 'MRIIRS AURA')
        self.assertEqual(data['full_form'], 'Artificial University Response Assistant')
        self.assertGreaterEqual(data['faq_count'], 50)

    def test_mca_bcom_eligibility_specific(self):
        data = self.ask('I completed B.Com. Can I apply for the two-year MCA?')
        self.assertIn('Mathematics', data['answer'])
        self.assertIn('50%', data['answer'])
        self.assertEqual(data['category'], 'Programmes')

    def test_mca_fee_is_not_general_fee_answer(self):
        data = self.ask('What is the MCA fee?')
        self.assertIn('2,18,100', data['answer'])
        self.assertIn('MCA', data['matched_question'])

    def test_admission_process_has_actual_steps(self):
        data = self.ask('How can I apply for admission?')
        self.assertIn('online', data['answer'].lower())
        self.assertIn('application/reference number', data['answer'].lower())

    def test_hostel_answer_has_specific_details(self):
        data = self.ask('Does MRIIRS have hostel accommodation?')
        self.assertIn('single, double and triple', data['answer'])

    def test_unrelated_query_uses_safe_fallback(self):
        data = self.ask('What is the current cricket score in Delhi?')
        self.assertIsNone(data['matched_question'])
        self.assertIn("don't have a verified answer", data['answer'])
        self.assertEqual(data['match'], 'none')

    def test_fee_question_with_programme_anchor(self):
        data = self.ask('Tell me the fee structure for MCA with installments')
        self.assertIn('2,18,100', data['answer'])
        self.assertEqual(data['category'], 'Programmes')

    def test_categories(self):
        categories = self.client.get('/api/categories').get_json()
        self.assertIn('Admissions', categories)
        self.assertIn('Programmes', categories)
        self.assertIn('Contact & Help', categories)

    def test_empty_question(self):
        self.assertEqual(self.client.post('/api/chat', json={'message': '  '}).status_code, 400)

    def test_long_question(self):
        self.assertEqual(self.client.post('/api/chat', json={'message': 'x' * 501}).status_code, 400)


    def test_mca_without_maths_gets_direct_eligibility_answer(self):
        data = self.ask('Can I apply for MCA without Mathematics?')
        self.assertIn('Mathematics', data['answer'])
        self.assertIn('10+2', data['answer'])
        self.assertEqual(data['category'], 'Programmes')

    def test_combined_mca_duration_and_fee(self):
        data = self.ask('What is the duration and fee of MCA?')
        self.assertIn('2 years', data['answer'])
        self.assertIn('2,18,100', data['answer'])
        self.assertIn('duration and fee', (data['matched_question'] or '').lower())

    def test_rechecking_query_routes_to_revaluation(self):
        data = self.ask('How can I request rechecking of my examination result?')
        self.assertIn('revaluation', (data['matched_question'] or '').lower())

    def test_class_timings_do_not_return_an_unrelated_answer(self):
        data = self.ask('What are the class timings for MCA?')
        self.assertIsNone(data['matched_question'])
        self.assertEqual(data['match'], 'none')

    def test_aura_identity_question(self):
        data = self.ask('What is MRIIRS AURA?')
        self.assertIn('Artificial University Response Assistant', data['answer'])

    def test_feedback(self):
        self.assertEqual(self.client.post('/api/feedback', json={'vote': 'up'}).status_code, 200)
        self.assertEqual(self.client.post('/api/feedback', json={'vote': 'wrong'}).status_code, 400)

if __name__ == '__main__':
    unittest.main(verbosity=2)

```
