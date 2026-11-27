# MRIIRS AURA — Artificial University Response Assistant

**Tagline:** Ask. Explore. Discover.  
**Project:** AI / NLP-based University FAQ Chatbot mini project  
**Institutional context:** Manav Rachna International Institute of Research and Studies (MRIIRS)

MRIIRS AURA is a local web-based chatbot that retrieves detailed answers from a structured, source-linked university knowledge base. It is designed to respond with programme-specific information, related questions and the official source page. It does not invent answers when it cannot find a reliable match.

## What changed in this improved version

- Expanded the knowledge base from 28 short entries to **79 detailed FAQs** across 11 topic areas.
- Added useful question aliases and phrase normalisation so students can ask questions in more than one way.
- Replaced the earlier basic cosine/keyword blend with **BM25-style weighted retrieval**, question/alias matching and entity anchors (for example, MCA, B.Com., MRNAT and ERP).
- Search deliberately uses question titles, aliases and curated keywords rather than long answer text. This reduces accidental matches caused by words that appear only incidentally in an answer.
- Added stricter confidence handling. When the best result is weak or ambiguous, AURA says it does not have a verified answer instead of returning an unrelated FAQ.
- Each matched answer includes its source name, official URL and review date.
- Kept the original visual theme: near-black background, electric blue highlights and red accents.
- Renamed every visible project label to **MRIIRS AURA — Artificial University Response Assistant**.

## Features

1. Natural-language question input.
2. Topic navigation for Admissions, Fees & Scholarships, Programmes, Academics, Examinations, Campus Facilities, Placements & Careers, Student Support and Contact & Help.
3. Searchable JSON knowledge base with categories, question aliases, keywords and source links.
4. NLP preprocessing: Unicode normalisation, lowercasing, tokenisation, stop-word filtering and synonym mapping.
5. BM25-style ranking with phrase and programme-name boosts.
6. Safe fallback for unsupported or ambiguous questions.
7. Related-question suggestions, feedback buttons and responsive interface.
8. Flask JSON API and local execution without a paid LLM key.

## Folder structure

```text
MRIIRS_AURA/
├── app.py                    # Flask backend and NLP retrieval engine
├── knowledge_base.json       # 79 curated FAQ records
├── templates/
│   └── index.html            # Chatbot interface
├── static/
│   ├── style.css             # Dark UI styling (blue/red accents)
│   └── app.js                # Browser-side chat logic
├── test_chatbot.py           # Backend tests
├── requirements.txt          # Python dependencies
├── RUN_WINDOWS.bat           # Windows one-click launcher
├── run_mac_linux.sh          # macOS/Linux launcher
├── PROJECT_REPORT.docx       # Formatted academic report
├── PROJECT_REPORT.md         # Report source
├── SOURCE_CODE.md            # Source-code listing
├── SOURCES.md                # Official reference URLs and verification notes
├── TESTING.md                # Test plan and commands
└── LICENSE.txt
```

## Requirements

- Python **3.10 or newer**
- Internet connection for the first dependency installation (Flask only); the chatbot itself runs locally
- Windows 10/11, macOS or Linux

## Run on Windows (recommended)

1. Download and extract `MRIIRS_AURA_Mini_Project.zip`.
2. Open the extracted `MRIIRS_AURA` folder.
3. Double-click **`RUN_WINDOWS.bat`**.
4. The script creates a virtual environment, installs Flask and starts the server.
5. Open **http://127.0.0.1:5000** in Chrome, Edge or Firefox.
6. Keep the command window open while using AURA. Press `Ctrl + C` in that window to stop the server.

If Windows blocks the script, right-click it and choose **Run** or use the manual commands below.

## Run manually (Windows PowerShell)

Open PowerShell in the project folder and run:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Run on macOS / Linux

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

Or run manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Test the backend

After dependencies are installed, run:

```bash
python -m unittest -v
```

The tests cover page branding, health endpoint, detailed MCA eligibility, MCA fee retrieval, admissions workflow, hostel details, unsupported questions, category output, input validation and feedback handling.

