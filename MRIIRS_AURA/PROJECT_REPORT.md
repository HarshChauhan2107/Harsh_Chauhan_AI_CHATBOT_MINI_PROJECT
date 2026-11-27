# MINI PROJECT REPORT

# MRIIRS AURA — Artificial University Response Assistant

**Tagline:** Ask. Explore. Discover.  
**Subject:** Artificial Intelligence  
**Programme:** Master of Computer Applications (MCA)  
**Project Type:** Web-based AI / NLP mini project  
**Submitted by:** Harsh Chauhan  
**Institution:** Manav Rachna International Institute of Research and Studies (MRIIRS)  
**Technology:** Python, Flask, JSON, HTML5, CSS3 and JavaScript  
**Knowledge base:** 79 source-linked FAQ records  
**Review date for source material:** 27 November 2026

---

## Abstract

MRIIRS AURA (Artificial University Response Assistant) is a web-based university FAQ chatbot developed as an academic Artificial Intelligence mini project. It is intended to help prospective applicants and current students find structured information about Manav Rachna International Institute of Research and Studies (MRIIRS). The chatbot covers institutional information, admissions, programmes, MCA eligibility and curriculum, fees, scholarships, academic calendars, examinations, facilities, transport, placements, student support and contact information.

The improved version addresses a common weakness of basic FAQ chatbots: returning a loosely related answer simply because a few words overlap. AURA uses natural-language preprocessing, synonym normalisation, BM25-style weighted retrieval, phrase matching and named-topic boosts. The knowledge base contains 79 detailed, curated FAQ records, each with question aliases, keywords and an official source URL. A confidence threshold and ambiguity check prevent weak matches from being presented as reliable answers. When the system does not find a suitable record, it explicitly says that it cannot verify the answer and provides an official website route.

The frontend uses HTML, CSS and JavaScript; the backend uses Python and Flask. The application runs locally and does not require a paid generative AI API. It is a retrieval-based academic prototype, not an official MRIIRS service and not a replacement for current university notices or office confirmation.

## 1. Introduction

Universities publish information across programme pages, admission portals, fee tables, academic calendars, notices and student-support pages. A student may need to visit several pages to answer a single question. A FAQ chatbot can reduce this effort by accepting natural-language questions and retrieving a relevant, organised answer from a knowledge base.

MRIIRS AURA demonstrates how Natural Language Processing (NLP) and information retrieval can be used to create a practical university information assistant. The interface offers topic navigation and related questions, while the backend identifies the closest FAQ and returns both the answer and its source link.

## 2. Problem Statement

A simple keyword-matching chatbot may return a general or unrelated answer when the user's wording differs from the stored question. For example, a B.Com graduate asking about MCA eligibility needs the conditions related to Mathematics and qualifying marks, not a generic description of MCA. Similarly, a person asking for the MCA fee should not receive the fee for another programme.

The problem is to build a system that can interpret different phrasings, distinguish programme-specific topics, provide sufficiently detailed answers and avoid guessing when the knowledge base does not contain a verified answer.

## 3. Objectives

1. Develop a responsive web-based chatbot for common MRIIRS questions.
2. Build a structured knowledge base with detailed answers, aliases, keywords and source links.
3. Apply NLP preprocessing to user-entered questions.
4. Rank relevant FAQ records using weighted text retrieval and phrase/entity signals.
5. Prevent unrelated answers through relevance thresholds and ambiguity checks.
6. Display the official source used for each retrieved answer.
7. Preserve a premium black interface with electric-blue and red accents.
8. Provide a simple local setup process and automated backend tests.

## 4. Scope and Limitations

AURA covers 11 subject categories: About MRIIRS, Admissions, Fees & Scholarships, Programmes, Academics, Examinations, Campus Facilities, Placements & Careers, Student Support, Contact & Help and General.

The chatbot does not connect to private student records, the ERP database, attendance, personal examination results, payment ledgers, application status, hostel inventory or live transport availability. It does not generate new factual information with a large language model. Its response quality depends on the accuracy, freshness and completeness of its curated JSON data. Dynamic details such as fees, scholarships, admission deadlines, transport tariffs and examination dates must be checked on the linked official page before a decision is made.

## 5. Tools and Technologies

| Component | Technology | Purpose |
|---|---|---|
| Frontend structure | HTML5 | Chat layout and topic navigation |
| Visual styling | CSS3 | Dark theme, blue/red accents, responsiveness and animation |
| Client-side logic | JavaScript | Sending questions, displaying answers, feedback and suggestions |
| Backend | Python 3 | NLP preprocessing and answer retrieval |
| Web framework | Flask | Local server and JSON API |
| Knowledge base | JSON | Structured question-answer-source records |
| Text processing | Python standard library | Unicode normalisation, tokenisation and synonym mapping |
| Retrieval | BM25-style scoring | Rank relevant FAQ documents |
| Tests | unittest and Flask test client | API and matching checks |

