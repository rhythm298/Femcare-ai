"""
Symptom logging router for FemCare AI.
Handles symptom tracking and analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, timedelta
from typing import List, Optional
import numpy as np

from app.database import get_db
from app import models, schemas
from app.security import get_current_user
from app.config import SYMPTOM_TYPES, ALL_SYMPTOMS

router = APIRouter(prefix="/api/symptoms", tags=["Symptom Tracking"])


def classify_symptom(symptom_type: str, description: Optional[str] = None) -> dict:
    """
    Classify a symptom into category and provide additional context.
    This is a simplified version - in production, use BioClinicalBERT.
    """
    symptom_lower = symptom_type.lower().replace(" ", "_")
    
    # Determine category
    category = "other"
    for cat, symptoms in SYMPTOM_TYPES.items():
        if symptom_lower in symptoms:
            category = cat
            break
    
    # Simple keyword-based classification from description
    keywords = {
        "severe": {"urgency": "high"},
        "intense": {"urgency": "high"},
        "mild": {"urgency": "low"},
        "chronic": {"pattern": "recurring"},
        "sudden": {"pattern": "acute"},
        "persistent": {"pattern": "chronic"}
    }
    
    context = {}
    if description:
        desc_lower = description.lower()
        for keyword, info in keywords.items():
            if keyword in desc_lower:
                context.update(info)
    
    return {
        "category": category,
        "standardized_name": symptom_lower,
        "context": context
    }


@router.post("/", response_model=schemas.SymptomResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom(
    symptom_data: schemas.SymptomCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a new symptom entry.
    """
    # AI classification
    classification = classify_symptom(symptom_data.symptom_type, symptom_data.description)
    
    # Find associated cycle if any
    cycle_id = symptom_data.cycle_id
    if not cycle_id:
        # Try to find the current cycle
        current_cycle = db.query(models.CycleEntry).filter(
            models.CycleEntry.user_id == current_user.id,
            models.CycleEntry.start_date <= symptom_data.date
        ).order_by(desc(models.CycleEntry.start_date)).first()
        
        if current_cycle:
            # Check if symptom date is within reasonable range of cycle
            if current_cycle.cycle_length:
                max_date = current_cycle.start_date + timedelta(days=current_cycle.cycle_length)
            else:
                max_date = current_cycle.start_date + timedelta(days=45)
            
            if symptom_data.date <= max_date:
                cycle_id = current_cycle.id
    
    # Create symptom
    new_symptom = models.Symptom(
        user_id=current_user.id,
        cycle_id=cycle_id,
        date=symptom_data.date,
        symptom_type=symptom_data.symptom_type,
        category=classification["category"],
        severity=symptom_data.severity,
        description=symptom_data.description,
        duration_hours=symptom_data.duration_hours,
        ai_classification=classification
    )
    
    db.add(new_symptom)
    
    # Update logging streak
    streak = db.query(models.HealthStreak).filter(
        models.HealthStreak.user_id == current_user.id,
        models.HealthStreak.streak_type == "logging"
    ).first()
    
    if streak:
        today = date.today()
        if streak.last_activity_date:
            days_diff = (today - streak.last_activity_date).days
            if days_diff == 1:
                streak.current_streak += 1
            elif days_diff > 1:
                streak.current_streak = 1
            # Same day doesn't change streak
        else:
            streak.current_streak = 1
        
        streak.last_activity_date = today
        streak.total_activities += 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    
    # Check for symptom tracker achievement
    total_symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id
    ).count()
    
    if total_symptoms >= 50:
        existing = db.query(models.Achievement).filter(
            models.Achievement.user_id == current_user.id,
            models.Achievement.achievement_type == "symptom_tracker"
        ).first()
        
        if not existing:
            achievement = models.Achievement(
                user_id=current_user.id,
                achievement_type="symptom_tracker",
                title="Symptom Tracker 📝",
                description="You've logged 50 symptoms!",
                icon="📝"
            )
            db.add(achievement)
    
    db.commit()
    db.refresh(new_symptom)
    
    return new_symptom


@router.get("/", response_model=List[schemas.SymptomResponse])
async def get_symptoms(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get symptom entries with optional filtering.
    """
    query = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(models.Symptom.date >= start_date)
    if end_date:
        query = query.filter(models.Symptom.date <= end_date)
    if category:
        query = query.filter(models.Symptom.category == category)
    
    symptoms = query.order_by(desc(models.Symptom.date)).offset(skip).limit(limit).all()
    
    return symptoms


@router.get("/today", response_model=List[schemas.SymptomResponse])
async def get_today_symptoms(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get symptoms logged today.
    """
    today = date.today()
    symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date == today
    ).all()
    
    return symptoms


