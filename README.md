# Pitch Practice Partner

### *AI Interview & Communication Simulator*

> **Practice realistic conversations with AI personas instead of answering static question lists.**

---

## 📌 Overview

**Pitch Practice Partner** is a modern, interactive communication simulator designed to help professionals, students, job candidates, and founders prepare for high-stakes speaking scenarios. 

Whether preparing for an executive client pitch, a behavioral HR interview, a technical architecture defense, or an academic viva, Pitch Practice Partner creates dynamic, persona-driven practice environments.

---

## 🛑 Problem

Traditional interview and communication prep tools suffer from major limitations:
* **Static Question Lists:** Reading lists of FAQs does not test real-time conversational adaptability.
* **Lack of Dynamic Follow-ups:** Real interviewers probe deeper based on what candidates actually say.
* **One-Way Monologues:** Speaking to a mirror or a basic timer lacks conversational tension, active listening, and audience context.
* **Vague Scores Without Guidance:** Telling a candidate they scored "72/100" without explaining what happened, why it matters, or what to do next provides little practical value.

---

## 💡 Solution

**Pitch Practice Partner** bridges this gap by offering:
1. **Interactive Persona Simulations:** Practice with specialized AI interviewers, moderators, client executives, and evaluators.
2. **Context-Aware Dynamic Follow-ups:** Experience dynamic back-and-forth dialogue tailored to your actual responses, the chosen scenario, and difficulty.
3. **Structured Scenario & Persona Library:** Scenarios across HR interviews, technical coding/system design, investor pitches, academic vivas, team discussions, and managerial leadership.
4. **Conversation Intelligence (Phase 4):** Pure evidence-based extraction of linguistic features, question responses, topical coverage, and persona concerns.
5. **Evaluation & Scoring Engine (Phase 5):** Deterministic, evidence-backed multi-dimensional scoring (0–100 scale) with normalized overall scores.
6. **Explainable Feedback Engine (Phase 6):** Evidence-backed **WHAT / WHY / EVIDENCE / IMPACT / ACTION** feedback framework providing concrete, prioritized practice steps.
7. **Session History & Longitudinal Analytics (Phase 7):** Persistent SQLite storage, historical detail inspection, chronological progress tracking, recurring pattern detection, and neutral session comparisons.

---

## 🚀 Current Phase

**Phase 7 — Session History & Longitudinal Analytics**

> [!NOTE]
> Phase 7 introduces a lightweight local persistence layer powered by Python's standard-library SQLite engine. Completed practice sessions, full transcripts, dimensional evaluation scores, and explainable feedback are stored permanently without recalculation. Users can review past sessions, track longitudinal progress over time, discover recurring strength/improvement themes, and compare sessions side-by-side using objective, neutral descriptive language.

---

## 💡 Explainable Feedback Architecture (Phase 6)

```text
                  Completed Practice Session Transcript
                                    │
                                    ▼
                      ConversationAnalyzer (Phase 4)
                       [Structured Evidence Object]
                                    │
                                    ▼
                       EvaluationEngine (Phase 5)
                      [Dimensional Scores & Status]
                                    │
                                    ▼
                        FeedbackEngine (Phase 6)
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
WHAT / WHY / EVIDENCE / IMPACT / ACTION              Prioritized Practice Guidance
- WHAT: Factual conversation observation            - High / Medium / Low priority mapping
- WHY: Why the observation influenced score         - Top priority actions for next session
- EVIDENCE: Verbatim quote or factual metric        - Evidence-backed strengths
- IMPACT: Real-world significance in mode/domain    - Actionable key improvement areas
- ACTION: Concrete step-by-step technique           - Insufficient evidence guidance
```

### 🔍 The WHAT / WHY / EVIDENCE / IMPACT / ACTION Framework

Every evaluated communication dimension is decomposed into an explainable 5-part model:

| Element | Purpose | Example |
| :--- | :--- | :--- |
| **WHAT** | What was observed in the candidate's conversation? | *"You addressed most questions, but one follow-up question remained only partially answered."* |
| **WHY** | Why did this observation affect evaluation? | *"The response discussed the broader topic but did not provide the specific implementation detail requested."* |
| **EVIDENCE** | What verifiable transcript evidence supports this? | `[Transcript excerpt — Turn 2]: "We used AWS services to handle the load."`<br>*(or `[Analysis observation]: Time complexity analysis: Detected; Space/memory overhead analysis: Detected`)* |
| **IMPACT** | Why does this matter in the selected scenario? | *"In technical interviews, missing requested implementation details makes it harder for interviewers to verify depth."* |
| **ACTION** | What concrete thing should the user do next time? | *"When asked a follow-up, answer the exact question in your opening sentence before elaborating with context."* |