## How to use AURA effectively

AURA works best when a question includes the topic or programme name. For example:

- "Can a B.Com graduate apply for the two-year MCA if they studied Mathematics?"
- "What is the MCA fee and how is it split into instalments?"
- "Which documents are required for postgraduate admission?"
- "How do I request revaluation of marks?"
- "Does the campus have hostel accommodation and transport?"
- "How can I register for placement drives?"

When AURA cannot verify a relevant record, it provides a safe fallback and will not choose an unrelated answer just to respond.

## How the system works

1. The browser sends the user's question to `POST /api/chat`.
2. Flask validates the input length and emptiness.
3. Text is normalised and tokenised; common stop words and known variants are handled.
4. The retrieval engine compares the query with FAQ questions, aliases, keywords and categories.
5. BM25-style weights reward rare, meaningful terms. Phrase matches and strong anchors such as "MCA" receive additional weight.
6. If the score is sufficiently high and not ambiguous, AURA returns the detailed answer with its official source. Otherwise it returns a safe fallback.
7. The browser displays the answer, match type, source link and related questions.

This is a **retrieval-based NLP chatbot**, not a generative LLM. It returns curated information rather than generating new facts.

## Update the knowledge base

Open `knowledge_base.json` and add a new object using the existing structure:

```json
{
  "id": "FAQ069",
  "category": "Admissions",
  "q": "How can I update my application details?",
  "a": "Write a detailed answer here and include the correct official process.",
  "keywords": ["application", "update", "edit", "admission"],
  "aliases": ["Can I correct my form?", "How do I edit my application?"],
  "source_name": "MRIIRS - Official admission process",
  "source_url": "https://manavrachna.edu.in/mriirs/admissions/admission-process",
  "last_verified": "27 November 2026"
}
```

Use a unique ID. Include several natural question phrasings in `aliases`, a concise discriminative keyword list, and an official source URL. Do not add rumours or unverified fee, placement, admission or exam claims. Restart Flask after editing the JSON file.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Chatbot interface |
| GET | `/api/health` | System status, brand and FAQ counts |
| GET | `/api/categories` | List knowledge-base categories |
| POST | `/api/chat` | Retrieve an answer from a JSON message |
| POST | `/api/feedback` | Demonstration feedback acknowledgement |

Example request body:

```json
{"message": "What is the eligibility for the two-year MCA programme?"}
```

## Accuracy and limitations

- This is a student academic prototype, **not an official MRIIRS service** and not endorsed by the university.
- University details may change. Some facts in the knowledge base were checked against official MRIIRS pages on **27 November 2026**; the answer shows its source and review date.
- Fee tables, scholarship policies, admission dates, transport tariffs, examination schedules and department instructions can be revised. Always confirm the current notice or written advice from the relevant office before making payments or decisions.
- AURA cannot access private student records, attendance, personal results, ERP accounts, application status, payments or live seat availability.
- AURA does not provide a paid generative AI connection. Its retrieval ranking is deterministic and depends on the quality and coverage of the JSON knowledge base.

## Troubleshooting

- **`python` or `py` not recognised:** install Python 3.10+ and enable the PATH option during installation.
- **PowerShell blocks activation:** use `RUN_WINDOWS.bat`, or run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` only in the current PowerShell session, then activate `.venv` again.
- **`ModuleNotFoundError: flask`:** activate the virtual environment and run `python -m pip install -r requirements.txt`.
- **Port 5000 is busy:** close the other local server or change the port in the final `app.run(...)` statement, then open the matching local URL.
- **The browser cannot connect:** keep the terminal open and ensure it shows that Flask is running.
- **An answer is missing or too broad:** try including the programme/topic and add a sourced FAQ record to `knowledge_base.json`.

## Academic project identity

**Title:** MRIIRS AURA — Artificial University Response Assistant  
**Tagline:** Ask. Explore. Discover.  
**Domain:** Artificial Intelligence / Natural Language Processing  
**Implementation:** Python, Flask, JSON, HTML5, CSS3 and JavaScript
