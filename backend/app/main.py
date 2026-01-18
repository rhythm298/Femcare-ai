"""
FemCare AI - Main FastAPI Application
Women's Health Intelligence Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.config import settings
from app.routers import auth, cycles, symptoms, insights, chat, activity, nutrition, family, hydration, mood


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("🚀 Starting FemCare AI...")
    init_db()
    print("✅ FemCare AI is ready!")
    yield
    # Shutdown
    print("👋 Shutting down FemCare AI...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🩺 **FemCare AI** - Comprehensive Women's Health Intelligence Platform
    
    An agentic AI system that provides personalized, proactive women's health management 
    through intelligent health monitoring, risk prediction, and guided wellness support.
    
    ## Features
    
    * 📅 **Cycle Tracking** - Track and predict menstrual cycles
    * 🩹 **Symptom Logging** - Log and analyze symptoms
    * 📊 **Risk Assessment** - AI-powered health risk scoring
    * 💬 **AI Chat** - Personalized health assistant
    * 💡 **Recommendations** - Evidence-based health guidance
    * 🏆 **Gamification** - Health streaks and achievements
    
    ## Privacy First
    
    All data is stored locally. No external API calls required.
    """,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(cycles.router)
app.include_router(symptoms.router)
app.include_router(insights.router)
app.include_router(chat.router)
app.include_router(activity.router)
app.include_router(nutrition.router)
app.include_router(family.router)
app.include_router(hydration.router)
app.include_router(mood.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "message": "Welcome to FemCare AI! 🩺",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "cycles": "/api/cycles",
            "symptoms": "/api/symptoms",
            "insights": "/api/insights",
            "chat": "/api/chat"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
