"""
Activity and Exercise router for FemCare AI.
Provides period-phase based exercise suggestions, YouTube integration, and exercise logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, timedelta
from typing import List, Optional
import json
import os

from app.database import get_db
from app import models
from app.security import get_current_user

router = APIRouter(prefix="/api/activity", tags=["Activity & Exercise"])


def load_exercises_from_json():
    """Load exercises from JSON file."""
    # Get the path relative to backend directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(base_dir, "data", "exercises.json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Try alternate path
    alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "exercises.json")
    if os.path.exists(alt_path):
        with open(alt_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print(f"Warning: exercises.json not found at {json_path}")
    return []


def seed_exercises(db: Session):
    """Seed exercises from JSON if database is empty."""
    existing_count = db.query(models.Exercise).count()
    if existing_count == 0:
        exercises_data = load_exercises_from_json()
        
        # Valid columns in the Exercise model
        valid_columns = {
            'name', 'category', 'intensity_level', 'duration_minutes',
            'suitable_phases', 'description', 'benefits', 'instructions',
            'youtube_search_query', 'youtube_video_id', 'youtube_video_title',
            'calories_per_minute', 'image_url'
        }
        
        for exercise_data in exercises_data:
            # Filter to only valid columns
            filtered_data = {k: v for k, v in exercise_data.items() if k in valid_columns}
            exercise = models.Exercise(**filtered_data)
            db.add(exercise)
        db.commit()
        print(f"✅ Seeded {len(exercises_data)} exercises")


def get_current_cycle_phase(user_id: int, db: Session) -> str:
    """Get the current cycle phase for a user."""
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == user_id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if not latest_cycle:
        return "follicular"  # Default phase
    
    today = date.today()
    days_since_start = (today - latest_cycle.start_date).days
    
    # Calculate average cycle length
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == user_id,
        models.CycleEntry.cycle_length.isnot(None)
    ).order_by(desc(models.CycleEntry.start_date)).limit(6).all()
    
    avg_cycle_length = 28
    if cycles:
        total = sum(c.cycle_length for c in cycles if c.cycle_length)
        if total > 0:
            avg_cycle_length = total / len(cycles)
    
    # Determine phase based on cycle day
    if days_since_start <= 5:
        return "menstrual"
    elif days_since_start <= 13:
        return "follicular"
    elif days_since_start <= 16:
        return "ovulation"
    elif days_since_start <= avg_cycle_length - 3:
        return "luteal"
    else:
        return "late_luteal"


@router.get("/suggestions")
async def get_exercise_suggestions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized exercise suggestions based on:
    - Current cycle phase
    - Recent exercise history
    - Current symptoms
    - Recent mood and energy levels
    """
    # Seed exercises if needed
    seed_exercises(db)
    
    # Get current phase from actual cycle data
    current_phase = get_current_cycle_phase(current_user.id, db)
    
    # Get recent mood and energy level (last 3 days)
    recent_moods = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == current_user.id,
        models.MoodLog.date >= date.today() - timedelta(days=3)
    ).order_by(desc(models.MoodLog.date)).limit(3).all()
    
    avg_energy = 5  # Default medium energy
    if recent_moods:
        energies = [m.energy_level for m in recent_moods if m.energy_level]
        if energies:
            avg_energy = sum(energies) / len(energies)
    
    # Get recent symptoms (today)
    today_symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date == date.today()
    ).all()
    
    symptom_types = [s.symptom_type for s in today_symptoms]
    has_cramps = any('cramp' in s.lower() for s in symptom_types)
    has_fatigue = any('fatigue' in s.lower() or 'tired' in s.lower() for s in symptom_types)
    has_headache = any('headache' in s.lower() for s in symptom_types)
    
    # Get recent exercise history (last 7 days)
    recent_exercises = db.query(models.ExerciseLog).filter(
        models.ExerciseLog.user_id == current_user.id,
        models.ExerciseLog.date >= date.today() - timedelta(days=7)
    ).all()
    
    recent_categories = [e.exercise_name.lower() for e in recent_exercises]
    exercise_count_this_week = len(recent_exercises)
    
    # Determine recommended intensity based on real data
    if has_cramps or has_fatigue or avg_energy <= 3:
        recommended_intensity = "low"
        intensity_reason = "Based on your current symptoms and energy level"
    elif current_phase in ["menstrual", "late_luteal"]:
        recommended_intensity = "low"
        intensity_reason = f"Gentle exercises recommended during {current_phase} phase"
    elif avg_energy >= 7 and current_phase in ["ovulation", "follicular"]:
        recommended_intensity = "high"
        intensity_reason = "Your energy levels are high - great time for challenging workouts!"
    elif avg_energy >= 5:
        recommended_intensity = "medium"
        intensity_reason = "Moderate intensity based on your current energy level"
    else:
        recommended_intensity = "low"
        intensity_reason = "Lower intensity recommended today"
    
    # Get exercises suitable for current phase
    all_exercises = db.query(models.Exercise).all()
    
    suggested_exercises = []
    for exercise in all_exercises:
        phases = exercise.suitable_phases or []
        if current_phase in phases or "all" in phases:
            # Calculate a personalized score
            score = 0
            
            # Intensity match
            if exercise.intensity_level == recommended_intensity:
                score += 10
            elif exercise.intensity_level == "low" and has_cramps:
                score += 8  # Gentle is good for cramps
            
            # Variety bonus - suggest exercises they haven't done recently
            if exercise.name.lower() not in recent_categories:
                score += 5
            
            # Category preferences based on symptoms
            if has_cramps and exercise.category in ["yoga", "stretching"]:
                score += 7
            if has_headache and exercise.category == "meditation":
                score += 7
            
            suggested_exercises.append({
                "id": exercise.id,
                "name": exercise.name,
                "category": exercise.category,
                "intensity_level": exercise.intensity_level,
                "duration_minutes": exercise.duration_minutes,
                "description": exercise.description,
                "benefits": exercise.benefits,
                "instructions": exercise.instructions or [],
                "youtube_video_id": exercise.youtube_video_id,
                "youtube_video_title": exercise.youtube_video_title,
                "youtube_url": f"https://www.youtube.com/watch?v={exercise.youtube_video_id}" if exercise.youtube_video_id else None,
                "calories_per_minute": exercise.calories_per_minute,
                "image_url": exercise.image_url,
                "suitable_phases": phases,
                "phase_match": True,
                "personalization_score": score
            })
    
    # Sort by personalization score (highest first)
    suggested_exercises.sort(key=lambda x: -x.get("personalization_score", 0))
    
    # Build personalized tip based on real data
    phase_tips = {
        "menstrual": "During your period, focus on gentle movements like yoga and stretching. Listen to your body and rest when needed.",
        "follicular": "Energy is rising! This is a great time for more intense workouts and trying new exercises.",
        "ovulation": "Peak energy levels! Take advantage with HIIT, strength training, and challenging workouts.",
        "luteal": "Energy may start to dip. Mix moderate and gentle exercises based on how you feel.",
        "late_luteal": "Focus on restorative activities. Yoga, stretching, and meditation are ideal."
    }
    
    personal_insights = []
    if has_cramps:
        personal_insights.append("🌸 Gentle stretching recommended for cramp relief")
    if has_fatigue:
        personal_insights.append("💤 Light exercises today - listen to your body")
    if exercise_count_this_week >= 5:
        personal_insights.append("🏆 Great week! Consider a rest day")
    elif exercise_count_this_week == 0:
        personal_insights.append("💪 Start your week with something light!")
    
    return {
        "current_phase": current_phase,
        "phase_tip": phase_tips.get(current_phase, ""),
        "intensity_recommendation": {
            "level": recommended_intensity,
            "reason": intensity_reason
        },
        "personal_insights": personal_insights,
        "energy_level": round(avg_energy, 1),
        "exercises_this_week": exercise_count_this_week,
        "suggestions": suggested_exercises[:10],
        "total_available": len(suggested_exercises)
    }