---

## 🛡️ Real Evidence & Language Safety Guarantees

* **Real Evidence Only:** The engine strictly utilizes verbatim transcript excerpts from user turns or clearly labeled analysis observations (e.g., `[Transcript excerpt — Turn 1]` or `[Analysis observation]`). It **never fabricates or hallucinates dialogue**.
* **Objective Language Signals Only:** Feedback strictly avoids unsupported psychological or personality diagnoses (such as *"you are nervous"*, *"you lack confidence"*, or *"you have anxiety"*). It references observable linguistic indicators only (e.g. *"language-based confidence indicator: filler words detected (4.2% of speech)"*).
* **Deterministic & Zero-API Dependency:** Like earlier phases, Phase 6 feedback generation is 100% deterministic and runs locally in Demo Mode without requiring an LLM API key.
* **Non-Penalizing Missing Evidence:** Dimensions with `insufficient_evidence` (e.g. no objection voiced by the persona) are explicitly explained with guidance on how to trigger those conditions, without penalizing the overall score.

---

## 👔 Mode-Specific Feedback Rubrics

| Practice Mode | Evaluated Competencies | Feedback Focus & Guidance |
| :--- | :--- | :--- |
| **HR Interview** | STAR framework, metrics, question handling | Situation → Task → Action → Result structure, personal ownership, quantifiable outcomes |
| **Technical Interview** | Complexity rigor, concept breadth, edge cases | Dual Big-O time and space analysis, boundary conditions, data structure trade-offs |
| **Client Pitch** | Value proposition, ROI, security, objections | Connecting features to ROI payback, enterprise security compliance, resolving pushback |
| **Project Viva** | Architecture defense, validation, limitations | Design pattern rationale, empirical baseline benchmarks, candid limitation appraisal |
| **Group Discussion** | Argument quality, synthesis, debate dynamics | Evidence-backed assertions, multi-perspective nuance, collaborative consensus building |
| **Managerial Interview** | Empathy, coaching, mediation, prioritization | 1-on-1 coaching frameworks, data-driven conflict resolution, RICE roadmap ownership |

---

## 🎭 Supported AI Persona Archetypes

| Mode | Persona | Role | Difficulty | Core Probing Focus |
| :--- | :--- | :--- | :--- | :--- |
| **HR Interview** | **Friendly HR Recruiter** | HR Recruiter | Beginner | Career transitions, enthusiasm, culture fit |
| **HR Interview** | **Strict HR Interviewer** | Senior HR Interviewer | Advanced | STAR framework, personal ownership, metrics |
| **Technical Interview** | **Software Engineer** | Software Engineer | Intermediate | Algorithm design, time/space complexity |
| **Technical Interview** | **Senior Technical Interviewer** | Staff Systems Architect | Advanced | Distributed systems, latency, fault tolerance |
| **Client Pitch** | **Non-Technical Business Executive** | Business Executive | Beginner | Strategic business impact, jargon-free value |
| **Client Pitch** | **Budget-Conscious Manager** | Business Manager | Intermediate | ROI payback timelines, total cost, onboarding |
| **Client Pitch** | **Skeptical CTO** | Chief Technology Officer | Advanced | Enterprise security, scalability, vendor lock-in |
| **Project Viva** | **Professor** | University Professor | Intermediate | Foundational principles, tech stack rationale |
| **Project Viva** | **Technical Examiner** | Technical Examiner | Advanced | Validation rigor, statistical baselines, error analysis |
| **Group Discussion** | **Confident Participant** | Peer Discussion Contributor | Intermediate | Strategic vision, fast-paced debate progression |
| **Group Discussion** | **Analytical Participant** | Peer Data Strategist | Advanced | Empirical data points, trade-offs, ethical nuances |
| **Managerial Interview** | **Operations Director** | Director of Operations | Intermediate | Process architecture, RACI alignment, risk plans |
| **Managerial Interview** | **Hiring Manager** | Hiring Manager | Advanced | Conflict resolution, leadership under pressure |

---

---

## 🗄️ Persistence & Analytics Architecture (Phase 7)

