from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, UniqueConstraint
from database import Base

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(String(100), primary_key=True, index=True)
    slug = Column(String(120), unique=True, index=True)
    title_en = Column(String(255), nullable=False)
    title_hi = Column(String(255), nullable=False)
    title_mr = Column(String(255), nullable=False)
    ministry = Column(String(255), nullable=False)
    level = Column(String(50), default="Central") # Central or State
    state_name = Column(String(100), default="All India")
    category = Column(String(100), nullable=False, index=True)
    
    brief_en = Column(Text, nullable=False)
    brief_hi = Column(Text, nullable=False)
    brief_mr = Column(Text, nullable=False)
    
    description_en = Column(Text, nullable=False)
    description_hi = Column(Text, nullable=False)
    description_mr = Column(Text, nullable=False)
    
    benefits_en = Column(Text, nullable=False) # JSON or newline string
    benefits_hi = Column(Text, nullable=False)
    benefits_mr = Column(Text, nullable=False)
    
    eligibility_criteria_json = Column(Text, nullable=False) # JSON string
    eligibility_summary_en = Column(Text, nullable=False)
    eligibility_summary_hi = Column(Text, nullable=False)
    eligibility_summary_mr = Column(Text, nullable=False)
    
    documents_required_json = Column(Text, nullable=False) # JSON string
    application_steps_json = Column(Text, nullable=False) # JSON string
    
    official_portal_url = Column(String(500), nullable=False)
    application_mode = Column(String(50), default="Online")
    helpline_number = Column(String(100), nullable=True)
    tags = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class SavedScheme(Base):
    __tablename__ = "saved_schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_identifier = Column(String(120), index=True, nullable=False)
    scheme_id = Column(String(100), index=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_identifier', 'scheme_id', name='uq_user_scheme'),
    )

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    user_identifier = Column(String(120), nullable=True)
    response_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