@router.get("/exercises")
async def get_all_exercises(
    category: Optional[str] = Query(None, description="Filter by category"),
    intensity: Optional[str] = Query(None, description="Filter by intensity level"),
    phase: Optional[str] = Query(None, description="Filter by suitable phase"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available exercises with optional filters.
    """
    seed_exercises(db)
    
    query = db.query(models.Exercise)
    
    if category:
        query = query.filter(models.Exercise.category == category)
    
    if intensity:
        query = query.filter(models.Exercise.intensity_level == intensity)
    
    if search:
        query = query.filter(models.Exercise.name.ilike(f"%{search}%"))
    
    exercises = query.offset(skip).limit(limit).all()
    
    result = []
    for exercise in exercises:
        # Filter by phase if specified
        if phase:
            phases = exercise.suitable_phases or []
            if phase not in phases:
                continue
        
        result.append({
            "id": exercise.id,
            "name": exercise.name,
            "category": exercise.category,
            "intensity_level": exercise.intensity_level,
            "duration_minutes": exercise.duration_minutes,
            "description": exercise.description,
            "benefits": exercise.benefits,
            "instructions": exercise.instructions or [],
            "youtube_video_id": exercise.youtube_video_id,
            "youtube_video_title": exercise.youtube_video_title,
            "youtube_url": f"https://www.youtube.com/watch?v={exercise.youtube_video_id}" if exercise.youtube_video_id else None,
            "calories_per_minute": exercise.calories_per_minute,
            "image_url": exercise.image_url,
            "suitable_phases": exercise.suitable_phases or []
        })
    
    return {
        "exercises": result,
        "total": len(result),
        "categories": ["yoga", "cardio", "strength", "stretching", "pilates", "swimming", "meditation", "dance", "recovery", "low_impact"]
    }


@router.post("/log")
async def log_exercise(
    exercise_name: str,
    duration_minutes: int,
    exercise_id: Optional[int] = None,
    intensity: Optional[str] = None,
    notes: Optional[str] = None,
    youtube_video_watched: Optional[str] = None,
    difficulty_rating: Optional[int] = Query(None, ge=1, le=5),
    enjoyment_rating: Optional[int] = Query(None, ge=1, le=5),
    log_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a completed exercise.
    """
    # Calculate calories burned
    calories_burned = None
    if exercise_id:
        exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
        if exercise:
            calories_burned = exercise.calories_per_minute * duration_minutes
    else:
        # Default calculation for custom exercises
        intensity_calories = {"low": 4, "medium": 6, "high": 10}
        cal_per_min = intensity_calories.get(intensity or "medium", 6)
        calories_burned = cal_per_min * duration_minutes
    
    # Create exercise log
    exercise_log = models.ExerciseLog(
        user_id=current_user.id,
        exercise_id=exercise_id,
        exercise_name=exercise_name,
        date=log_date or date.today(),
        duration_minutes=duration_minutes,
        calories_burned=calories_burned,
        intensity=intensity,
        notes=notes,
        youtube_video_watched=youtube_video_watched,
        difficulty_rating=difficulty_rating,
        enjoyment_rating=enjoyment_rating
    )
    
    db.add(exercise_log)
    
    # Update exercise streak
    streak = db.query(models.HealthStreak).filter(
        models.HealthStreak.user_id == current_user.id,
        models.HealthStreak.streak_type == "exercise"
    ).first()
    
    if not streak:
        streak = models.HealthStreak(
            user_id=current_user.id,
            streak_type="exercise",
            current_streak=1,
            longest_streak=1,
            last_activity_date=log_date or date.today(),
            total_activities=1
        )
        db.add(streak)
    else:
        today = log_date or date.today()
        if streak.last_activity_date:
            days_diff = (today - streak.last_activity_date).days
            if days_diff == 1:
                streak.current_streak += 1
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
            elif days_diff > 1:
                streak.current_streak = 1
        streak.last_activity_date = today
        streak.total_activities += 1
    
    db.commit()
    db.refresh(exercise_log)
    
    return {
        "id": exercise_log.id,
        "exercise_name": exercise_log.exercise_name,
        "duration_minutes": exercise_log.duration_minutes,
        "calories_burned": exercise_log.calories_burned,
        "date": str(exercise_log.date),
        "current_streak": streak.current_streak,
        "message": f"Great job completing {exercise_name}! You burned approximately {calories_burned:.0f} calories."
    }


@router.get("/logs")
async def get_exercise_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get exercise history for the current user.
    """
    query = db.query(models.ExerciseLog).filter(
        models.ExerciseLog.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(models.ExerciseLog.date >= start_date)
    if end_date:
        query = query.filter(models.ExerciseLog.date <= end_date)
    
    logs = query.order_by(desc(models.ExerciseLog.date)).offset(skip).limit(limit).all()
    
    return {
        "logs": [{
            "id": log.id,
            "exercise_name": log.exercise_name,
            "date": str(log.date),
            "duration_minutes": log.duration_minutes,
            "calories_burned": log.calories_burned,
            "intensity": log.intensity,
            "notes": log.notes,
            "difficulty_rating": log.difficulty_rating,
            "enjoyment_rating": log.enjoyment_rating,
            "youtube_video_watched": log.youtube_video_watched
        } for log in logs],
        "total": len(logs)
    }


@router.get("/stats")
async def get_exercise_stats(
    days: int = Query(30, ge=7, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get exercise statistics for the current user.
    """
    start_date = date.today() - timedelta(days=days)
    
    logs = db.query(models.ExerciseLog).filter(
        models.ExerciseLog.user_id == current_user.id,
        models.ExerciseLog.date >= start_date
    ).all()
    
    if not logs:
        return {
            "total_workouts": 0,
            "total_duration_minutes": 0,
            "total_calories_burned": 0,
            "avg_duration_per_workout": 0,
            "avg_calories_per_workout": 0,
            "favorite_exercises": [],
            "workouts_by_category": {},
            "current_streak": 0,
            "longest_streak": 0
        }
    
    total_duration = sum(log.duration_minutes for log in logs)
    total_calories = sum(log.calories_burned or 0 for log in logs)
    
    # Count exercises by name
    exercise_counts = {}
    category_counts = {}
    for log in logs:
        exercise_counts[log.exercise_name] = exercise_counts.get(log.exercise_name, 0) + 1
        # Get category if we have exercise_id
        if log.exercise_id:
            exercise = db.query(models.Exercise).filter(models.Exercise.id == log.exercise_id).first()
            if exercise:
                category_counts[exercise.category] = category_counts.get(exercise.category, 0) + 1
    
    favorite_exercises = sorted(exercise_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Get streak info
    streak = db.query(models.HealthStreak).filter(
        models.HealthStreak.user_id == current_user.id,
        models.HealthStreak.streak_type == "exercise"
    ).first()
    
    return {
        "total_workouts": len(logs),
        "total_duration_minutes": total_duration,
        "total_calories_burned": round(total_calories, 0),
        "avg_duration_per_workout": round(total_duration / len(logs), 1),
        "avg_calories_per_workout": round(total_calories / len(logs), 0),
        "favorite_exercises": [{"name": name, "count": count} for name, count in favorite_exercises],
        "workouts_by_category": category_counts,
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "total_activities": streak.total_activities if streak else len(logs)
    }


@router.get("/youtube/{exercise_id}")
async def get_youtube_video(
    exercise_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get YouTube video information for an exercise.
    """
    exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if not exercise.youtube_video_id:
        return {
            "has_video": False,
            "message": "No video available for this exercise",
            "search_query": exercise.youtube_search_query
        }
    
    return {
        "has_video": True,
        "video_id": exercise.youtube_video_id,
        "video_title": exercise.youtube_video_title,
        "video_url": f"https://www.youtube.com/watch?v={exercise.youtube_video_id}",
        "embed_url": f"https://www.youtube.com/embed/{exercise.youtube_video_id}",
        "thumbnail_url": f"https://img.youtube.com/vi/{exercise.youtube_video_id}/hqdefault.jpg"
    }