## 6. System Architecture

```text
+---------------------------+
|       Student / User      |
+-------------+-------------+
              |
              v
+---------------------------+
| Browser Interface         |
| HTML + CSS + JavaScript   |
+-------------+-------------+
              | POST /api/chat
              v
+---------------------------+
| Flask Backend             |
| Input validation          |
| Text normalisation        |
| Tokenisation and synonyms |
+-------------+-------------+
              |
              v
+---------------------------+
| FAQ Retrieval Engine      |
| BM25-style term ranking   |
| Alias / phrase matching   |
| Programme-anchor boosts   |
| Threshold and ambiguity   |
+-------------+-------------+
              |
              v
+---------------------------+
| knowledge_base.json       |
| 79 curated FAQ records    |
| Answers + source URLs     |
+-------------+-------------+
              |
              v
+---------------------------+
| Answer + Source + Related |
| Questions / Safe Fallback |
+---------------------------+
```

## 7. Knowledge Base Design

Each JSON object represents one FAQ record. Its principal fields are:

- `id`: unique record identifier.
- `category`: topic area shown in the UI.
- `q`: canonical question.
- `a`: detailed, readable answer.
- `keywords`: discriminative terms used during retrieval.
- `aliases`: alternate ways a user may ask the same question.
- `source_name` and `source_url`: official page associated with the answer.
- `last_verified`: review date recorded by the project.

The knowledge base contains **79 unique records across 11 categories**. Search is intentionally based mainly on the question, aliases and keywords. Long answer text is excluded from matching because incidental words in an answer can create false matches.

## 8. NLP and Retrieval Methodology

### 8.1 Input validation

The backend accepts a natural-language question from the browser. Empty input and questions longer than 500 characters are rejected with a clear error message.

### 8.2 Text normalisation

Text is converted to lowercase, Unicode-normalised and standardised by replacing punctuation with spaces. Common degree abbreviations such as B.Com., B.Sc. and BCA are normalised to a single searchable token. Selected multiword phrases, such as “Master of Computer Applications”, are mapped to their abbreviations.

### 8.3 Tokenisation and stop-word handling

The normalised sentence is split into tokens. Common grammatical words are removed, while meaningful terms such as `not`, `MCA`, `fee`, `eligibility` and `Mathematics` are retained. Synonym mapping standardises frequently used variants, such as “tuition” to “fee” and “apply” to “admission”.

### 8.4 BM25-style ranking

AURA uses a BM25-style relevance function. A term receives more weight when it is relatively rare across the FAQ collection and occurs in the candidate FAQ. The core BM25 component is:

\[
IDF(t)=\ln\left(1+rac{N-n_t+0.5}{n_t+0.5}ight)
\]

\[
BM25(D,Q)=\sum_{t\in Q} IDF(t)\cdotrac{f(t,D)(k_1+1)}{f(t,D)+k_1\left(1-b+brac{|D|}{avgdl}ight)}
\]

where `N` is the number of FAQ records, `n_t` is the number of records containing term `t`, `f(t,D)` is the term frequency in document `D`, `|D|` is the document length, and `avgdl` is the average document length.

The implementation combines a scaled BM25 score with weighted token coverage, ordinary token coverage, exact/partial phrase bonuses and programme/entity-anchor boosts. These extra signals help distinguish questions such as “MCA fee” from general fee questions.

### 8.5 Relevance threshold and ambiguity handling

AURA uses a minimum relevance threshold and checks for close competing results. If a query is weak or ambiguous, the backend does not return the top-ranked FAQ as though it were correct. It responds with a safe fallback and may show relevant question suggestions.

The score is an internal ranking measure, **not a statistically calibrated probability**. The interface therefore displays a qualitative match label rather than a percentage.

### 8.6 Entity-aware safeguards

If a user mentions a specific degree and asks for its fee, the retrieval layer requires a fee record that also contains that degree. For example, the MCA fee cannot be reused as a BCA fee. Degree abbreviations are normalised before matching so a query containing B.Com. can be compared with the relevant B.Com eligibility record.

## 9. Working of the Application

1. User opens the local web page and enters a question.
2. JavaScript sends the question as JSON to `POST /api/chat`.
3. Flask validates the input.
4. The NLP module normalises the text and creates query tokens.
5. The retrieval engine scores the candidate FAQ records.
6. The system applies programme-specific checks and the minimum relevance threshold.
7. A matching answer is returned with its category, official source URL, review date and related questions. If no reliable match exists, a safe fallback is returned.
8. JavaScript renders the answer and turns source URLs into clickable links.

## 10. Application Modules

**User Interface Module:** Displays the AURA brand, topic navigation, chat window, quick prompts and input composer.

**Input Processing Module:** Validates the question and converts it into normalised tokens.

