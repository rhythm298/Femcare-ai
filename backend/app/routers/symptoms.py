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


@router.get("/pms-prediction")
async def get_pms_prediction(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Predict upcoming PMS symptoms based on historical patterns.
    Analyzes what symptoms occurred at similar cycle days in previous cycles.
    """
    # Get user's cycle history
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).all()
    
    if len(cycles) < 1:
        return {
            "has_predictions": False,
            "message": "Log at least one cycle to get PMS predictions"
        }
    
    latest_cycle = cycles[0]
    today = date.today()
    current_cycle_day = (today - latest_cycle.start_date).days + 1
    
    # Calculate average cycle length
    cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
    avg_cycle = int(np.mean(cycle_lengths)) if cycle_lengths else 28
    
    # Get all symptoms for this user
    all_symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id
    ).all()
    
    if not all_symptoms:
        return {
            "has_predictions": False,
            "message": "Log symptoms to get personalized PMS predictions"
        }
    
    # Map symptoms to cycle days
    symptom_by_cycle_day = {}
    for symptom in all_symptoms:
        # Find which cycle this symptom belongs to
        for cycle in cycles:
            cycle_end = cycle.start_date + timedelta(days=cycle.cycle_length or avg_cycle)
            if cycle.start_date <= symptom.date < cycle_end:
                cycle_day = (symptom.date - cycle.start_date).days + 1
                if cycle_day not in symptom_by_cycle_day:
                    symptom_by_cycle_day[cycle_day] = []
                symptom_by_cycle_day[cycle_day].append({
                    "type": symptom.symptom_type,
                    "severity": symptom.severity,
                    "category": symptom.category
                })
                break
    
    # Analyze patterns for upcoming days (next 7 days)
    predictions = []
    for days_ahead in range(1, 8):
        future_cycle_day = current_cycle_day + days_ahead
        future_date = today + timedelta(days=days_ahead)
        
        # Handle cycle wrap-around
        if future_cycle_day > avg_cycle:
            future_cycle_day = future_cycle_day - avg_cycle
        
        # Get symptoms that occurred on this cycle day in history
        historical_symptoms = symptom_by_cycle_day.get(future_cycle_day, [])
        
        if historical_symptoms:
            # Group by symptom type and calculate frequency/avg severity
            symptom_stats = {}
            for sym in historical_symptoms:
                key = sym["type"]
                if key not in symptom_stats:
                    symptom_stats[key] = {"count": 0, "total_severity": 0, "category": sym["category"]}
                symptom_stats[key]["count"] += 1
                symptom_stats[key]["total_severity"] += sym["severity"]
            
            # Calculate likelihood and average severity
            predicted_symptoms = []
            for sym_type, stats in sorted(symptom_stats.items(), key=lambda x: -x[1]["count"]):
                likelihood = min(100, round((stats["count"] / len(cycles)) * 100))
                avg_severity = round(stats["total_severity"] / stats["count"], 1)
                
                if likelihood >= 20:  # Only show if happened at least 20% of the time
                    predicted_symptoms.append({
                        "symptom": sym_type,
                        "likelihood": likelihood,
                        "avg_severity": avg_severity,
                        "category": stats["category"]
                    })
            
            if predicted_symptoms:
                predictions.append({
                    "date": future_date.isoformat(),
                    "days_ahead": days_ahead,
                    "cycle_day": future_cycle_day,
                    "predicted_symptoms": predicted_symptoms[:5]  # Top 5 most likely
                })
    
    # Determine PMS phase
    days_until_period = avg_cycle - current_cycle_day
    is_pms_phase = 0 <= days_until_period <= 7
    pms_phase_message = ""
    
    if is_pms_phase:
        pms_phase_message = f"You're in the PMS phase. Period expected in {days_until_period} days."
    elif days_until_period < 0:
        pms_phase_message = "Your period may have started or is late."
    else:
        pms_phase_message = f"PMS phase starts in about {days_until_period - 7} days."
    
    # Generate proactive recommendations based on predictions
    recommendations = []
    all_predicted = []
    for pred in predictions:
        for sym in pred["predicted_symptoms"]:
            all_predicted.append(sym["symptom"])
    
    if "cramps" in all_predicted:
        recommendations.append({
            "emoji": "🔥",
            "tip": "Get a heating pad ready - cramps are likely coming"
        })
    if "headache" in all_predicted:
        recommendations.append({
            "emoji": "💧",
            "tip": "Stay extra hydrated to help prevent headaches"
        })
    if "mood_swings" in all_predicted:
        recommendations.append({
            "emoji": "🧘",
            "tip": "Schedule some self-care time for emotional balance"
        })
    if "fatigue" in all_predicted:
        recommendations.append({
            "emoji": "😴",
            "tip": "Plan for extra rest - fatigue is predicted"
        })
    if "bloating" in all_predicted:
        recommendations.append({
            "emoji": "🥗",
            "tip": "Reduce salt intake to minimize bloating"
        })
    if "acne" in all_predicted:
        recommendations.append({
            "emoji": "✨",
            "tip": "Start your skin care routine early"
        })
    
    return {
        "has_predictions": len(predictions) > 0,
        "current_cycle_day": current_cycle_day,
        "avg_cycle_length": avg_cycle,
        "days_until_period": max(0, days_until_period),
        "is_pms_phase": is_pms_phase,
        "pms_phase_message": pms_phase_message,
        "predictions": predictions,
        "proactive_recommendations": recommendations[:5],
        "data_quality": {
            "cycles_analyzed": len(cycles),
            "symptoms_analyzed": len(all_symptoms),
            "confidence": "high" if len(cycles) >= 6 else "medium" if len(cycles) >= 3 else "low"
        }
    }


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


@router.get("/guidance/{symptom_type}")
async def get_symptom_guidance(
    symptom_type: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive guidance for a specific symptom including:
    - What to do (recommendations)
    - What NOT to do (things to avoid)
    - Home remedies
    - When to see a doctor
    """
    symptom_lower = symptom_type.lower().replace(" ", "_")
    
    # Comprehensive symptom guidance database
    guidance_db = {
        "cramps": {
            "name": "Menstrual Cramps",
            "emoji": "😣",
            "description": "Painful muscle contractions in the lower abdomen during menstruation",
            "do": [
                "Apply a heating pad to your lower abdomen",
                "Take a warm bath or shower",
                "Do light stretching or yoga",
                "Stay hydrated with warm water or herbal tea",
                "Try over-the-counter pain relievers (ibuprofen/naproxen)",
                "Gentle massage with essential oils (lavender, clary sage)",
                "Get adequate rest and sleep"
            ],
            "dont": [
                "Don't consume excessive caffeine",
                "Avoid cold drinks and ice cream",
                "Don't skip meals or eat irregularly",
                "Avoid high-salt foods that cause bloating",
                "Don't do intense exercise if pain is severe",
                "Avoid stress and tension",
                "Don't ignore severe or unusual pain"
            ],
            "remedies": [
                {"name": "Ginger Tea", "how": "Boil fresh ginger in water for 10 mins, add honey"},
                {"name": "Chamomile Tea", "how": "Steep chamomile flowers in hot water for 5 mins"},
                {"name": "Heating Pad", "how": "Apply to lower abdomen for 15-20 mins"},
                {"name": "Child's Pose", "how": "Yoga pose - kneel and stretch arms forward, relax"}
            ],
            "see_doctor": [
                "Pain doesn't improve with OTC medication",
                "Cramps last longer than 2-3 days",
                "Heavy bleeding with large clots",
                "Pain during non-menstrual days",
                "Fever or nausea with cramps"
            ]
        },
        "headache": {
            "name": "Headache",
            "emoji": "🤕",
            "description": "Pain in the head that can be related to hormonal changes",
            "do": [
                "Rest in a quiet, dark room",
                "Stay well hydrated",
                "Apply cold compress to forehead",
                "Practice deep breathing exercises",
                "Take OTC pain relievers if needed",
                "Get adequate sleep",
                "Try gentle neck stretches"
            ],
            "dont": [
                "Don't stare at screens for long periods",
                "Avoid loud noises and bright lights",
                "Don't skip meals",
                "Avoid excessive caffeine or sudden withdrawal",
                "Don't consume too much sugar",
                "Avoid alcohol",
                "Don't ignore persistent headaches"
            ],
            "remedies": [
                {"name": "Peppermint Oil", "how": "Apply diluted oil to temples"},
                {"name": "Cold Compress", "how": "Apply ice pack wrapped in cloth for 15 mins"},
                {"name": "Hydration", "how": "Drink a full glass of water immediately"},
                {"name": "Pressure Points", "how": "Press between thumb and index finger for 5 mins"}
            ],
            "see_doctor": [
                "Sudden, severe headache (worst ever)",
                "Headache with fever, stiff neck, or confusion",
                "Headaches that wake you from sleep",
                "Headache after head injury",
                "Persistent headaches that don't respond to treatment"
            ]
        },
        "bloating": {
            "name": "Bloating",
            "emoji": "😤",
            "description": "Feeling of fullness or swelling in the abdomen",
            "do": [
                "Eat smaller, more frequent meals",
                "Walk after eating to aid digestion",
                "Drink peppermint or fennel tea",
                "Eat slowly and chew food thoroughly",
                "Include probiotics in your diet",
                "Stay active with light exercise",
                "Wear comfortable, loose clothing"
            ],
            "dont": [
                "Avoid carbonated drinks and sodas",
                "Don't eat too quickly",
                "Avoid chewing gum (causes air swallowing)",
                "Don't consume excessive salt",
                "Avoid artificial sweeteners",
                "Don't lie down immediately after eating",
                "Avoid beans and cruciferous vegetables during flare-ups"
            ],
            "remedies": [
                {"name": "Peppermint Tea", "how": "Steep peppermint leaves in hot water for 5 mins"},
                {"name": "Fennel Seeds", "how": "Chew a teaspoon of fennel seeds after meals"},
                {"name": "Ginger", "how": "Add fresh ginger to tea or meals"},
                {"name": "Abdominal Massage", "how": "Gentle clockwise massage around navel"}
            ],
            "see_doctor": [
                "Bloating with severe abdominal pain",
                "Blood in stool",
                "Unexplained weight loss with bloating",
                "Persistent bloating for more than 2 weeks",
                "Bloating with vomiting"
            ]
        },
        "fatigue": {
            "name": "Fatigue",
            "emoji": "😴",
            "description": "Extreme tiredness and lack of energy",
            "do": [
                "Get 7-9 hours of quality sleep",
                "Take short power naps (20 mins max)",
                "Eat iron-rich foods (spinach, beans, red meat)",
                "Stay hydrated throughout the day",
                "Do light exercise like walking",
                "Expose yourself to natural sunlight",
                "Eat balanced meals with protein and complex carbs"
            ],
            "dont": [
                "Don't rely on caffeine as a fix",
                "Avoid heavy meals before bed",
                "Don't use screens before sleep",
                "Avoid alcohol before bed",
                "Don't oversleep on weekends",
                "Avoid excessive sugar intake",
                "Don't skip breakfast"
            ],
            "remedies": [
                {"name": "Iron-Rich Snack", "how": "Eat dates, raisins, or dark chocolate"},
                {"name": "Power Nap", "how": "20-minute nap between 1-3 PM"},
                {"name": "Vitamin C", "how": "Have citrus fruits to help iron absorption"},
                {"name": "Sunlight Exposure", "how": "Spend 15-20 mins in morning sunlight"}
            ],
            "see_doctor": [
                "Fatigue lasting more than 2 weeks without improvement",
                "Fatigue with shortness of breath",
                "Unexplained weight changes with fatigue",
                "Fatigue with pale skin (possible anemia)",
                "Depression or anxiety with fatigue"
            ]
        },
        "mood_swings": {
            "name": "Mood Swings",
            "emoji": "😢",
            "description": "Sudden changes in emotional state related to hormonal fluctuations",
            "do": [
                "Practice deep breathing exercises",
                "Journal your feelings",
                "Exercise regularly (releases endorphins)",
                "Get adequate sleep",
                "Spend time outdoors in nature",
                "Talk to a trusted friend or family member",
                "Practice mindfulness or meditation"
            ],
            "dont": [
                "Don't bottle up your emotions",
                "Avoid excessive caffeine and sugar",
                "Don't make major decisions during mood episodes",
                "Avoid isolation - stay connected",
                "Don't blame yourself for your feelings",
                "Avoid alcohol as a coping mechanism",
                "Don't skip meals"
            ],
            "remedies": [
                {"name": "Box Breathing", "how": "Breathe in 4s, hold 4s, out 4s, hold 4s"},
                {"name": "Journaling", "how": "Write down 3 things you're grateful for"},
                {"name": "Walk Outside", "how": "15-minute walk in fresh air"},
                {"name": "Dark Chocolate", "how": "Small piece of dark chocolate for mood boost"}
            ],
            "see_doctor": [
                "Mood swings severely affecting daily life",
                "Thoughts of self-harm",
                "Mood changes not related to menstrual cycle",
                "Persistent depression lasting 2+ weeks",
                "Anxiety that interferes with work/relationships"
            ]
        },
        "back_pain": {
            "name": "Back Pain",
            "emoji": "😖",
            "description": "Lower back pain often associated with menstruation",
            "do": [
                "Apply heat to the affected area",
                "Do gentle stretching exercises",
                "Maintain good posture",
                "Sleep with a pillow between your knees",
                "Take OTC pain relievers if needed",
                "Try gentle yoga poses like cat-cow",
                "Stay moderately active"
            ],
            "dont": [
                "Don't sit or stand for too long",
                "Avoid heavy lifting",
                "Don't slouch or hunch",
                "Avoid high heels if pain is severe",
                "Don't sleep on your stomach",
                "Avoid sudden twisting movements",
                "Don't stay in bed all day"
            ],
            "remedies": [
                {"name": "Cat-Cow Stretch", "how": "Alternate arching and rounding back on hands and knees"},
                {"name": "Heat Therapy", "how": "Apply heating pad for 15-20 mins"},
                {"name": "Child's Pose", "how": "Kneel and reach arms forward, rest forehead on floor"},
                {"name": "Epsom Salt Bath", "how": "Add 2 cups to warm bath, soak for 20 mins"}
            ],
            "see_doctor": [
                "Back pain with numbness in legs",
                "Pain that doesn't improve after a week",
                "Back pain with fever",
                "Pain after an injury",
                "Difficulty controlling bladder or bowels"
            ]
        },
        "nausea": {
            "name": "Nausea",
            "emoji": "🤢",
            "description": "Feeling of sickness with an urge to vomit",
            "do": [
                "Eat small, bland meals",
                "Stay hydrated with clear fluids",
                "Get fresh air",
                "Try ginger in any form (tea, candy, fresh)",
                "Rest in a seated position, not lying flat",
                "Eat crackers or dry toast",
                "Use acupressure wristbands"
            ],
            "dont": [
                "Don't eat large, heavy meals",
                "Avoid greasy, spicy, or fried foods",
                "Don't lie down immediately after eating",
                "Avoid strong odors",
                "Don't skip eating entirely",
                "Avoid caffeine and alcohol",
                "Don't brush teeth right after eating"
            ],
            "remedies": [
                {"name": "Ginger Tea", "how": "Fresh ginger slices in hot water with honey"},
                {"name": "Peppermint", "how": "Smell peppermint oil or drink peppermint tea"},
                {"name": "Lemon Water", "how": "Squeeze fresh lemon in cool water"},
                {"name": "Acupressure", "how": "Press P6 point 3 finger widths from wrist"}
            ],
            "see_doctor": [
                "Nausea with severe abdominal pain",
                "Blood in vomit",
                "Signs of dehydration",
                "Nausea lasting more than 48 hours",
                "Nausea with high fever"
            ]
        },
        "breast_tenderness": {
            "name": "Breast Tenderness",
            "emoji": "💜",
            "description": "Soreness or sensitivity in the breasts before or during periods",
            "do": [
                "Wear a well-fitted, supportive bra",
                "Apply cold or warm compresses",
                "Reduce caffeine intake",
                "Take evening primrose oil supplements",
                "Wear a sports bra during sleep if needed",
                "Massage gently with evening primrose oil",
                "Consider vitamin E supplements"
            ],
            "dont": [
                "Don't wear underwire bras if uncomfortable",
                "Avoid high-sodium foods",
                "Don't consume excessive caffeine",
                "Avoid running or high-impact exercise without support",
                "Don't ignore unusual lumps",
                "Avoid sleeping on your stomach",
                "Don't dismiss persistent changes"
            ],
            "remedies": [
                {"name": "Cold Compress", "how": "Apply ice pack wrapped in cloth for 10 mins"},
                {"name": "Magnesium Foods", "how": "Eat nuts, seeds, dark leafy greens"},
                {"name": "Cabbage Leaves", "how": "Place cold cabbage leaves inside bra (folk remedy)"},
                {"name": "Flaxseed", "how": "Add 1 tbsp ground flaxseed to breakfast"}
            ],
            "see_doctor": [
                "New or unusual lumps",
                "Nipple discharge (not breastfeeding)",
                "Changes in breast shape or skin",
                "Persistent pain not related to cycle",
                "Pain on one side only"
            ]
        }
    }
    
    # Get guidance for the symptom
    guidance = guidance_db.get(symptom_lower)
    
    if not guidance:
        # Generic guidance for unknown symptoms
        guidance = {
            "name": symptom_type.replace("_", " ").title(),
            "emoji": "📋",
            "description": f"Symptom: {symptom_type.replace('_', ' ').title()}",
            "do": [
                "Rest and relaxation",
                "Stay hydrated",
                "Track the symptom for patterns",
                "Maintain a balanced diet",
                "Get adequate sleep"
            ],
            "dont": [
                "Don't ignore persistent symptoms",
                "Avoid excessive stress",
                "Don't skip meals",
                "Avoid overexertion"
            ],
            "remedies": [
                {"name": "General Rest", "how": "Take breaks throughout the day"},
                {"name": "Hydration", "how": "Drink 8 glasses of water daily"}
            ],
            "see_doctor": [
                "Symptoms persist for more than a week",
                "Symptoms are severe or worsening",
                "Symptoms interfere with daily activities"
            ]
        }
    
    # Add user's history with this symptom
    user_symptom_count = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.symptom_type.ilike(f"%{symptom_type}%")
    ).count()
    
    avg_severity = db.query(func.avg(models.Symptom.severity)).filter(
        models.Symptom.user_id == current_user.id,
        models.Symptom.symptom_type.ilike(f"%{symptom_type}%")
    ).scalar() or 0
    
    guidance["user_history"] = {
        "times_logged": user_symptom_count,
        "average_severity": round(float(avg_severity), 1) if avg_severity else 0
    }
    
    return guidance


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
