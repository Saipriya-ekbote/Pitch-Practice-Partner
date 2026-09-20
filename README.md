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
* **No Actionable Feedback:** General advice rarely pinpoints filler words, clarity gaps, structural issues, or missed objectives.

---

## 💡 Solution

**Pitch Practice Partner** bridges this gap by offering:
1. **Interactive Persona Simulations:** Practice with specialized AI interviewers, moderators, client executives, and evaluators.
2. **Context-Aware Dynamic Follow-ups:** Experience dynamic back-and-forth dialogue tailored to your actual responses, the chosen scenario, and difficulty.
3. **Structured Scenario & Persona Library:** Scenarios across HR interviews, technical coding/system design, investor pitches, academic vivas, team discussions, and managerial leadership.
4. **Conversation Intelligence (Phase 4):** Pure evidence-based extraction of linguistic features, question responses, topical coverage, and persona concerns.
5. **Explainable Evaluation & Scoring Engine (Phase 5):** Deterministic, evidence-backed multi-dimensional scoring (0–100 scale) with explainable rationales and normalized overall scores.

---

## 🚀 Current Phase

**Phase 5 — Evaluation & Scoring Engine**

> [!NOTE]
> The application evaluates completed role-play sessions using deterministic scoring rules and domain-specific rubrics mapped directly to extracted conversation evidence. Every score is fully explainable with explicit factual evidence and rationales.

---

## 📊 Evaluation & Scoring Architecture (Phase 5)

`	ext
                     Completed Practice Session Transcript
                                      │
                                      ▼
                        ConversationAnalyzer (Phase 4)
                          [Structured Evidence Object]
                                      │
                                      ▼
                         EvaluationEngine (Phase 5)
                                      │
      ┌───────────────────────────────┴───────────────────────────────┐
      ▼                                                               ▼
Standard Shared Dimensions                               Mode-Specific Evaluators
- Question Handling (addressed/partial/unaddressed)     - HR: STAR completeness & concrete metrics
- Topic Coverage (expected scenario topics)             - Tech: Complexity rigor & edge case reasoning
- Communication & Fluency (fillers/repetition/length)   - Pitch: Value prop, ROI, security & objections
- Relevance & Substance (substantive turns)             - Viva: Architecture defense & limitations
- Objection Handling (pushback evidence)               - GD: Argument nuance & collaborative synthesis
                                                        - Managerial: 1-on-1 coaching & prioritization
                                      │
                                      ▼
                     Normalized Overall Score (0–100)
            + Evidence-Backed Strengths & Improvement Areas
            + Insufficient Evidence & Applicability Badges
`

### 🎯 Standardized Scoring Methodology (0–100 Scale)

| Score Dimension | Evaluation Focus | Deterministic Scoring Logic |
| :--- | :--- | :--- |
| **Question Handling** | Responsiveness to AI inquiries | (Addressed * 1.0 + Partially * 0.5) / Total Questions * 100 |
| **Topic Coverage** | Alignment with scenario goals | (Covered Topics / Total Expected Topics) * 100 |
| **Communication & Fluency** | Language delivery & pacing | 100 - Filler Penalty - Repetition Penalty - Brevity Penalty |
| **Relevance & Substance** | Content depth & consistency | 70 + (Substantive Turn Ratio * 30) - Contradiction Penalties |
| **Objection Handling** | Addressing persona pushback | (Addressed Objections / Total Raised Objections) * 100 |
| **Domain Dimensions** | Mode-specific competencies | STAR framework (HR), Complexity (Tech), ROI/Security (Pitch), etc. |

> [!TIP]
> **Evidence-Grounded Normalization**: If a session lacks questions, objections, or speech data, dimensions are labeled as insufficient_evidence or 
ot_applicable. The overall score dynamically normalizes only across evaluated dimensions, ensuring the user is never penalized with arbitrary zeros for conditions not encountered in the conversation.

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

## ✨ Current Features (Phase 1 to Phase 5)

* **Interactive Multi-Turn Role-Play:** Dynamic back-and-forth simulation with persona-guided follow-ups and turn controls.
* **Evidence-Based Conversation Intelligence:** On-demand analysis of completed sessions providing factual observations.
* **Explainable Evaluation & Scoring:** Multi-dimensional scoring on a 0–100 scale backed by explicit evidence quotes and rationales.
* **Domain-Specific Mode Evaluators:** Customized rubrics across all 6 practice modes (HR, Tech, Pitch, Viva, GD, Managerial).
* **Evidence-Backed Feedback:** Automatically generated strengths and concrete improvement areas tied directly to conversation data.
* **Normalized Overall Scoring:** Weighted scoring that gracefully handles unobserved dimensions (insufficient_evidence / 
ot_applicable).
* **Zero-Dependency Demo Mode:** 100% deterministic local execution without requiring an LLM API key.
* **Robust Pytest Suite:** 85 deterministic unit tests passing in < 0.3s.

---

## 🗺️ Planned Features (Future Phases)

* **Phase 6:** Session History & Persistence (Database storage, session review, progress tracking).
* **Phase 7:** Analytics Dashboard & Longitudinal Performance Trends.
* **Phase 8:** Real-Time Voice Practice & Speech Evaluation (VAD, pitch, pacing, hesitation detection).

---

## 🛠️ Technology Stack

* **Language:** Python 3.10+
* **Frontend / UI:** [Streamlit](https://streamlit.io/)
* **Testing:** [pytest](https://pytest.org/)
* **Configuration:** [python-dotenv](https://github.com/theskumar/python-dotenv)

---

## 📦 Installation

### 1. Clone the Repository
`ash
git clone https://github.com/your-username/pitch-practice-partner.git
cd pitch-practice-partner
`

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
`powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
`

**On macOS / Linux:**
`ash
python3 -m venv .venv
source .venv/bin/activate
`

### 3. Install Dependencies
`ash
pip install -r requirements.txt
`

---

## 🏃 Running the Application

Launch the Streamlit web application:

`ash
streamlit run app.py
`

The application will start locally at http://localhost:8501.

---

## 🧪 Running Tests

Execute the automated test suite with pytest:

`ash
python -m pytest -q
`

To run with verbose output:

`ash
python -m pytest -v
`

---

## 📂 Project Structure

`	ext
Pitch-Practice-Partner/
│
├── app.py                      # Streamlit application layout, chat UI, analysis & evaluation view
├── README.md                   # Project documentation updated for Phase 5
├── requirements.txt            # Minimal Python dependencies
├── .gitignore                  # Git ignore rules for virtualenvs, cache & secrets
├── .env.example                # Example environment variables template
│
├── src/                        # Core source code
│   ├── __init__.py             # Package metadata
│   │
│   ├── evaluation/             # Evaluation & Scoring Engine (Phase 5)
│   │   ├── __init__.py
│   │   ├── evaluation_models.py # ScoreDimension, EvaluationResult, DimensionStatus
│   │   ├── scoring_rules.py    # Deterministic scoring mathematical formulas
│   │   ├── mode_evaluators.py  # Evaluators for all 6 practice modes
│   │   └── evaluation_engine.py # Central evaluator & explainability generator
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
│   ├── scenarios/
│   │   └── scenarios.json      # Sample scenarios for all 6 practice modes
│   └── personas/
│       └── personas.json       # AI personas with behaviors, concerns & styles
│
└── tests/                      # Automated unit test suite
    ├── __init__.py
    └── test_scenarios.py       # Deterministic pytest suite (85 unit tests)
`

---

## 📄 License

MIT License. Designed for portfolio and educational demonstration.