```text
Completed Practice Session (Turns + Evaluation + Explainable Feedback)
                                │
                                ▼
                          HistoryService
                     [Application Logic & Validation]
                     - Ensures session completion
                     - Enforces duplicate prevention (idempotency)
                     - Calculates session duration
                                │
                                ▼
                        HistoryRepository
                     [SQLite Persistence Engine]
                     - Parameterized SQL queries
                     - Foreign key cascading & indexing
                     - Atomic transactions
                                │
                                ▼
                   SQLite Database (pitch_practice.db)
                   ├── sessions (Metadata, scores, JSON payloads)
                   ├── messages (Ordered transcript turns & roles)
                   └── dimension_scores (Fast indexed dimension metrics)
                                │
                                ▼
                         AnalyticsService
             [Descriptive & Longitudinal Analytics]
             ├── Summary KPIs (Averages, high/low scores, turns)
             ├── Chronological progression trends (Line chart)
             ├── Mode & difficulty breakdowns
             ├── Dimension historical averages
             ├── Recurring pattern discovery (Strengths & improvements)
             └── Side-by-side session comparison (Neutral score deltas)
```

### 📜 Session History Page
* **Filter & Sort:** Query past sessions by Practice Mode, Difficulty Tier, Minimum Score, and Date Order.
* **Session Metadata Cards:** Immediate visibility into Scenario, Persona, Date, Turn Count, Duration, and Recorded Score.
* **Full Session Detail Inspection:**
  * **Evaluation Breakdown:** Dimensional scores, rationales, and underlying evidence.
  * **Explainable Feedback:** Complete WHAT / WHY / EVIDENCE / IMPACT / ACTION report, executive summary, and priority practice actions.
  * **Conversation Transcript:** Verbatim dialogue turns between candidate and AI persona. **Internal system instructions are strictly excluded.**
* **Safe Deletion:** Permanent session deletion with cascade cleanup of messages and dimensional scores.

### 📊 Longitudinal Performance Analytics
* **Descriptive Summary KPIs:** Neutral metrics including completed sessions count, average score, highest recorded score, lowest recorded score, and average turns.
* **Chronological Score Progression:** Visualized score trends over time (requiring at least two sessions for meaningful trend line rendering).
* **Mode & Difficulty Breakdowns:** Descriptive statistics across practice modes and difficulty tiers without value judgments.
* **Historical Dimension Averages:** Longitudinal averages for evaluated competencies (e.g. Question Handling, Fluency, Topic Coverage).
* **Recurring Patterns:** Frequency analysis of recurring actionable improvement themes and evidence-backed strengths.
* **Side-by-Side Session Comparison:** Neutral comparative tool analyzing score deltas (`+X.X points`), metadata differences, dimensional score shifts, and shared feedback themes.

### 🛡️ Privacy & Local Data Security Guarantees
* **100% Local Storage:** Session transcripts, scores, and feedback reside entirely on your local machine in `data/pitch_practice.db`.
* **Zero External Telemetry:** No user conversations or evaluation data are ever transmitted to third-party databases or analytics servers.
* **Excluded from Git:** Database files (`*.db`, `*.sqlite`, `data/*.db`) are registered in `.gitignore` to prevent accidental commits of user practice sessions.
* **Parameterized Queries:** All SQLite interactions use parameterized statements to prevent SQL injection vulnerabilities.

---

## ✨ Current Features (Phase 1 to Phase 7)

* **Interactive Multi-Turn Role-Play:** Dynamic back-and-forth simulation with persona-guided follow-ups and turn controls.
* **Evidence-Based Conversation Intelligence:** On-demand analysis of completed sessions providing factual observations.
* **Transparent Evaluation & Scoring:** Multi-dimensional scoring on a 0–100 scale backed by explicit evidence quotes and rationales.
* **Explainable Feedback Engine (WHAT / WHY / EVIDENCE / IMPACT / ACTION):** Fully explainable feedback for every evaluated dimension.
* **Prioritized Practice Actions:** Top actionable guidelines categorized into High, Medium, and Low priority.
* **Evidence-Backed Strengths & Improvements:** Concrete positive accomplishments and actionable improvement areas tied to transcript evidence.
* **Persistent Session History:** Automatic, idempotent SQLite storage of completed sessions, transcripts, evaluations, and feedback.
* **Longitudinal Analytics & Charts:** Chronological performance tracking, dimensional averages, and mode/difficulty breakdowns.
* **Recurring Pattern Detection:** Observable frequencies of improvement themes and demonstrated strengths.
* **Neutral Session Comparison Tool:** Side-by-side comparison of two sessions with descriptive score differences and dimensional analysis.
* **Zero-Dependency Demo Mode:** 100% deterministic local execution without requiring an LLM API key.
* **Comprehensive Pytest Suite:** 135 unit and integration tests passing in < 2.0s.

---

## 🗺️ Planned Features (Future Phases)

* **Phase 8:** Advanced Simulation Scenarios & Custom Persona Creation.
* **Phase 9:** Real-Time Voice Practice & Speech Evaluation (VAD, pitch, pacing, hesitation detection).

---

## 🛠️ Technology Stack

