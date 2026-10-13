from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EligibilityProfile(BaseModel):
    state: str = Field(..., json_schema_extra={"example": "Maharashtra"})
    district: Optional[str] = Field(None, json_schema_extra={"example": "Pune"})
    age: int = Field(..., ge=0, le=120, json_schema_extra={"example": 24})
    gender: str = Field("all", json_schema_extra={"example": "female"})  # female, male, other, all
    caste_category: str = Field("General", json_schema_extra={"example": "OBC"})  # General, OBC, SC, ST, EWS
    occupation: str = Field("student", json_schema_extra={"example": "farmer"})  # farmer, student, artisan, street_vendor, unemployed, salaried, self_employed, homemaker, other
    student_status: bool = Field(False, json_schema_extra={"example": True})
    education_level: Optional[str] = Field(None, json_schema_extra={"example": "undergraduate"})  # 10th, 12th, undergraduate, postgraduate, vocational, none
    annual_income: float = Field(..., ge=0, json_schema_extra={"example": 180000})  # In INR per year
    is_farmer: bool = Field(False, json_schema_extra={"example": False})
    has_landholding: bool = Field(False, json_schema_extra={"example": False})
    is_entrepreneur: bool = Field(False, json_schema_extra={"example": False})
    is_differently_abled: bool = Field(False, json_schema_extra={"example": False})
    is_bpl_ration_card_holder: bool = Field(False, json_schema_extra={"example": False})
    is_minority: bool = Field(False, json_schema_extra={"example": False})
    language: str = Field("en", json_schema_extra={"example": "en"})  # en, hi, mr

class CriteriaEvaluation(BaseModel):
    criteria_name: str
    status: str  # "matched", "unmet", "neutral", "needs_verification"
    message: str

class SchemeMatchResult(BaseModel):
    scheme_id: str
    slug: str
    title: str
    category: str
    level: str
    state_name: str
    ministry: str
    brief: str
    benefits: List[str]
    match_status: str  # "ELIGIBLE", "POTENTIALLY_ELIGIBLE", "NOT_ELIGIBLE"
    match_score: int  # 0 to 100
    matched_reasons: List[str]
    unmet_reasons: List[str]
    info_needed: List[str]
    criteria_evaluations: List[CriteriaEvaluation]
    official_portal_url: str
    application_mode: str
    helpline_number: Optional[str] = None

class EligibilityCheckResponse(BaseModel):
    total_schemes_analyzed: int
    eligible_count: int
    potentially_eligible_count: int
    not_eligible_count: int
    user_summary: Dict[str, Any]
    results: List[SchemeMatchResult]

class SchemeResponse(BaseModel):
    id: str
    slug: str
    title_en: str
    title_hi: str
    title_mr: str
    ministry: str
    level: str
    state_name: str
    category: str
    brief_en: str
    brief_hi: str
    brief_mr: str
    description_en: str
    description_hi: str
    description_mr: str
    benefits_en: List[str]
    benefits_hi: List[str]
    benefits_mr: List[str]
    eligibility_summary_en: str
    eligibility_summary_hi: str
    eligibility_summary_mr: str
    documents_required: List[str]
    application_steps: List[str]
    official_portal_url: str
    application_mode: str
    helpline_number: Optional[str]
    tags: List[str]

class ChatQuery(BaseModel):
    query: str = Field(..., min_length=2, json_schema_extra={"example": "What are the scholarship schemes for undergraduate girl students?"})
    language: str = Field("en", json_schema_extra={"example": "en"})  # en, hi, mr
    api_key: Optional[str] = None
    llm_provider: Optional[str] = "gemini"  # gemini or openai or offline
    user_context: Optional[Dict[str, Any]] = None

class Citation(BaseModel):
    scheme_id: str
    title: str
    official_portal_url: str
    relevance_score: float

class ChatResponse(BaseModel):
    query: str
    language: str
    answer: str
    citations: List[Citation]
    suggested_followups: List[str]
    referenced_schemes: List[Dict[str, Any]]

class SavedSchemeCreate(BaseModel):
    user_identifier: str
    scheme_id: str
    notes: Optional[str] = None

class SavedSchemeResponse(BaseModel):
    id: int
    user_identifier: str
    scheme_id: str
    notes: Optional[str]
    scheme: Optional[Dict[str, Any]] = None
