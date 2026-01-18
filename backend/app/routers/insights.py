"""
Health insights router for FemCare AI.
Provides AI-generated insights, risk assessments, and recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta, datetime
from typing import List, Optional
import numpy as np

from app.database import get_db
from app import models, schemas
from app.security import get_current_user

router = APIRouter(prefix="/api/insights", tags=["Health Insights"])


def calculate_pcos_risk(user: models.User, cycles: List[models.CycleEntry], symptoms: List[models.Symptom]) -> dict:
    """
    Calculate PCOS risk score based on available data.
    Returns score, confidence, and contributing factors.
    """
    factors = []
    scores = []
    weights = []
    
    # Cycle irregularity (major factor)
    if len(cycles) >= 3:
        cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
        if cycle_lengths:
            avg_length = np.mean(cycle_lengths)
            std_length = np.std(cycle_lengths)
            
            # Long cycles (>35 days) or high variability
            if avg_length > 35:
                scores.append(0.8)
                weights.append(3)
                factors.append({"factor": "Long cycle length", "value": f"{avg_length:.1f} days avg", "impact": "high"})
            elif avg_length > 32:
                scores.append(0.5)
                weights.append(3)
                factors.append({"factor": "Slightly long cycles", "value": f"{avg_length:.1f} days avg", "impact": "medium"})
            else:
                scores.append(0.1)
                weights.append(3)
            
            if std_length > 7:
                scores.append(0.7)
                weights.append(2)
                factors.append({"factor": "Irregular cycle pattern", "value": f"±{std_length:.1f} days variation", "impact": "high"})
    
    # Hormonal symptoms
    hormonal_symptoms = [s for s in symptoms if s.category == "hormonal"]
    if hormonal_symptoms:
        acne_count = len([s for s in hormonal_symptoms if "acne" in s.symptom_type.lower()])
        hair_issues = len([s for s in hormonal_symptoms if "hair" in s.symptom_type.lower()])
        weight_issues = len([s for s in hormonal_symptoms if "weight" in s.symptom_type.lower()])
        
        if acne_count >= 3:
            scores.append(0.6)
            weights.append(1.5)
            factors.append({"factor": "Persistent acne", "value": f"{acne_count} occurrences", "impact": "medium"})
        
        if hair_issues >= 2:
            scores.append(0.5)
            weights.append(1.5)
            factors.append({"factor": "Hair-related symptoms", "value": f"{hair_issues} occurrences", "impact": "medium"})
        
        if weight_issues >= 2:
            scores.append(0.4)
            weights.append(1)
            factors.append({"factor": "Weight changes", "value": f"{weight_issues} occurrences", "impact": "low"})
    
    # BMI factor (if available)
    if user.weight and user.height:
        bmi = user.weight / ((user.height / 100) ** 2)
        if bmi > 30:
            scores.append(0.6)
            weights.append(1.5)
            factors.append({"factor": "BMI", "value": f"{bmi:.1f}", "impact": "medium"})
        elif bmi > 25:
            scores.append(0.3)
            weights.append(1)
    
    # Calculate weighted score
    if scores and weights:
        score = np.average(scores, weights=weights)
        # Confidence based on data availability
        data_points = len(cycles) + len(symptoms)
        confidence = min(0.9, 0.3 + (data_points / 50))
    else:
        score = 0.1
        confidence = 0.2
    
    return {
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "factors": factors
    }


def calculate_endometriosis_risk(symptoms: List[models.Symptom], cycles: List[models.CycleEntry]) -> dict:
    """
    Calculate endometriosis risk based on pain patterns and symptoms.
    """
    factors = []
    scores = []
    weights = []
    
    # Pain-related symptoms
    pain_symptoms = [s for s in symptoms if "pain" in s.symptom_type.lower() or s.symptom_type.lower() == "cramps"]
    
    if pain_symptoms:
        avg_severity = np.mean([s.severity for s in pain_symptoms])
        
        if avg_severity >= 7:
            scores.append(0.8)
            weights.append(3)
            factors.append({"factor": "Severe pelvic/menstrual pain", "value": f"Avg severity: {avg_severity:.1f}/10", "impact": "high"})
        elif avg_severity >= 5:
            scores.append(0.5)
            weights.append(3)
            factors.append({"factor": "Moderate pelvic pain", "value": f"Avg severity: {avg_severity:.1f}/10", "impact": "medium"})
        
        # Pain frequency
        if len(pain_symptoms) >= 10:
            scores.append(0.7)
            weights.append(2)
            factors.append({"factor": "Frequent pain episodes", "value": f"{len(pain_symptoms)} occurrences", "impact": "high"})
    
    # Heavy bleeding
    heavy_cycles = [c for c in cycles if c.flow_level in ["heavy", "very_heavy"]]
    if len(heavy_cycles) >= 2:
        scores.append(0.5)
        weights.append(1.5)
        factors.append({"factor": "Heavy menstrual bleeding", "value": f"{len(heavy_cycles)} cycles", "impact": "medium"})
    
    # Fatigue correlation with period
    fatigue_symptoms = [s for s in symptoms if "fatigue" in s.symptom_type.lower()]
    if len(fatigue_symptoms) >= 5:
        scores.append(0.4)
        weights.append(1)
        factors.append({"factor": "Chronic fatigue", "value": f"{len(fatigue_symptoms)} occurrences", "impact": "low"})
    
    if scores and weights:
        score = np.average(scores, weights=weights)
        confidence = min(0.85, 0.3 + (len(symptoms) / 40))
    else:
        score = 0.1
        confidence = 0.2
    
    return {
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "factors": factors
    }


def calculate_anemia_risk(symptoms: List[models.Symptom], cycles: List[models.CycleEntry]) -> dict:
    """
    Calculate anemia risk based on symptoms and menstrual patterns.
    """
    factors = []
    scores = []
    weights = []
    
    # Heavy bleeding is a major factor
    heavy_cycles = [c for c in cycles if c.flow_level in ["heavy", "very_heavy"]]
    if heavy_cycles:
        ratio = len(heavy_cycles) / max(len(cycles), 1)
        if ratio > 0.5:
            scores.append(0.7)
            weights.append(3)
            factors.append({"factor": "Consistently heavy periods", "value": f"{len(heavy_cycles)}/{len(cycles)} cycles", "impact": "high"})
        elif ratio > 0.25:
            scores.append(0.4)
            weights.append(2)
            factors.append({"factor": "Occasional heavy periods", "value": f"{len(heavy_cycles)}/{len(cycles)} cycles", "impact": "medium"})
    
    # Fatigue symptoms
    fatigue_symptoms = [s for s in symptoms if "fatigue" in s.symptom_type.lower() or "tired" in s.symptom_type.lower()]
    if fatigue_symptoms:
        avg_severity = np.mean([s.severity for s in fatigue_symptoms])
        if avg_severity >= 6:
            scores.append(0.6)
            weights.append(2)
            factors.append({"factor": "Significant fatigue", "value": f"Severity: {avg_severity:.1f}/10", "impact": "medium"})
    
    # Dizziness
    dizziness = [s for s in symptoms if "dizz" in s.symptom_type.lower()]
    if len(dizziness) >= 2:
        scores.append(0.5)
        weights.append(1.5)
        factors.append({"factor": "Episodes of dizziness", "value": f"{len(dizziness)} occurrences", "impact": "medium"})
    
    # Headaches
    headaches = [s for s in symptoms if "headache" in s.symptom_type.lower()]
    if len(headaches) >= 5:
        scores.append(0.3)
        weights.append(1)
        factors.append({"factor": "Frequent headaches", "value": f"{len(headaches)} occurrences", "impact": "low"})
    
    if scores and weights:
        score = np.average(scores, weights=weights)
        confidence = min(0.85, 0.3 + (len(symptoms) / 40))
    else:
        score = 0.1
        confidence = 0.2
    
    return {
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "factors": factors
    }


def calculate_thyroid_risk(user: models.User, symptoms: List[models.Symptom], cycles: List[models.CycleEntry]) -> dict:
    """
    Calculate thyroid disorder risk indicators.
    """
    factors = []
    scores = []
    weights = []
    
    # Weight changes
    weight_symptoms = [s for s in symptoms if "weight" in s.symptom_type.lower()]
    if len(weight_symptoms) >= 2:
        scores.append(0.5)
        weights.append(2)
        factors.append({"factor": "Weight fluctuations", "value": f"{len(weight_symptoms)} reported", "impact": "medium"})
    
    # Fatigue
    fatigue = [s for s in symptoms if "fatigue" in s.symptom_type.lower()]
    if len(fatigue) >= 5:
        scores.append(0.4)
        weights.append(1.5)
        factors.append({"factor": "Persistent fatigue", "value": f"{len(fatigue)} occurrences", "impact": "medium"})
    
    # Mood symptoms
    mood_symptoms = [s for s in symptoms if s.category == "emotional"]
    if len(mood_symptoms) >= 8:
        scores.append(0.4)
        weights.append(1)
        factors.append({"factor": "Mood changes", "value": f"{len(mood_symptoms)} emotional symptoms", "impact": "low"})
    
    # Cycle irregularity (also thyroid indicator)
    if len(cycles) >= 3:
        cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
        if cycle_lengths:
            std_length = np.std(cycle_lengths)
            if std_length > 10:
                scores.append(0.5)
                weights.append(1.5)
                factors.append({"factor": "Very irregular cycles", "value": f"±{std_length:.1f} days", "impact": "medium"})
    
    # Hair symptoms
    hair_symptoms = [s for s in symptoms if "hair" in s.symptom_type.lower()]
    if hair_symptoms:
        scores.append(0.4)
        weights.append(1)
        factors.append({"factor": "Hair changes", "value": f"{len(hair_symptoms)} occurrences", "impact": "low"})
    
    if scores and weights:
        score = np.average(scores, weights=weights)
        confidence = min(0.8, 0.25 + (len(symptoms) / 50))
    else:
        score = 0.1
        confidence = 0.2
    
    return {
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "factors": factors
    }


@router.get("/risks")
async def get_risk_assessment(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive risk assessment for all tracked conditions.
    """
    # Get user data
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(models.CycleEntry.start_date).all()
    
    # Get symptoms from last 6 months
    six_months_ago = date.today() - timedelta(days=180)
    symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date >= six_months_ago
    ).all()
    
    # Calculate all risk scores
    pcos_result = calculate_pcos_risk(current_user, cycles, symptoms)
    endo_result = calculate_endometriosis_risk(symptoms, cycles)
    anemia_result = calculate_anemia_risk(symptoms, cycles)
    thyroid_result = calculate_thyroid_risk(current_user, symptoms, cycles)
    
    # Save to database
    now = datetime.utcnow()
    
    for condition, result in [
        ("pcos", pcos_result),
        ("endometriosis", endo_result),
        ("anemia", anemia_result),
        ("thyroid", thyroid_result)
    ]:
        # Get previous score
        previous = db.query(models.RiskScore).filter(
            models.RiskScore.user_id == current_user.id,
            models.RiskScore.condition_type == condition
        ).order_by(desc(models.RiskScore.calculated_at)).first()
        
        previous_score = previous.score if previous else None
        
        # Determine trend
        if previous_score is not None:
            diff = result["score"] - previous_score
            if diff < -0.1:
                trend = "improving"
            elif diff > 0.1:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = None
        
        risk_score = models.RiskScore(
            user_id=current_user.id,
            condition_type=condition,
            score=result["score"],
            confidence=result["confidence"],
            contributing_factors=result["factors"],
            previous_score=previous_score,
            trend=trend
        )
        db.add(risk_score)
    
    db.commit()
    
    # Calculate overall health score (inverse of weighted risk average)
    all_scores = [pcos_result["score"], endo_result["score"], anemia_result["score"], thyroid_result["score"]]
    avg_risk = np.mean(all_scores)
    overall_health_score = round((1 - avg_risk) * 100, 1)
    
    # Determine priority concerns
    priority_concerns = []
    for condition, result in [
        ("PCOS", pcos_result),
        ("Endometriosis", endo_result),
        ("Anemia", anemia_result),
        ("Thyroid", thyroid_result)
    ]:
        if result["score"] >= 0.6:
            priority_concerns.append(f"{condition} risk is elevated ({result['score']*100:.0f}%)")
    
    return {
        "pcos": pcos_result,
        "endometriosis": endo_result,
        "anemia": anemia_result,
        "thyroid": thyroid_result,
        "overall_health_score": overall_health_score,
        "priority_concerns": priority_concerns,
        "calculated_at": now.isoformat()
    }


