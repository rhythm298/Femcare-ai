"""
Application configuration for FemCare AI.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "FemCare AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "femcare-ai-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # AI/LLM Settings
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    USE_LOCAL_LLM: bool = True
    
    # Gemini API Fallback (when Ollama is unavailable)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Imagga API for Food Image Analysis (fallback when Ollama unavailable)
    IMAGGA_API_KEY: Optional[str] = None
    IMAGGA_API_SECRET: Optional[str] = None
    
    # Risk Thresholds
    RISK_THRESHOLD_LOW: float = 0.3
    RISK_THRESHOLD_MEDIUM: float = 0.6
    RISK_THRESHOLD_HIGH: float = 0.8
    
    # Confidence Thresholds
    MIN_CONFIDENCE_FOR_ACTION: float = 0.7
    MIN_CYCLES_FOR_PREDICTION: int = 3
    
    # CORS - includes production Netlify domain and local development
    CORS_ORIGINS: List[str] = [
        "https://femcare-ai.netlify.app",
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173"
    ]


# Global settings instance
settings = Settings()


# Symptom categories and types for the classifier
SYMPTOM_TYPES = {
    "physical": [
        "cramps", "headache", "back_pain", "breast_tenderness",
        "bloating", "fatigue", "nausea", "dizziness", "hot_flashes",
        "joint_pain", "muscle_aches", "pelvic_pain"
    ],
    "emotional": [
        "mood_swings", "irritability", "anxiety", "depression",
        "crying_spells", "stress", "low_energy", "difficulty_concentrating"
    ],
    "hormonal": [
        "acne", "oily_skin", "hair_loss", "excessive_hair_growth",
        "weight_changes", "appetite_changes", "libido_changes"
    ],
    "reproductive": [
        "heavy_bleeding", "light_bleeding", "spotting", "clots",
        "irregular_periods", "painful_periods", "vaginal_discharge"
    ],
    "digestive": [
        "constipation", "diarrhea", "gas", "indigestion", "food_cravings"
    ]
}

# All symptoms flattened for quick lookup
ALL_SYMPTOMS = []
for category_symptoms in SYMPTOM_TYPES.values():
    ALL_SYMPTOMS.extend(category_symptoms)

# Achievement definitions
ACHIEVEMENTS = {
    "first_log": {
        "title": "First Steps",
        "description": "Logged your first cycle entry",
        "icon": "🌟"
    },
    "week_streak": {
        "title": "Week Warrior",
        "description": "Maintained a 7-day logging streak",
        "icon": "🔥"
    },
    "month_streak": {
        "title": "Monthly Champion",
        "description": "Maintained a 30-day logging streak",
        "icon": "💪"
    },
    "symptom_tracker": {
        "title": "Symptom Tracker",
        "description": "Logged 50 symptoms",
        "icon": "📝"
    },
    "health_explorer": {
        "title": "Health Explorer",
        "description": "Read 10 educational articles",
        "icon": "📚"
    },
    "pattern_finder": {
        "title": "Pattern Finder",
        "description": "Received your first AI-detected pattern",
        "icon": "🔍"
    },
    "full_profile": {
        "title": "Profile Complete",
        "description": "Filled out all profile information",
        "icon": "✅"
    },
    "cycle_master": {
        "title": "Cycle Master",
        "description": "Tracked 12 complete cycles",
        "icon": "🏆"
    }
}
