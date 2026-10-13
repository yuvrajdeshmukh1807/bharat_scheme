# backend/main.py
import json
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
from schemas import (
    EligibilityProfile, EligibilityCheckResponse, SchemeMatchResult,
    SchemeResponse, ChatQuery, ChatResponse,
    SavedSchemeCreate, SavedSchemeResponse
)
from schemes_data import SCHEMES_DATA, CATEGORIES_METADATA
from eligibility_engine import evaluate_scheme_eligibility
from rag_service import rag_service

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed verified schemes into the database on startup if not already seeded."""
    db = next(get_db())
    try:
        count = db.query(models.Scheme).count()
        if count == 0:
            for s in SCHEMES_DATA:
                db_scheme = models.Scheme(
                    id=s["id"],
                    slug=s["slug"],
                    title_en=s["title_en"],
                    title_hi=s["title_hi"],
                    title_mr=s["title_mr"],
                    ministry=s["ministry"],
                    level=s["level"],
                    state_name=s["state_name"],
                    category=s["category"],
                    brief_en=s["brief_en"],
                    brief_hi=s["brief_hi"],
                    brief_mr=s["brief_mr"],
                    description_en=s["description_en"],
                    description_hi=s["description_hi"],
                    description_mr=s["description_mr"],
                    benefits_en=json.dumps(s["benefits_en"]),
                    benefits_hi=json.dumps(s["benefits_hi"]),
                    benefits_mr=json.dumps(s["benefits_mr"]),
                    eligibility_criteria_json=json.dumps(s["eligibility_criteria"]),
                    eligibility_summary_en=s["eligibility_summary_en"],
                    eligibility_summary_hi=s["eligibility_summary_hi"],
                    eligibility_summary_mr=s["eligibility_summary_mr"],
                    documents_required_json=json.dumps(s["documents_required_en"]),
                    application_steps_json=json.dumps(s["application_steps_en"]),
                    official_portal_url=s["official_portal_url"],
                    application_mode=s["application_mode"],
                    helpline_number=s.get("helpline_number"),
                    tags=",".join(s["tags"])
                )
                db.add(db_scheme)
            db.commit()
    finally:
        db.close()
    yield  # application runs here

app = FastAPI(
    title="BharatScheme AI Backend API",
    description="Multilingual AI-powered Indian Government Scheme Discovery & Eligibility Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local dev and preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "BharatScheme AI",
        "version": "1.0.0",
        "schemes_indexed": len(SCHEMES_DATA)
    }

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    """Retrieve all scheme categories with metadata and scheme counts."""
    # Count per category
    counts = {}
    for s in SCHEMES_DATA:
        cat = s["category"]
        counts[cat] = counts.get(cat, 0) + 1
        
    result = []
    for cat in CATEGORIES_METADATA:
        item = dict(cat)
        item["scheme_count"] = counts.get(cat["id"], 0)
        result.append(item)
    return result

@app.get("/api/schemes")
def list_schemes(
    category: Optional[str] = None,
    level: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    language: str = "en",
    db: Session = Depends(get_db)
):
    """List schemes with filtering and search support."""
    filtered = SCHEMES_DATA

    if category and category != "All":
        filtered = [s for s in filtered if s["category"].lower() == category.lower()]

    if level and level != "All":
        filtered = [s for s in filtered if s["level"].lower() == level.lower()]

    if state and state != "All":
        filtered = [s for s in filtered if s["state_name"].lower() in [state.lower(), "all india"]]

    if search:
        q = search.lower().strip()
        filtered = [
            s for s in filtered
            if q in s["title_en"].lower()
            or q in s.get("title_hi", "").lower()
            or q in s.get("title_mr", "").lower()
            or q in s["brief_en"].lower()
            or any(q in t.lower() for t in s.get("tags", []))
        ]

    # Map localized fields
    output = []
    for s in filtered:
        title = s.get(f"title_{language}") or s["title_en"]
        brief = s.get(f"brief_{language}") or s["brief_en"]
        output.append({
            "id": s["id"],
            "slug": s["slug"],
            "title": title,
            "title_en": s["title_en"],
            "title_hi": s.get("title_hi"),
            "title_mr": s.get("title_mr"),
            "category": s["category"],
            "level": s["level"],
            "state_name": s["state_name"],
            "ministry": s["ministry"],
            "brief": brief,
            "benefits": s.get(f"benefits_{language}") or s["benefits_en"],
            "official_portal_url": s["official_portal_url"],
            "application_mode": s["application_mode"],
            "helpline_number": s.get("helpline_number"),
            "tags": s.get("tags", [])
        })

    return output

@app.get("/api/schemes/{id_or_slug}")
def get_scheme(id_or_slug: str, language: str = "en", db: Session = Depends(get_db)):
    """Retrieve full details of a single scheme by ID or slug."""
    scheme = None
    for s in SCHEMES_DATA:
        if s["id"] == id_or_slug or s["slug"] == id_or_slug:
            scheme = s
            break
            
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    docs = scheme.get(f"documents_required_{language}") or scheme["documents_required_en"]
    steps = scheme.get(f"application_steps_{language}") or scheme["application_steps_en"]

    return {
        "id": scheme["id"],
        "slug": scheme["slug"],
        "title": scheme.get(f"title_{language}") or scheme["title_en"],
        "title_en": scheme["title_en"],
        "title_hi": scheme["title_hi"],
        "title_mr": scheme["title_mr"],
        "ministry": scheme["ministry"],
        "level": scheme["level"],
        "state_name": scheme["state_name"],
        "category": scheme["category"],
        "brief": scheme.get(f"brief_{language}") or scheme["brief_en"],
        "description": scheme.get(f"description_{language}") or scheme["description_en"],
        "benefits": scheme.get(f"benefits_{language}") or scheme["benefits_en"],
        "eligibility_summary": scheme.get(f"eligibility_summary_{language}") or scheme["eligibility_summary_en"],
        "eligibility_criteria": scheme["eligibility_criteria"],
        "documents_required": docs,
        "application_steps": steps,
        "official_portal_url": scheme["official_portal_url"],
        "application_mode": scheme["application_mode"],
        "helpline_number": scheme.get("helpline_number"),
        "tags": scheme["tags"]
    }

@app.get("/api/featured")
def get_featured_schemes(language: str = "en"):
    """Get curated featured schemes across top sectors for homepage showcase."""
    featured_ids = ["pm-kisan", "ayushman-bharat-pmjay", "pm-mudra-yojana", "sukanya-samriddhi-yojana", "majhi-ladki-bahin-maharashtra", "central-sector-scholarship-pm-usp"]
    featured = [s for s in SCHEMES_DATA if s["id"] in featured_ids]
    
    result = []
    for s in featured:
        result.append({
            "id": s["id"],
            "slug": s["slug"],
            "title": s.get(f"title_{language}") or s["title_en"],
            "category": s["category"],
            "level": s["level"],
            "state_name": s["state_name"],
            "ministry": s["ministry"],
            "brief": s.get(f"brief_{language}") or s["brief_en"],
            "benefits": s.get(f"benefits_{language}") or s["benefits_en"],
            "official_portal_url": s["official_portal_url"],
            "application_mode": s["application_mode"]
        })
    return result

@app.post("/api/eligibility/check", response_model=EligibilityCheckResponse)
def check_eligibility(profile: EligibilityProfile):
    """Evaluate user profile against all schemes using rule engine with explainability."""
    results: List[SchemeMatchResult] = []
    
    for s in SCHEMES_DATA:
        evaluation = evaluate_scheme_eligibility(s, profile)
        results.append(evaluation)

    # Sort results: ELIGIBLE first (by score desc), then POTENTIALLY_ELIGIBLE (by score desc), then NOT_ELIGIBLE
    status_order = {"ELIGIBLE": 0, "POTENTIALLY_ELIGIBLE": 1, "NOT_ELIGIBLE": 2}
    results.sort(key=lambda r: (status_order.get(r.match_status, 3), -r.match_score))

    eligible_count = sum(1 for r in results if r.match_status == "ELIGIBLE")
    pot_count = sum(1 for r in results if r.match_status == "POTENTIALLY_ELIGIBLE")
    not_count = sum(1 for r in results if r.match_status == "NOT_ELIGIBLE")

    return EligibilityCheckResponse(
        total_schemes_analyzed=len(SCHEMES_DATA),
        eligible_count=eligible_count,
        potentially_eligible_count=pot_count,
        not_eligible_count=not_count,
        user_summary={
            "state": profile.state,
            "age": profile.age,
            "gender": profile.gender,
            "occupation": profile.occupation,
            "caste_category": profile.caste_category,
            "annual_income": profile.annual_income,
            "student_status": profile.student_status,
            "is_farmer": profile.is_farmer,
            "is_entrepreneur": profile.is_entrepreneur
        },
        results=results
    )

@app.post("/api/assistant/chat", response_model=ChatResponse)
async def chat_with_assistant(chat_query: ChatQuery, db: Session = Depends(get_db)):
    """RAG-powered conversational assistant for Indian Government schemes."""
    # Log query
    try:
        log_entry = models.QueryLog(
            query_text=chat_query.query,
            language=chat_query.language
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        pass

    response = await rag_service.answer_query(
        query=chat_query.query,
        language=chat_query.language,
        api_key=chat_query.api_key,
        llm_provider=chat_query.llm_provider,
        user_context=chat_query.user_context
    )
    return response

@app.get("/api/saved-schemes")
def get_saved_schemes(user_id: str = Query(..., description="Unique device/user identifier"), language: str = "en", db: Session = Depends(get_db)):
    """Retrieve saved schemes for user."""
    records = db.query(models.SavedScheme).filter(models.SavedScheme.user_identifier == user_id).all()
    
    results = []
    schemes_dict = {s["id"]: s for s in SCHEMES_DATA}
    
    for r in records:
        scheme_data = schemes_dict.get(r.scheme_id)
        if scheme_data:
            s_summary = {
                "id": scheme_data["id"],
                "slug": scheme_data["slug"],
                "title": scheme_data.get(f"title_{language}") or scheme_data["title_en"],
                "category": scheme_data["category"],
                "brief": scheme_data.get(f"brief_{language}") or scheme_data["brief_en"],
                "official_portal_url": scheme_data["official_portal_url"],
                "application_mode": scheme_data["application_mode"]
            }
        else:
            s_summary = None

        results.append({
            "id": r.id,
            "user_identifier": r.user_identifier,
            "scheme_id": r.scheme_id,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "scheme": s_summary
        })
    return results

@app.post("/api/saved-schemes")
def save_scheme(payload: SavedSchemeCreate, db: Session = Depends(get_db)):
    """Save or bookmark a scheme."""
    # Check if already saved
    existing = db.query(models.SavedScheme).filter(
        models.SavedScheme.user_identifier == payload.user_identifier,
        models.SavedScheme.scheme_id == payload.scheme_id
    ).first()
    
    if existing:
        return {"message": "Scheme already saved", "id": existing.id}
        
    record = models.SavedScheme(
        user_identifier=payload.user_identifier,
        scheme_id=payload.scheme_id,
        notes=payload.notes
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"message": "Scheme saved successfully", "id": record.id}

@app.delete("/api/saved-schemes/{scheme_id}")
def delete_saved_scheme(scheme_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Remove a saved scheme."""
    record = db.query(models.SavedScheme).filter(
        models.SavedScheme.user_identifier == user_id,
        models.SavedScheme.scheme_id == scheme_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Saved scheme not found")
        
    db.delete(record)
    db.commit()
    return {"message": "Saved scheme removed successfully"}
