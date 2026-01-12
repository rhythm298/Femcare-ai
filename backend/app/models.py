"""
SQLAlchemy ORM Models for FemCare AI.
Defines all database tables for health tracking and AI insights.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, JSON, Enum as SQLEnum, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime


class FlowLevel(enum.Enum):
    """Menstrual flow intensity levels"""
    SPOTTING = "spotting"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    VERY_HEAVY = "very_heavy"


class SymptomCategory(enum.Enum):
    """Categories for symptoms"""
    PHYSICAL = "physical"
    EMOTIONAL = "emotional"
    HORMONAL = "hormonal"
    REPRODUCTIVE = "reproductive"
    DIGESTIVE = "digestive"
    OTHER = "other"


class ConditionType(enum.Enum):
    """Health conditions tracked by the system"""
    PCOS = "pcos"
    ENDOMETRIOSIS = "endometriosis"
    ANEMIA = "anemia"
    THYROID = "thyroid"
    PREGNANCY_RISK = "pregnancy_risk"


class User(Base):
    """User account and profile information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    
    # Profile data
    date_of_birth = Column(Date, nullable=True)
    weight = Column(Float, nullable=True)  # kg
    height = Column(Float, nullable=True)  # cm
    
    # Health context
    has_given_birth = Column(Boolean, default=False)
    is_pregnant = Column(Boolean, default=False)
    is_trying_to_conceive = Column(Boolean, default=False)
    is_on_birth_control = Column(Boolean, default=False)
    medical_conditions = Column(JSON, default=list)  # List of known conditions
    
    # Settings
    notification_enabled = Column(Boolean, default=True)
    partner_sharing_enabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    cycles = relationship("CycleEntry", back_populates="user", cascade="all, delete-orphan")
    symptoms = relationship("Symptom", back_populates="user", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("HealthInsight", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    streaks = relationship("HealthStreak", back_populates="user", cascade="all, delete-orphan")


class CycleEntry(Base):
    """Menstrual cycle tracking entries"""
    __tablename__ = "cycle_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Cycle data
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    cycle_length = Column(Integer, nullable=True)  # Days from this start to next start
    period_length = Column(Integer, nullable=True)  # Days of bleeding
    
    # Flow tracking
    flow_level = Column(String(20), default="medium")
    
    # Additional data
    ovulation_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Predictions
    predicted_next_start = Column(Date, nullable=True)
    prediction_confidence = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cycles")
    symptoms = relationship("Symptom", back_populates="cycle", cascade="all, delete-orphan")


class Symptom(Base):
    """Daily symptom logging"""
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cycle_id = Column(Integer, ForeignKey("cycle_entries.id"), nullable=True)
    
    # Symptom details
    date = Column(Date, nullable=False)
    symptom_type = Column(String(100), nullable=False)  # e.g., "cramps", "headache", "fatigue"
    category = Column(String(50), default="physical")
    severity = Column(Integer, nullable=False)  # 1-10 scale
    
    # Additional info
    description = Column(Text, nullable=True)
    duration_hours = Column(Float, nullable=True)
    
    # AI analysis
    ai_classification = Column(JSON, nullable=True)  # Structured classification result
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="symptoms")
    cycle = relationship("CycleEntry", back_populates="symptoms")


class RiskScore(Base):
    """AI-calculated health risk scores"""
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Risk data
    condition_type = Column(String(50), nullable=False)  # pcos, endometriosis, anemia, thyroid
    score = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Contributing factors
    contributing_factors = Column(JSON, default=list)  # List of factors that contributed
    
    # Trend
    previous_score = Column(Float, nullable=True)
    trend = Column(String(20), nullable=True)  # improving, stable, worsening
    
    # Timestamps
    calculated_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="risk_scores")


class HealthInsight(Base):
    """AI-generated health insights and observations"""
    __tablename__ = "health_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Insight details
    insight_type = Column(String(50), nullable=False)  # pattern, alert, tip, correlation
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Priority and status
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    
    # Related data
    related_conditions = Column(JSON, default=list)
    evidence = Column(JSON, default=list)  # Data points supporting this insight
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="insights")


class Recommendation(Base):
    """Personalized health recommendations"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Recommendation details
    category = Column(String(50), nullable=False)  # lifestyle, diet, exercise, medical, tracking
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Priority and completion
    priority = Column(Integer, default=5)  # 1-10, higher is more important
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Action plan
    action_steps = Column(JSON, default=list)  # List of specific steps
    expected_duration = Column(String(50), nullable=True)  # e.g., "1 week", "ongoing"
    
    # Evidence
    reason = Column(Text, nullable=True)  # Why this recommendation
    evidence_based = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")


class ChatMessage(Base):
    """Chat history with AI health assistant"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # AI processing metadata
    intent = Column(String(50), nullable=True)  # Detected user intent
    entities = Column(JSON, nullable=True)  # Extracted entities
    actions_taken = Column(JSON, nullable=True)  # Agent actions
    confidence = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_history")


class HealthStreak(Base):
    """Gamification - Health tracking streaks"""
    __tablename__ = "health_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Streak details
    streak_type = Column(String(50), nullable=False)  # logging, exercise, sleep, hydration
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    
    # Tracking
    last_activity_date = Column(Date, nullable=True)
    total_activities = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="streaks")


class Achievement(Base):
    """User achievements for gamification"""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Achievement details
    achievement_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon identifier
    
    # Timestamps
    earned_at = Column(DateTime, default=func.now())


class EducationArticle(Base):
    """Educational health articles"""
    __tablename__ = "education_articles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Article content
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    
    # Categorization
    category = Column(String(100), nullable=False)  # menstrual, reproductive, nutrition, mental_health
    tags = Column(JSON, default=list)
    
    # Metadata
    is_myth_busting = Column(Boolean, default=False)
    difficulty_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    reading_time_minutes = Column(Integer, default=5)
    
    # Sources
    sources = Column(JSON, default=list)  # List of source URLs/references
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
