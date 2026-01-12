"""
Pydantic schemas for request/response validation in FemCare AI.
Provides type safety and automatic API documentation.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


# ============== Enums ==============

class FlowLevel(str, Enum):
    SPOTTING = "spotting"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    VERY_HEAVY = "very_heavy"


class SymptomCategory(str, Enum):
    PHYSICAL = "physical"
    EMOTIONAL = "emotional"
    HORMONAL = "hormonal"
    REPRODUCTIVE = "reproductive"
    DIGESTIVE = "digestive"
    OTHER = "other"


class ConditionType(str, Enum):
    PCOS = "pcos"
    ENDOMETRIOSIS = "endometriosis"
    ANEMIA = "anemia"
    THYROID = "thyroid"
    PREGNANCY_RISK = "pregnancy_risk"


class InsightType(str, Enum):
    PATTERN = "pattern"
    ALERT = "alert"
    TIP = "tip"
    CORRELATION = "correlation"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============== User Schemas ==============

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    weight: Optional[float] = Field(None, gt=0, lt=500)
    height: Optional[float] = Field(None, gt=0, lt=300)
    has_given_birth: Optional[bool] = None
    is_pregnant: Optional[bool] = None
    is_trying_to_conceive: Optional[bool] = None
    is_on_birth_control: Optional[bool] = None
    medical_conditions: Optional[List[str]] = None
    notification_enabled: Optional[bool] = None
    partner_sharing_enabled: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    date_of_birth: Optional[date] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    has_given_birth: bool = False
    is_pregnant: bool = False
    is_trying_to_conceive: bool = False
    is_on_birth_control: bool = False
    medical_conditions: List[str] = []
    notification_enabled: bool = True
    partner_sharing_enabled: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ============== Cycle Schemas ==============

class CycleBase(BaseModel):
    start_date: date
    end_date: Optional[date] = None
    flow_level: FlowLevel = FlowLevel.MEDIUM
    notes: Optional[str] = None


class CycleCreate(CycleBase):
    pass


class CycleUpdate(BaseModel):
    end_date: Optional[date] = None
    flow_level: Optional[FlowLevel] = None
    ovulation_date: Optional[date] = None
    notes: Optional[str] = None


class CycleResponse(CycleBase):
    id: int
    user_id: int
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None
    ovulation_date: Optional[date] = None
    predicted_next_start: Optional[date] = None
    prediction_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CyclePrediction(BaseModel):
    next_period_start: date
    next_period_end: date
    next_ovulation: Optional[date] = None
    fertile_window_start: Optional[date] = None
    fertile_window_end: Optional[date] = None
    confidence: float
    average_cycle_length: float
    average_period_length: float


class CyclePatterns(BaseModel):
    average_cycle_length: float
    cycle_length_std: float
    average_period_length: float
    is_regular: bool
    regularity_score: float  # 0-1
    total_cycles_tracked: int
    longest_cycle: int
    shortest_cycle: int
    common_symptoms: List[Dict[str, Any]]
    cycle_phase_patterns: Dict[str, Any]


# ============== Symptom Schemas ==============

class SymptomBase(BaseModel):
    date: date
    symptom_type: str = Field(..., min_length=1, max_length=100)
    category: SymptomCategory = SymptomCategory.PHYSICAL
    severity: int = Field(..., ge=1, le=10)
    description: Optional[str] = None
    duration_hours: Optional[float] = Field(None, ge=0)


class SymptomCreate(SymptomBase):
    cycle_id: Optional[int] = None


class SymptomResponse(SymptomBase):
    id: int
    user_id: int
    cycle_id: Optional[int] = None
    ai_classification: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SymptomAnalysis(BaseModel):
    total_symptoms: int
    symptoms_by_category: Dict[str, int]
    average_severity: float
    most_common: List[Dict[str, Any]]
    severity_trend: str  # improving, stable, worsening
    correlations: List[Dict[str, Any]]
    recommendations: List[str]


# ============== Risk Score Schemas ==============

class RiskScoreBase(BaseModel):
    condition_type: ConditionType
    score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)


class RiskScoreResponse(RiskScoreBase):
    id: int
    user_id: int
    contributing_factors: List[Dict[str, Any]] = []
    previous_score: Optional[float] = None
    trend: Optional[str] = None
    calculated_at: datetime

    class Config:
        from_attributes = True


class RiskAssessment(BaseModel):
    pcos: RiskScoreResponse
    endometriosis: RiskScoreResponse
    anemia: RiskScoreResponse
    thyroid: RiskScoreResponse
    overall_health_score: float
    priority_concerns: List[str]
    calculated_at: datetime


# ============== Health Insight Schemas ==============

class InsightBase(BaseModel):
    insight_type: InsightType
    title: str
    content: str
    priority: Priority = Priority.NORMAL


class InsightCreate(InsightBase):
    related_conditions: List[str] = []
    evidence: List[Dict[str, Any]] = []


class InsightResponse(InsightBase):
    id: int
    user_id: int
    is_read: bool = False
    is_dismissed: bool = False
    related_conditions: List[str] = []
    evidence: List[Dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Recommendation Schemas ==============

class RecommendationBase(BaseModel):
    category: str
    title: str
    description: str
    priority: int = Field(5, ge=1, le=10)


class RecommendationCreate(RecommendationBase):
    action_steps: List[str] = []
    expected_duration: Optional[str] = None
    reason: Optional[str] = None


class RecommendationResponse(RecommendationBase):
    id: int
    user_id: int
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    action_steps: List[str] = []
    expected_duration: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActionPlan(BaseModel):
    week: int
    focus_area: str
    tasks: List[RecommendationResponse]
    goals: List[str]


# ============== Chat Schemas ==============

class ChatMessageBase(BaseModel):
    content: str = Field(..., min_length=1)


class ChatRequest(ChatMessageBase):
    pass


class ChatResponse(BaseModel):
    id: int
    role: str
    content: str
    intent: Optional[str] = None
    actions_taken: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversation(BaseModel):
    messages: List[ChatResponse]
    context: Optional[Dict[str, Any]] = None


# ============== Timeline Schemas ==============

class TimelineEvent(BaseModel):
    id: int
    event_type: str  # cycle_start, cycle_end, symptom, insight, recommendation
    date: date
    title: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class HealthTimeline(BaseModel):
    events: List[TimelineEvent]
    start_date: date
    end_date: date
    patterns_detected: List[Dict[str, Any]]
    correlations: List[Dict[str, Any]]


# ============== Streak & Gamification Schemas ==============

class StreakResponse(BaseModel):
    id: int
    streak_type: str
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date] = None
    total_activities: int

    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    id: int
    achievement_type: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    earned_at: datetime

    class Config:
        from_attributes = True


class GamificationStatus(BaseModel):
    streaks: List[StreakResponse]
    achievements: List[AchievementResponse]
    total_points: int
    level: int
    next_level_points: int


# ============== Education Schemas ==============

class ArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    content: str
    category: str
    tags: List[str] = []
    is_myth_busting: bool = False
    difficulty_level: str = "beginner"
    reading_time_minutes: int = 5
    sources: List[str] = []

    class Config:
        from_attributes = True


class ArticleList(BaseModel):
    articles: List[ArticleResponse]
    total: int
    categories: List[str]


# ============== Export Schemas ==============

class DataExport(BaseModel):
    user: UserResponse
    cycles: List[CycleResponse]
    symptoms: List[SymptomResponse]
    risk_scores: List[RiskScoreResponse]
    insights: List[InsightResponse]
    recommendations: List[RecommendationResponse]
    exported_at: datetime


# ============== Dashboard Schemas ==============

class DashboardSummary(BaseModel):
    current_cycle_day: Optional[int] = None
    days_until_next_period: Optional[int] = None
    current_phase: Optional[str] = None  # menstrual, follicular, ovulation, luteal
    recent_symptoms: List[SymptomResponse]
    risk_summary: Dict[str, float]
    unread_insights: int
    pending_recommendations: int
    current_streak: int
    health_score: float