* **Language:** Python 3.10+
* **Frontend / UI:** [Streamlit](https://streamlit.io/)
* **Database:** SQLite (Python standard library `sqlite3`)
* **Testing:** [pytest](https://pytest.org/)
* **Configuration:** [python-dotenv](https://github.com/theskumar/python-dotenv)


---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/pitch-practice-partner.git
cd pitch-practice-partner
```

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the Application

Launch the Streamlit web application:

```bash
streamlit run app.py
```

The application will start locally at http://localhost:8501.

---

## 🧪 Running Tests

Execute the automated test suite with pytest:

```bash
python -m pytest -q
```

To run with verbose output:

```bash
python -m pytest -v
```

---

## 📂 Project Structure

```text
Pitch-Practice-Partner/
│
├── app.py                      # Streamlit application: practice, history, analytics & settings
├── README.md                   # Project documentation updated for Phase 7
├── requirements.txt            # Minimal Python dependencies
├── .gitignore                  # Git ignore rules for virtualenvs, cache, secrets & databases (*.db)
├── .env.example                # Example environment variables template
│
├── src/                        # Core source code
│   ├── __init__.py             # Package metadata
│   │
│   ├── history/                # Session History & Analytics Engine (Phase 7)
│   │   ├── __init__.py
│   │   ├── history_models.py   # HistoricalSession, HistoricalMessage, HistoricalDimensionScore
│   │   ├── history_repository.py # SQLite database repository layer
│   │   ├── history_service.py  # Application persistence service, idempotency & validation
│   │   └── analytics.py        # Descriptive statistics, progress tracking & session comparison
│   │
│   ├── feedback/               # Explainable Feedback Engine (Phase 6)
│   │   ├── __init__.py
│   │   ├── feedback_models.py  # FeedbackItem, StrengthFeedbackItem, ImprovementFeedbackItem, PracticeAction
│   │   ├── feedback_rules.py   # Mode-specific & dimension rules (WHAT/WHY/EVIDENCE/IMPACT/ACTION)
│   │   ├── feedback_engine.py  # Central feedback synthesizer & priority classifier
│   │   └── evidence_utils.py   # Real transcript excerpt extractor & attribution formatter
│   │
│   ├── evaluation/             # Evaluation & Scoring Engine (Phase 5)
│   │   ├── __init__.py
│   │   ├── evaluation_models.py # ScoreDimension, EvaluationResult, DimensionStatus
│   │   ├── scoring_rules.py    # Deterministic scoring mathematical formulas
│   │   ├── mode_evaluators.py  # Evaluators for all 6 practice modes
│   │   └── evaluation_engine.py # Central evaluator & score normalizer
│   │
│   ├── intelligence/           # Conversation Intelligence Engine (Phase 4)
│   │   ├── __init__.py
│   │   ├── analysis_models.py  # Structured evidence dataclasses
│   │   ├── conversation_analyzer.py # Central analyzer & mode strategies
│   │   └── detectors.py        # Deterministic & heuristic linguistic detectors
│   │
│   ├── conversation/           # Conversation & Session Engine (Phase 3)
│   │   ├── __init__.py
│   │   ├── conversation_manager.py # Session lifecycle & prompt orchestration
│   │   └── conversation_models.py  # Message & PracticeSession dataclasses
│   │
│   ├── scenarios/              # Scenario & Persona models and management logic
│   │   ├── __init__.py
│   │   ├── scenario_manager.py # Loader, query filters, persona lookup & validation
│   │   └── scenario_models.py  # Typed Scenario & Persona dataclasses
│   │
│   ├── ai/                     # AI provider abstraction layer
│   │   ├── __init__.py
│   │   └── provider.py         # AIProvider interface, DemoProvider, RealAIProvider
│   │
│   └── utils/                  # Utility helpers and UI constants
│       └── __init__.py
│
├── data/                       # Structured definitions
│   ├── pitch_practice.db       # Local persistent SQLite database (git-ignored)
│   ├── scenarios/
│   │   └── scenarios.json      # Sample scenarios for all 6 practice modes
│   └── personas/
│       └── personas.json       # AI personas with behaviors, concerns & styles
│
└── tests/                      # Automated unit test suite (135 tests passing)
    ├── __init__.py
    ├── test_scenarios.py       # Deterministic pytest suite (85 unit tests for Phases 1-5)
    ├── test_feedback.py        # Comprehensive Phase 6 unit test suite (26 unit tests)
    ├── test_history.py         # SQLite persistence, transcript & detail tests (14 tests)
    └── test_analytics.py       # Longitudinal stats, trends & comparison tests (10 tests)
```

---

## 📄 License

MIT License. Designed for portfolio and educational demonstration.