@router.get("/analysis", response_model=schemas.SymptomAnalysis)
async def get_symptom_analysis(
    days: int = Query(30, ge=7, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive symptom analysis.
    """
    start_date = date.today() - timedelta(days=days)
    
    symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date >= start_date
    ).all()
    
    if not symptoms:
        return {
            "total_symptoms": 0,
            "symptoms_by_category": {},
            "average_severity": 0,
            "most_common": [],
            "severity_trend": "stable",
            "correlations": [],
            "recommendations": ["Start tracking symptoms to get personalized insights!"]
        }
    
    # Category breakdown
    category_counts = {}
    for symptom in symptoms:
        cat = symptom.category
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Average severity
    avg_severity = np.mean([s.severity for s in symptoms])
    
    # Most common symptoms
    symptom_counts = {}
    for symptom in symptoms:
        key = symptom.symptom_type
        if key in symptom_counts:
            symptom_counts[key]["count"] += 1
            symptom_counts[key]["total_severity"] += symptom.severity
        else:
            symptom_counts[key] = {"count": 1, "total_severity": symptom.severity}
    
    most_common = [
        {
            "symptom": k,
            "count": v["count"],
            "avg_severity": round(v["total_severity"] / v["count"], 1)
        }
        for k, v in sorted(symptom_counts.items(), key=lambda x: -x[1]["count"])[:5]
    ]
    
    # Severity trend (compare first half to second half)
    sorted_symptoms = sorted(symptoms, key=lambda s: s.date)
    mid = len(sorted_symptoms) // 2
    
    if mid > 0:
        first_half_avg = np.mean([s.severity for s in sorted_symptoms[:mid]])
        second_half_avg = np.mean([s.severity for s in sorted_symptoms[mid:]])
        
        if second_half_avg < first_half_avg - 0.5:
            severity_trend = "improving"
        elif second_half_avg > first_half_avg + 0.5:
            severity_trend = "worsening"
        else:
            severity_trend = "stable"
    else:
        severity_trend = "stable"
    
    # Correlations (simplified - check for symptoms that occur together)
    correlations = []
    dates_symptoms = {}
    for symptom in symptoms:
        d = symptom.date
        if d not in dates_symptoms:
            dates_symptoms[d] = []
        dates_symptoms[d].append(symptom.symptom_type)
    
    # Find co-occurring symptoms
    co_occurrences = {}
    for d, syms in dates_symptoms.items():
        if len(syms) > 1:
            for i, s1 in enumerate(syms):
                for s2 in syms[i+1:]:
                    pair = tuple(sorted([s1, s2]))
                    co_occurrences[pair] = co_occurrences.get(pair, 0) + 1
    
    for pair, count in sorted(co_occurrences.items(), key=lambda x: -x[1])[:3]:
        if count >= 2:
            correlations.append({
                "symptoms": list(pair),
                "co_occurrence_count": count,
                "insight": f"{pair[0]} and {pair[1]} often occur together"
            })
    
    # Generate recommendations based on symptoms
    recommendations = []
    
    if "cramps" in symptom_counts and symptom_counts["cramps"]["count"] >= 3:
        recommendations.append("Consider heat therapy or gentle exercise for recurring cramps")
    
    if "fatigue" in symptom_counts:
        recommendations.append("Track your sleep patterns - fatigue may be linked to sleep quality")
    
    if "headache" in symptom_counts:
        recommendations.append("Monitor hydration and caffeine intake for headache management")
    
    if avg_severity > 6:
        recommendations.append("Your symptoms have been quite severe - consider consulting a healthcare provider")
    
    if not recommendations:
        recommendations.append("Keep tracking to build a complete picture of your health patterns!")
    
    return {
        "total_symptoms": len(symptoms),
        "symptoms_by_category": category_counts,
        "average_severity": round(avg_severity, 1),
        "most_common": most_common,
        "severity_trend": severity_trend,
        "correlations": correlations,
        "recommendations": recommendations
    }


@router.get("/types")
async def get_symptom_types():
    """
    Get all available symptom types organized by category.
    """
    return SYMPTOM_TYPES


@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom(
    symptom_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a symptom entry.
    """
    symptom = db.query(models.Symptom).filter(
        models.Symptom.id == symptom_id,
        models.Symptom.user_id == current_user.id
    ).first()
    
    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    
    db.delete(symptom)
    db.commit()
    
    return None
