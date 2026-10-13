# BharatScheme AI — Architecture Documentation

**Version:** 1.0  
**Project:** AI-Powered Indian Government Scheme Finder  
**Target:** Academic B.Tech Mini-Project & Production-Ready Reference  

---

## 1. System Overview

BharatScheme AI is a full-stack, multilingual, AI-driven government scheme discovery and explainable eligibility verification platform designed specifically for Indian citizens.

```
+-----------------------------------------------------------------------+
|                           CLIENT LAYER                                |
|  React 19 + TypeScript + Vite + Tailwind CSS v4                       |
|  - Multi-step Eligibility Wizard (Form State & Validation)            |
|  - Multilingual Context (EN, HI, MR translations)                     |
|  - RAG Conversational Assistant with Inline Citations                 |
|  - Scheme Directory & Filterable Category Navigation                  |
|  - Saved Schemes / Bookmarks (Local Device UUID)                      |
+-----------------------------------▲-----------------------------------+
                                    │ HTTP / JSON (Port 5173 -> 8000)
+-----------------------------------▼-----------------------------------+
|                        API GATEWAY / FASTAPI                          |
|  FastAPI Lifespan Startup Seeding, CORS Middleware, Error Handling     |
+-----------------------------------▲-----------------------------------+
                                    │
    +-------------------------------+-------------------------------+
    │                               │                               │
+---▼-------------------+ +---------▼---------+ +-------------------▼---+
|  ELIGIBILITY ENGINE   | |     RAG SERVICE   | |   SCHEME REPOSITORY   |
|  - Multi-Factor Rules | |  - TF-IDF Index   | |  - 21 Verified        |
|  - Explainability     | |  - Dual Synthesizer| |    Govt Schemes       |
|    (Matched/Unmet)    | |    (Offline/LLM)  | |  - Trilingual Meta    |
|  - Percentage Scoring | |  - Sanitization   | |  - Official Portals   |
+-----------------------+ +-------------------+ +-----------------------+
            │                       │                       │
+-----------▼-----------------------▼-----------------------▼-----------+
|                          DATABASE LAYER                               |
|  SQLAlchemy 2.0 ORM + SQLite (Default) / PostgreSQL Compatible        |
|  - schemes (Full trilingual descriptions, criteria, portals)          |
|  - saved_schemes (UniqueConstraint on user_identifier + scheme_id)    |
|  - query_logs (Anonymized RAG telemetry & usage metrics)              |
+-----------------------------------------------------------------------+
```

---

## 2. Component Architecture

### 2.1 Frontend Architecture (`frontend/src`)
- **UI Framework:** React 19 with Vite 8.3 bundling.
- **Styling:** Tailwind CSS v4 for responsive layout and animations.
- **State Management:**
  - `LanguageContext`: Coordinates language toggle (`en`, `hi`, `mr`) across all views.
  - `SavedSchemesContext`: Coordinates saved scheme bookmarks with local storage fallback and backend synchronization.
- **Pages:**
  - `HomePage`: Hero search, quick category cards, featured schemes showcase, FAQ section.
  - `EligibilityPage`: Multi-step questionnaire (Demographics -> Occupation -> Social -> Results) with explainable reasons.
  - `CategoriesPage`: Filter schemes by category, level (Central/State), state name, and search queries.
  - `SchemeDetailPage`: In-depth scheme view including benefits, required documents, step-by-step application instructions, and direct official portal button.
  - `AssistantPage`: Conversational RAG assistant with grounded citations, suggested follow-ups, and chat history.
  - `SavedSchemesPage`: Bookmarked schemes overview with notes and removal controls.
  - `AboutPage`: Project mission, architecture summary, and disclaimer.

### 2.2 Backend Architecture (`backend/`)
- **Framework:** FastAPI with Python 3.11.
- **Data Serialization:** Pydantic v2 schemas (`schemas.py`) with strict field validations.
- **Database Engine:** SQLAlchemy 2.0 with SQLite / PostgreSQL support (`database.py`, `models.py`).
- **Core Subsystems:**
  - `main.py`: REST API route controllers and lifespan application lifecycle.
  - `eligibility_engine.py`: Deterministic rule evaluator with granular match status (`ELIGIBLE`, `POTENTIALLY_ELIGIBLE`, `NOT_ELIGIBLE`) and explainable bullet points.
  - `rag_service.py`: Retrieval-Augmented Generation service combining TF-IDF retrieval with dual synthesizers (built-in offline template generator + external Gemini/OpenAI integration).
  - `schemes_data.py`: Central curated repository of 21 authentic central and state government schemes.

---

## 3. Data Flow & Critical Journeys

### 3.1 Eligibility Check Journey
1. Citizen fills in demographic, economic, and occupational profile on `EligibilityPage`.
2. Frontend submits `POST /api/eligibility/check` with payload structured as `EligibilityProfile`.
3. Backend evaluates profile across all 21 schemes using `evaluate_scheme_eligibility`:
   - Checks age boundaries, gender restrictions, state domicile requirements.
   - Checks occupation, landholding, annual income limits, caste categories, disability, and ration card status.
4. Generates an explainability report:
   - `matched_reasons`: Explicit conditions satisfied (e.g., "Farmer with landholding under 2 hectares").
   - `unmet_reasons`: Disqualifying conditions (e.g., "Annual income ₹3,00,000 exceeds ₹2,50,000 threshold").
   - `missing_info`: Additional documentation or details needed.
5. Scores results from 0 to 100 and classifies as `ELIGIBLE`, `POTENTIALLY_ELIGIBLE`, or `NOT_ELIGIBLE`.
6. Sorted response returned and presented as actionable cards with badge highlights and application links.

### 3.2 RAG Conversational Assistant Journey
1. Citizen submits query in English, Hindi, or Marathi on `AssistantPage`.
2. Frontend submits `POST /api/assistant/chat` with `ChatQuery`.
3. Backend sanitizes input (stripping excessive whitespace and bounding to 500 characters).
4. `rag_service.retrieve` performs TF-IDF vector matching against scheme corpus.
5. If API key present, calls external LLM with strict grounding instructions.
6. If offline or no API key, built-in structured synthesizer generates accurate, hallucination-free answer.
7. Citations, official portal links, helpline numbers, and suggested follow-up questions returned.

---

## 4. Security & Privacy Model

- **Zero PII Storage:** Demographic profiles processed in-memory only; no names, phone numbers, or Aadhaar numbers collected or stored.
- **Anonymized Telemetry:** Saved schemes and query logs reference random client-generated device UUIDs.
- **Input Sanitization:** RAG query input bounded and sanitized to mitigate prompt injection.
- **ACID Database Integrity:** DB-level unique constraint prevents duplicate bookmark entries.