@router.get("/recommendations", response_model=List[schemas.RecommendationResponse])
async def get_recommendations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized health recommendations.
    """
    # Get pending recommendations
    recommendations = db.query(models.Recommendation).filter(
        models.Recommendation.user_id == current_user.id,
        models.Recommendation.is_completed == False
    ).order_by(desc(models.Recommendation.priority)).all()
    
    # If no recommendations, generate some based on current data
    if not recommendations:
        await generate_recommendations(current_user, db)
        recommendations = db.query(models.Recommendation).filter(
            models.Recommendation.user_id == current_user.id,
            models.Recommendation.is_completed == False
        ).order_by(desc(models.Recommendation.priority)).all()
    
    return recommendations


async def generate_recommendations(user: models.User, db: Session):
    """
    Generate personalized recommendations based on user data.
    """
    # Get recent data
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == user.id
    ).all()
    
    symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == user.id
    ).all()
    
    recommendations_to_add = []
    
    # Profile completion
    if not user.date_of_birth or not user.weight or not user.height:
        recommendations_to_add.append({
            "category": "tracking",
            "title": "Complete Your Health Profile",
            "description": "Adding your age, weight, and height helps us provide more accurate health insights.",
            "priority": 8,
            "action_steps": ["Go to Settings", "Fill in your personal information", "Save your profile"],
            "reason": "Complete profiles enable better risk calculations and personalized recommendations."
        })
    
    # Track more cycles
    if len(cycles) < 3:
        recommendations_to_add.append({
            "category": "tracking",
            "title": "Continue Cycle Tracking",
            "description": f"You've logged {len(cycles)} cycle(s). Track at least 3 cycles for accurate predictions.",
            "priority": 9,
            "action_steps": ["Log your next period when it starts", "Note the end date when it finishes"],
            "reason": "More cycle data = more accurate predictions and pattern detection."
        })
    
    # Symptom tracking
    if len(symptoms) < 10:
        recommendations_to_add.append({
            "category": "tracking",
            "title": "Log Your Symptoms Daily",
            "description": "Regular symptom tracking helps identify patterns and potential health concerns.",
            "priority": 7,
            "action_steps": ["Open the Symptom Logger each day", "Record how you're feeling", "Rate symptom severity"],
            "reason": "Symptoms often correlate with your cycle phase and can reveal important health patterns."
        })
    
    # Based on symptoms
    pain_symptoms = [s for s in symptoms if "pain" in s.symptom_type.lower() or s.symptom_type.lower() == "cramps"]
    if len(pain_symptoms) >= 3:
        avg_severity = np.mean([s.severity for s in pain_symptoms])
        if avg_severity >= 6:
            recommendations_to_add.append({
                "category": "lifestyle",
                "title": "Pain Management Strategies",
                "description": "Your pain symptoms have been significant. Try these evidence-based approaches.",
                "priority": 8,
                "action_steps": [
                    "Apply heat therapy during painful episodes",
                    "Try gentle yoga or stretching",
                    "Consider anti-inflammatory foods",
                    "Track what helps reduce your pain"
                ],
                "reason": f"Your average pain severity is {avg_severity:.1f}/10. These strategies may help."
            })
    
    # Fatigue
    fatigue = [s for s in symptoms if "fatigue" in s.symptom_type.lower()]
    if len(fatigue) >= 3:
        recommendations_to_add.append({
            "category": "lifestyle",
            "title": "Boost Your Energy Levels",
            "description": "You've been experiencing fatigue. Here are some strategies to help.",
            "priority": 6,
            "action_steps": [
                "Aim for 7-9 hours of sleep",
                "Stay hydrated throughout the day",
                "Include iron-rich foods in your diet",
                "Consider gentle exercise"
            ],
            "reason": "Fatigue can be linked to your cycle, diet, or other factors."
        })
    
    # General wellness
    recommendations_to_add.append({
        "category": "medical",
        "title": "Schedule Regular Check-ups",
        "description": "Annual gynecological exams are important for preventive care.",
        "priority": 5,
        "action_steps": [
            "Schedule your annual well-woman visit",
            "Bring your cycle and symptom data to share",
            "Prepare questions about any concerns"
        ],
        "reason": "Regular check-ups help catch potential issues early."
    })
    
    # Add recommendations to database
    for rec_data in recommendations_to_add[:5]:  # Limit to 5
        # Check if similar recommendation exists
        existing = db.query(models.Recommendation).filter(
            models.Recommendation.user_id == user.id,
            models.Recommendation.title == rec_data["title"],
            models.Recommendation.is_completed == False
        ).first()
        
        if not existing:
            rec = models.Recommendation(
                user_id=user.id,
                **rec_data
            )
            db.add(rec)
    
    db.commit()


@router.post("/recommendations/{rec_id}/complete")
async def complete_recommendation(
    rec_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a recommendation as completed.
    """
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.id == rec_id,
        models.Recommendation.user_id == current_user.id
    ).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    rec.is_completed = True
    rec.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Recommendation completed! 🎉"}


