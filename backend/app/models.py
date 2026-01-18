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


# ============== Activity & Exercise Models ==============

class Exercise(Base):
    """Exercise database with period-phase recommendations"""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # yoga, cardio, strength, stretching, swimming, pilates
    intensity_level = Column(String(50), default="low")  # low, medium, high
    duration_minutes = Column(Integer, default=30)
    
    # Period phase suitability
    suitable_phases = Column(JSON, default=list)  # ["menstrual", "follicular", "ovulation", "luteal"]
    
    # Details
    description = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    instructions = Column(JSON, default=list)  # Step-by-step instructions
    
    # YouTube integration
    youtube_search_query = Column(String(300), nullable=True)
    youtube_video_id = Column(String(50), nullable=True)  # Curated video ID
    youtube_video_title = Column(String(300), nullable=True)
    
    # Calories
    calories_per_minute = Column(Float, default=5.0)
    
    # Image reference
    image_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


class ExerciseLog(Base):
    """User exercise logging"""
    __tablename__ = "exercise_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)
    
    # Exercise details
    exercise_name = Column(String(200), nullable=False)  # Store name for custom exercises
    date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    calories_burned = Column(Float, nullable=True)
    
    # Additional info
    intensity = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    youtube_video_watched = Column(String(100), nullable=True)  # Video ID if watched
    
    # Rating
    difficulty_rating = Column(Integer, nullable=True)  # 1-5
    enjoyment_rating = Column(Integer, nullable=True)  # 1-5
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


# ============== Nutrition & Calorie Models ==============

class FoodItem(Base):
    """Food database with nutritional info"""
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # fruits, vegetables, proteins, dairy, grains, snacks, beverages
    
    # Nutritional info per 100g
    calories_per_100g = Column(Float, nullable=False)
    protein_g = Column(Float, default=0)
    carbs_g = Column(Float, default=0)
    fat_g = Column(Float, default=0)
    fiber_g = Column(Float, default=0)
    
    # Serving info
    serving_size_g = Column(Float, default=100)
    serving_description = Column(String(100), nullable=True)  # "1 cup", "1 medium", etc.
    
    # Period phase benefits
    period_phase_benefit = Column(JSON, default=dict)  # {"menstrual": "Iron-rich, helps with fatigue"}
    
    # Custom items
    is_custom = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Only for custom items
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


class CalorieLog(Base):
    """Daily calorie logging"""
    __tablename__ = "calorie_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=True)
    
    # Log details
    food_name = Column(String(200), nullable=False)  # Store name for flexibility
    date = Column(Date, nullable=False)
    quantity_grams = Column(Float, nullable=False)
    meal_type = Column(String(50), nullable=False)  # breakfast, lunch, dinner, snack
    
    # Calculated nutrition
    total_calories = Column(Float, nullable=False)
    total_protein = Column(Float, default=0)
    total_carbs = Column(Float, default=0)
    total_fat = Column(Float, default=0)
    
    # Additional info
    notes = Column(Text, nullable=True)
    photo_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


class FoodAnalysis(Base):
    """AI food photo analysis results"""
    __tablename__ = "food_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Photo info
    photo_path = Column(String(500), nullable=False)
    
    # Analysis results
    analysis_result = Column(JSON, default=dict)
    detected_foods = Column(JSON, default=list)  # List of detected food items
    estimated_calories = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Status
    is_logged = Column(Boolean, default=False)  # Whether user logged these items
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


# ============== Family Sharing Models ==============

class FamilyMember(Base):
    """Family member connections for sharing"""
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Member info
    member_email = Column(String(255), nullable=False)
    member_name = Column(String(100), nullable=False)
    relation_type = Column(String(50), nullable=False)  # mother, father, sister, partner, friend
    
    # Invitation
    invite_code = Column(String(100), unique=True, nullable=False)
    invite_status = Column(String(50), default="pending")  # pending, accepted, declined
    
    # Permissions
    permissions = Column(JSON, default=dict)  # {"can_view_mood": true, "can_view_symptoms": true, ...}
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="family_members")


class FamilyNotification(Base):
    """Notifications for family members"""
    __tablename__ = "family_notifications"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    
    # Notification content
    notification_type = Column(String(100), nullable=False)  # phase_change, mood_update, exercise_completed, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


class CareSuggestion(Base):
    """AI-generated care suggestions for family members"""
    __tablename__ = "care_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Suggestion details
    phase = Column(String(50), nullable=False)  # menstrual, follicular, ovulation, luteal
    suggestion_type = Column(String(100), nullable=False)  # emotional_support, physical_care, dietary, activity
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


class MoodLog(Base):
    """Quick mood logging with emoji"""
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Mood data
    date = Column(Date, nullable=False)
    mood = Column(String(50), nullable=False)  # happy, sad, anxious, calm, irritated, tired, energetic
    mood_emoji = Column(String(10), nullable=True)
    energy_level = Column(Integer, nullable=True)  # 1-5
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


# ============== Hydration & Sleep Models ==============

class WaterLog(Base):
    """Daily water intake tracking"""
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Water data
    date = Column(Date, nullable=False)
    amount_ml = Column(Integer, nullable=False)  # Amount in milliliters
    drink_type = Column(String(50), default="water")  # water, tea, coffee, juice, infused_water
    
    # Time tracking
    logged_at = Column(DateTime, default=func.now())
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())


class DailyHydrationGoal(Base):
    """User's daily hydration goal"""
    __tablename__ = "hydration_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Goal settings
    daily_goal_ml = Column(Integer, default=2500)  # Default 2.5L
    reminder_enabled = Column(Boolean, default=True)
    reminder_interval_hours = Column(Integer, default=2)  # Remind every 2 hours
    
    # Phase-based adjustments
    adjust_for_phase = Column(Boolean, default=True)
    menstrual_multiplier = Column(Float, default=1.2)  # 20% more during period
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SleepLog(Base):
    """Sleep quality and duration tracking"""
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Sleep data
    date = Column(Date, nullable=False)  # Date of sleep (night before)
    bedtime = Column(DateTime, nullable=True)
    wake_time = Column(DateTime, nullable=True)
    duration_hours = Column(Float, nullable=True)
    
    # Quality metrics
    quality_rating = Column(Integer, nullable=True)  # 1-5
    had_cramps = Column(Boolean, default=False)
    had_hot_flashes = Column(Boolean, default=False)
    took_medication = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
