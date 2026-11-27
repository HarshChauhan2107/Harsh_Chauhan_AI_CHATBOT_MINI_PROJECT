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