@router.get("/timeline")
async def get_health_timeline(
    days: int = Query(90, ge=7, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get health timeline with all events.
    """
    start_date = date.today() - timedelta(days=days)
    end_date = date.today()
    
    events = []
    
    # Add cycle events
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id,
        models.CycleEntry.start_date >= start_date
    ).all()
    
    for cycle in cycles:
        events.append({
            "id": cycle.id,
            "event_type": "cycle_start",
            "date": cycle.start_date.isoformat(),
            "title": "Period Started",
            "description": f"Flow level: {cycle.flow_level}",
            "metadata": {"flow_level": cycle.flow_level}
        })
        if cycle.end_date:
            events.append({
                "id": cycle.id * 1000,  # Unique ID
                "event_type": "cycle_end",
                "date": cycle.end_date.isoformat(),
                "title": "Period Ended",
                "description": f"Duration: {cycle.period_length} days" if cycle.period_length else None,
                "metadata": {"period_length": cycle.period_length}
            })
    
    # Add symptoms
    symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date >= start_date
    ).all()
    
    for symptom in symptoms:
        events.append({
            "id": symptom.id + 100000,
            "event_type": "symptom",
            "date": symptom.date.isoformat(),
            "title": symptom.symptom_type.replace("_", " ").title(),
            "description": f"Severity: {symptom.severity}/10",
            "metadata": {
                "severity": symptom.severity,
                "category": symptom.category
            }
        })
    
    # Add insights
    insights = db.query(models.HealthInsight).filter(
        models.HealthInsight.user_id == current_user.id,
        models.HealthInsight.created_at >= datetime.combine(start_date, datetime.min.time())
    ).all()
    
    for insight in insights:
        events.append({
            "id": insight.id + 200000,
            "event_type": "insight",
            "date": insight.created_at.date().isoformat(),
            "title": insight.title,
            "description": insight.content[:100] + "..." if len(insight.content) > 100 else insight.content,
            "metadata": {"priority": insight.priority}
        })
    
    # Sort by date
    events.sort(key=lambda x: x["date"], reverse=True)
    
    # Detect patterns
    patterns = []
    
    # Check for symptom-cycle correlations
    if cycles and symptoms:
        # Group symptoms by cycle day
        for cycle in cycles:
            cycle_symptoms = [s for s in symptoms if cycle.start_date <= s.date]
            if cycle.cycle_length:
                cycle_symptoms = [s for s in cycle_symptoms 
                                if (s.date - cycle.start_date).days < cycle.cycle_length]
    
    return {
        "events": events,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "patterns_detected": patterns,
        "correlations": []
    }


@router.get("/dashboard")
async def get_dashboard_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary with REAL-TIME health score calculation.
    Health score is based on actual user data, not just risk scores.
    """
    today = date.today()
    
    # Get current cycle info
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    current_cycle_day = None
    days_until_period = None
    current_phase = None
    
    if latest_cycle:
        current_cycle_day = (today - latest_cycle.start_date).days + 1
        
        # Calculate phase
        if current_cycle_day <= 5:
            current_phase = "menstrual"
        elif current_cycle_day <= 13:
            current_phase = "follicular"
        elif current_cycle_day <= 16:
            current_phase = "ovulation"
        else:
            current_phase = "luteal"
        
        if latest_cycle.predicted_next_start:
            days_until_period = (latest_cycle.predicted_next_start - today).days
    
    # Get all cycles and symptoms for health calculation
    all_cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).all()
    
    six_months_ago = today - timedelta(days=180)
    all_symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date >= six_months_ago
    ).all()
    
    # Get recent symptoms for display
    week_ago = today - timedelta(days=7)
    recent_symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.date >= week_ago
    ).order_by(desc(models.Symptom.date)).limit(5).all()
    
    # === CALCULATE REAL HEALTH SCORE ===
    health_factors = []
    health_score = 100.0  # Start at 100 and deduct based on factors
    
    # Factor 1: Cycle Regularity (max -20 points)
    if len(all_cycles) >= 3:
        cycle_lengths = [c.cycle_length for c in all_cycles if c.cycle_length]
        if cycle_lengths:
            std_length = np.std(cycle_lengths)
            avg_length = np.mean(cycle_lengths)
            
            # Very irregular = more deduction
            if std_length > 10:
                health_score -= 15
                health_factors.append("Very irregular cycles")
            elif std_length > 7:
                health_score -= 10
                health_factors.append("Moderately irregular cycles")
            elif std_length > 4:
                health_score -= 5
            
            # Abnormal cycle length
            if avg_length < 21 or avg_length > 35:
                health_score -= 10
                health_factors.append("Cycle length outside normal range")
    else:
        # Not enough data - small penalty
        health_score -= 5
    
    # Factor 2: Flow Level - CURRENT cycle has immediate impact
    # First check latest cycle's flow
    if latest_cycle and latest_cycle.flow_level:
        current_flow = latest_cycle.flow_level.lower()
        if current_flow == "very_heavy":
            health_score -= 12
            health_factors.append("Current cycle: Very heavy flow")
        elif current_flow == "heavy":
            health_score -= 8
            health_factors.append("Current cycle: Heavy flow")
        elif current_flow == "light":
            health_score += 3  # Light flow is a positive indicator
        elif current_flow == "spotting":
            health_score += 2
    
    # Also check historical pattern (additional penalty if consistent)
    heavy_cycles = [c for c in all_cycles if c.flow_level and c.flow_level.lower() in ["heavy", "very_heavy"]]
    if len(heavy_cycles) >= 3:
        heavy_ratio = len(heavy_cycles) / max(len(all_cycles), 1)
        if heavy_ratio > 0.5:
            health_score -= 5  # Additional penalty for consistent heavy periods
    
    # Factor 3: Symptom Severity (max -25 points)
    if all_symptoms:
        avg_severity = np.mean([s.severity for s in all_symptoms])
        symptom_count = len(all_symptoms)
        
        if avg_severity >= 7:
            health_score -= 20
            health_factors.append("High symptom severity")
        elif avg_severity >= 5:
            health_score -= 12
            health_factors.append("Moderate symptom severity")
        elif avg_severity >= 3:
            health_score -= 5
        
        # Frequent symptoms
        if symptom_count > 50:
            health_score -= 5
            health_factors.append("Frequent symptom logging")
    
    # Factor 4: Pain Symptoms (max -15 points)
    pain_symptoms = [s for s in all_symptoms if "pain" in s.symptom_type.lower() or s.symptom_type.lower() == "cramps"]
    if pain_symptoms:
        pain_avg = np.mean([s.severity for s in pain_symptoms])
        if pain_avg >= 7:
            health_score -= 15
            health_factors.append("Severe pain symptoms")
        elif pain_avg >= 5:
            health_score -= 8
    
    # Factor 5: Fatigue (max -10 points)
    fatigue_symptoms = [s for s in all_symptoms if "fatigue" in s.symptom_type.lower() or "tired" in s.symptom_type.lower()]
    if len(fatigue_symptoms) >= 5:
        health_score -= 10
        health_factors.append("Chronic fatigue")
    elif len(fatigue_symptoms) >= 3:
        health_score -= 5
    
    # Factor 6: Mood/Emotional Health (max -10 points)
    mood_symptoms = [s for s in all_symptoms if s.category == "emotional"]
    if len(mood_symptoms) >= 10:
        health_score -= 10
        health_factors.append("Frequent emotional symptoms")
    elif len(mood_symptoms) >= 5:
        health_score -= 5
    
    # Factor 7: Recent Mood Log Energy (bonus up to +5 points)
    recent_moods = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == current_user.id,
        models.MoodLog.date >= week_ago
    ).all()
    
    if recent_moods:
        avg_energy = np.mean([m.energy_level for m in recent_moods if m.energy_level])
        if avg_energy >= 4:
            health_score += 5  # Bonus for good energy
        elif avg_energy <= 2:
            health_score -= 5
            health_factors.append("Low energy levels")
    
    # Ensure score is within bounds
    health_score = max(0, min(100, health_score))
    
    # Get unread insights count
    unread_insights = db.query(models.HealthInsight).filter(
        models.HealthInsight.user_id == current_user.id,
        models.HealthInsight.is_read == False
    ).count()
    
    # Get pending recommendations
    pending_recommendations = db.query(models.Recommendation).filter(
        models.Recommendation.user_id == current_user.id,
        models.Recommendation.is_completed == False
    ).count()
    
    # Get current streak
    streak = db.query(models.HealthStreak).filter(
        models.HealthStreak.user_id == current_user.id,
        models.HealthStreak.streak_type == "logging"
    ).first()
    
    current_streak = streak.current_streak if streak else 0
    
    # Build risk summary from actual calculations
    pcos_result = calculate_pcos_risk(current_user, all_cycles, all_symptoms)
    endo_result = calculate_endometriosis_risk(all_symptoms, all_cycles)
    anemia_result = calculate_anemia_risk(all_symptoms, all_cycles)
    thyroid_result = calculate_thyroid_risk(current_user, all_symptoms, all_cycles)
    
    risk_summary = {
        "pcos": pcos_result["score"],
        "endometriosis": endo_result["score"],
        "anemia": anemia_result["score"],
        "thyroid": thyroid_result["score"]
    }
    
    return {
        "current_cycle_day": current_cycle_day,
        "days_until_next_period": days_until_period,
        "current_phase": current_phase,
        "recent_symptoms": [
            {
                "id": s.id,
                "symptom_type": s.symptom_type,
                "severity": s.severity,
                "date": s.date.isoformat(),
                "category": s.category
            }
            for s in recent_symptoms
        ],
        "risk_summary": risk_summary,
        "unread_insights": unread_insights,
        "pending_recommendations": pending_recommendations,
        "current_streak": current_streak,
        "health_score": round(health_score, 1),
        "health_factors": health_factors[:5]  # Top 5 factors affecting score
    }