**Knowledge Base Module:** Loads the JSON FAQ records and makes source information available with each answer.

**Retrieval Module:** Calculates weighted relevance, phrase overlap and programme-anchor signals; returns a reliable match or fallback.

**Response Module:** Sends structured JSON containing the answer, category, match label, source and related questions.

**Feedback Module:** Acknowledges helpful/not-helpful input for demonstration purposes. It does not store personal data or persist a training dataset.

## 11. API Design

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the chatbot interface |
| GET | `/api/health` | Returns server status, AURA identity and FAQ counts |
| GET | `/api/categories` | Returns available FAQ categories |
| POST | `/api/chat` | Accepts a question and returns answer/source/suggestions |
| POST | `/api/feedback` | Acknowledges a valid feedback vote |

Example request:

```json
{{"message": "Can a B.Com graduate apply for the two-year MCA?"}}
```

The response contains the answer, matched question, category, qualitative match label, source name, source URL, review date and related questions.

## 12. Testing and Validation

The project includes a `unittest` suite. The planned automated checks cover the homepage title and full form, health endpoint, MCA eligibility for a B.Com graduate, MCA-specific fee response, admission steps, hostel details, unrelated-question fallback, topic categories, empty/overlong input and feedback validation.

| Test case | Input / action | Expected outcome |
|---|---|---|
| Brand check | Load `/` | MRIIRS AURA and full form appear |
| MCA eligibility | B.Com-to-MCA question | Returns Mathematics and 50% conditions |
| MCA fee | Ask MCA fee | Returns only the MCA-specific fee entry and caution |
| Admission | Ask application process | Explains online application and reference number |
| Hostel | Ask hostel availability | Provides room categories and caveat to confirm availability |
| Unrelated query | Ask about cricket score | Safe no-match response; no unrelated FAQ is returned |
| Wrong programme fee | Ask BCA fee where no verified record exists | Safe no-match response |
| Input validation | Empty / more than 500 characters | HTTP 400 error |

The source package includes the exact commands for running the test suite. The build environment used to generate this package did not have Flask installed and could not download packages; therefore the Flask test-client suite was included but not executed in this environment. Python syntax compilation, JSON structure checks and direct retrieval checks were completed during project preparation.

## 13. Security, Privacy and Responsible Use

The application binds to `127.0.0.1` by default, making it a local demonstration. It does not request student passwords, OTPs, payment PINs or personal records. Feedback is acknowledged but not stored. The project should not be represented as an official university chatbot. The source URL and last-reviewed date are displayed to encourage verification.

## 14. Limitations and Future Enhancements

Current limitations include a finite FAQ collection, no live access to university systems, no retrieval of private records, and no generative reasoning beyond curated answers. Future versions could include a controlled administrator interface for reviewing new FAQs, scheduled source verification, richer multilingual query support, semantic embeddings, a document-search pipeline over approved public circulars, analytics on unanswered questions and a secure institutional deployment after formal approval.

## 15. Conclusion

MRIIRS AURA demonstrates an end-to-end AI/NLP information retrieval application built with Python, Flask, JSON, HTML, CSS and JavaScript. The improved system is more specific than a basic keyword chatbot because it uses curated aliases, weighted ranking, entity-aware checks, source links and safe fallback handling. The project provides a functional base that can be expanded as verified university information becomes available. Its most important design principle is that a transparent no-answer response is better than a confident but unrelated answer.

## References

1. MRIIRS - About MRIIRS: https://manavrachna.edu.in/mriirs/about/about-mriirs
2. MRIIRS - MCA Programme: https://manavrachna.edu.in/mriirs/academics/master-of-computer-applications
3. MRIIRS - Admission Process: https://manavrachna.edu.in/mriirs/admissions/admission-process
4. MRIIRS - Fee Structure: https://manavrachna.edu.in/mriirs/admissions/fee-structure
5. MRIIRS - Financial Aid and Scholarships: https://manavrachna.edu.in/mriirs/admissions/financial-aid-and-scholarships
6. MRIIRS - Academic Calendar: https://manavrachna.edu.in/mriirs/academics/academic-calendar
7. MRIIRS - Campus Facilities: https://manavrachna.edu.in/mriirs/life/campus-facilities
8. MRIIRS - Transport Facility: https://manavrachna.edu.in/mriirs/life/transport-facility
9. MRIIRS - Students Welfare: https://manavrachna.edu.in/mriirs/life/dsw
10. MRIIRS - Student Facilitation Centre: https://manavrachna.edu.in/mriirs/admissions/student-falicitation-centre
11. MRIIRS - Placement Overview: https://manavrachna.edu.in/mriirs/placements/overview
12. Manav Rachna - Quick Contacts: https://manavrachna.edu.in/mru/about/quick-contacts

*Public source material reviewed for this academic prototype on 27 November 2026. Dynamic details must be reconfirmed against current official notices.*
