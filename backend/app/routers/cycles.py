"""
Cycle tracking router for FemCare AI.
Handles menstrual cycle logging, predictions, and pattern analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta
from typing import List, Optional
import numpy as np

from app.database import get_db
from app import models, schemas
from app.security import get_current_user

router = APIRouter(prefix="/api/cycles", tags=["Cycle Tracking"])


def calculate_cycle_length(start_date: date, next_start_date: date) -> int:
    """Calculate the length of a cycle in days"""
    return (next_start_date - start_date).days


def predict_next_cycle(cycles: List[models.CycleEntry]) -> tuple[date, float]:
    """
    Predict the next cycle start date using weighted moving average.
    More recent cycles have higher weight.
    Returns (predicted_date, confidence)
    """
    if len(cycles) < 2:
        # Not enough data, use default 28 days
        if cycles:
            return cycles[0].start_date + timedelta(days=28), 0.3
        return date.today() + timedelta(days=28), 0.1
    
    # Get cycle lengths (we need at least 2 cycles to calculate lengths)
    cycle_lengths = []
    sorted_cycles = sorted(cycles, key=lambda c: c.start_date)
    
    for i in range(1, len(sorted_cycles)):
        length = calculate_cycle_length(sorted_cycles[i-1].start_date, sorted_cycles[i].start_date)
        if 15 <= length <= 60:  # Filter out unrealistic values
            cycle_lengths.append(length)
    
    if not cycle_lengths:
        return sorted_cycles[-1].start_date + timedelta(days=28), 0.3
    
    # Weighted average (more recent = higher weight)
    weights = np.array([i + 1 for i in range(len(cycle_lengths))])
    weights = weights / weights.sum()
    
    avg_length = np.average(cycle_lengths, weights=weights)
    std_length = np.std(cycle_lengths)
    
    # Confidence based on consistency and sample size
    consistency_score = max(0, 1 - (std_length / 10))  # Lower std = higher confidence
    sample_score = min(1, len(cycle_lengths) / 6)  # More samples = higher confidence
    confidence = (consistency_score * 0.6 + sample_score * 0.4)
    
    # Predict next date
    last_cycle = sorted_cycles[-1]
    predicted_date = last_cycle.start_date + timedelta(days=round(avg_length))
    
    return predicted_date, round(confidence, 2)


@router.post("/", response_model=schemas.CycleResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    cycle_data: schemas.CycleCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a new menstrual cycle entry.
    """
    # Calculate period length if end date provided
    period_length = None
    if cycle_data.end_date:
        period_length = (cycle_data.end_date - cycle_data.start_date).days + 1
    
    # Create the cycle entry
    new_cycle = models.CycleEntry(
        user_id=current_user.id,
        start_date=cycle_data.start_date,
        end_date=cycle_data.end_date,
        period_length=period_length,
        flow_level=cycle_data.flow_level.value,
        notes=cycle_data.notes
    )
    
    db.add(new_cycle)
    db.commit()
    
    # Update previous cycle's length if exists
    previous_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id,
        models.CycleEntry.start_date < cycle_data.start_date
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if previous_cycle:
        previous_cycle.cycle_length = calculate_cycle_length(
            previous_cycle.start_date, 
            cycle_data.start_date
        )
    
    # Calculate prediction for this cycle
    all_cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).all()
    
    predicted_date, confidence = predict_next_cycle(all_cycles)
    new_cycle.predicted_next_start = predicted_date
    new_cycle.prediction_confidence = confidence
    
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
        else:
            streak.current_streak = 1
        
        streak.last_activity_date = today
        streak.total_activities += 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    
    db.commit()
    db.refresh(new_cycle)
    
    return new_cycle


@router.get("/", response_model=List[schemas.CycleResponse])
async def get_cycles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all cycle entries for the current user.
    """
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).offset(skip).limit(limit).all()
    
    return cycles


@router.get("/current")
async def get_current_cycle(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get information about the current cycle.
    """
    # Get the most recent cycle
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if not latest_cycle:
        return {
            "has_data": False,
            "message": "No cycle data yet. Start tracking to get insights!"
        }
    
    today = date.today()
    cycle_day = (today - latest_cycle.start_date).days + 1
    
    # Determine current phase (assuming 28-day cycle as baseline)
    all_cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).all()
    
    # Calculate average cycle length
    cycle_lengths = [c.cycle_length for c in all_cycles if c.cycle_length]
    avg_cycle_length = np.mean(cycle_lengths) if cycle_lengths else 28
    
    # Determine phase
    if cycle_day <= 5:
        phase = "menstrual"
        phase_description = "Menstrual Phase - Your period"
    elif cycle_day <= 13:
        phase = "follicular"
        phase_description = "Follicular Phase - Energy typically increases"
    elif cycle_day <= 16:
        phase = "ovulation"
        phase_description = "Ovulation Phase - Peak fertility window"
    else:
        phase = "luteal"
        phase_description = "Luteal Phase - PMS symptoms may occur"
    
    # Days until next period
    if latest_cycle.predicted_next_start:
        days_until_period = (latest_cycle.predicted_next_start - today).days
    else:
        days_until_period = round(avg_cycle_length - cycle_day)
    
    # Fertile window estimation (around ovulation)
    ovulation_day = round(avg_cycle_length - 14)
    fertile_window_start = latest_cycle.start_date + timedelta(days=ovulation_day - 5)
    fertile_window_end = latest_cycle.start_date + timedelta(days=ovulation_day + 1)
    is_fertile_window = fertile_window_start <= today <= fertile_window_end
    
    return {
        "has_data": True,
        "cycle_day": cycle_day,
        "phase": phase,
        "phase_description": phase_description,
        "days_until_period": max(0, days_until_period),
        "predicted_next_start": latest_cycle.predicted_next_start,
        "prediction_confidence": latest_cycle.prediction_confidence,
        "average_cycle_length": round(avg_cycle_length, 1),
        "is_fertile_window": is_fertile_window,
        "fertile_window": {
            "start": fertile_window_start,
            "end": fertile_window_end
        } if not current_user.is_on_birth_control else None
    }


@router.get("/prediction", response_model=schemas.CyclePrediction)
async def get_cycle_prediction(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed cycle predictions.
    """
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).all()
    
    if len(cycles) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 2 cycles to make predictions"
        )
    
    predicted_date, confidence = predict_next_cycle(cycles)
    
    # Calculate averages
    cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
    period_lengths = [c.period_length for c in cycles if c.period_length]
    
    avg_cycle = np.mean(cycle_lengths) if cycle_lengths else 28
    avg_period = np.mean(period_lengths) if period_lengths else 5
    
    # Calculate ovulation and fertile window
    ovulation_day = round(avg_cycle - 14)
    ovulation_date = predicted_date - timedelta(days=round(avg_cycle - ovulation_day))
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date + timedelta(days=1)
    
    return {
        "next_period_start": predicted_date,
        "next_period_end": predicted_date + timedelta(days=round(avg_period)),
        "next_ovulation": ovulation_date if not current_user.is_on_birth_control else None,
        "fertile_window_start": fertile_start if not current_user.is_on_birth_control else None,
        "fertile_window_end": fertile_end if not current_user.is_on_birth_control else None,
        "confidence": confidence,
        "average_cycle_length": round(avg_cycle, 1),
        "average_period_length": round(avg_period, 1)
    }


@router.get("/fertility")
async def get_fertility_window(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive fertility tracking information including:
    - Current fertility status
    - Ovulation prediction
    - Detailed calendar with daily fertility levels
    - Conception probability per day
    """
    if current_user.is_on_birth_control:
        return {
            "enabled": False,
            "message": "Fertility tracking is disabled while on birth control. Update your profile to enable."
        }
    
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).all()
    
    if len(cycles) < 1:
        return {
            "enabled": True,
            "has_data": False,
            "message": "Log at least one cycle to get fertility predictions"
        }
    
    latest_cycle = cycles[0]
    today = date.today()
    cycle_day = (today - latest_cycle.start_date).days + 1
    
    # Calculate averages
    cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
    avg_cycle = np.mean(cycle_lengths) if cycle_lengths else 28
    
    # Ovulation typically occurs 14 days BEFORE next period
    ovulation_day = round(avg_cycle - 14)
    ovulation_date = latest_cycle.start_date + timedelta(days=ovulation_day)
    
    # Fertile window: 5 days before ovulation to 1 day after
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date + timedelta(days=1)
    
    # Determine current fertility status
    if today < fertile_start:
        days_to_fertile = (fertile_start - today).days
        status = "low"
        status_message = f"Low fertility - Fertile window starts in {days_to_fertile} days"
        status_emoji = "🔵"
    elif today <= fertile_end:
        if today == ovulation_date:
            status = "peak"
            status_message = "🎯 Peak Ovulation Day! Highest fertility"
            status_emoji = "🔴"
        elif today >= ovulation_date - timedelta(days=1):
            status = "high"
            status_message = "Very high fertility - Peak ovulation window"
            status_emoji = "🟠"
        else:
            status = "fertile"
            status_message = "Fertile window - Elevated chance of conception"
            status_emoji = "🟡"
    else:
        status = "low"
        days_since_ovulation = (today - ovulation_date).days
        status_message = f"Low fertility - {days_since_ovulation} days post-ovulation"
        status_emoji = "🔵"
    
    # Generate calendar data for next 35 days
    calendar_days = []
    for i in range(-7, 35):  # Past week + next 5 weeks
        day = latest_cycle.start_date + timedelta(days=cycle_day - 1 + i)
        day_of_cycle = (day - latest_cycle.start_date).days + 1
        
        # Determine fertility level for this day
        if day_of_cycle <= 0:
            fertility_level = "none"
            conception_chance = 0
        elif day_of_cycle <= 5:  # Menstrual phase
            fertility_level = "menstrual"
            conception_chance = 2
        elif day_of_cycle < ovulation_day - 5:  # Pre-fertile
            fertility_level = "low"
            conception_chance = 5
        elif day_of_cycle == ovulation_day - 5:
            fertility_level = "fertile_start"
            conception_chance = 10
        elif day_of_cycle == ovulation_day - 4:
            fertility_level = "fertile"
            conception_chance = 15
        elif day_of_cycle == ovulation_day - 3:
            fertility_level = "fertile"
            conception_chance = 20
        elif day_of_cycle == ovulation_day - 2:
            fertility_level = "high"
            conception_chance = 25
        elif day_of_cycle == ovulation_day - 1:
            fertility_level = "very_high"
            conception_chance = 30
        elif day_of_cycle == ovulation_day:
            fertility_level = "peak"
            conception_chance = 33
        elif day_of_cycle == ovulation_day + 1:
            fertility_level = "high"
            conception_chance = 15
        else:  # Post-ovulation
            fertility_level = "low"
            conception_chance = 2
        
        calendar_days.append({
            "date": day.isoformat(),
            "cycle_day": day_of_cycle if day_of_cycle > 0 else None,
            "fertility_level": fertility_level,
            "conception_chance": conception_chance,
            "is_today": day == today,
            "is_ovulation": day_of_cycle == ovulation_day,
            "is_period": day_of_cycle <= 5 if day_of_cycle > 0 else False
        })
    
    # PMS window (5 days before expected period)
    predicted_period = latest_cycle.predicted_next_start or (latest_cycle.start_date + timedelta(days=round(avg_cycle)))
    pms_start = predicted_period - timedelta(days=7)
    is_pms_window = pms_start <= today < predicted_period
    
    return {
        "enabled": True,
        "has_data": True,
        "today": {
            "date": today.isoformat(),
            "cycle_day": cycle_day,
            "status": status,
            "status_message": status_message,
            "status_emoji": status_emoji
        },
        "ovulation": {
            "predicted_date": ovulation_date.isoformat(),
            "cycle_day": ovulation_day,
            "days_until": (ovulation_date - today).days if ovulation_date >= today else None,
            "days_since": (today - ovulation_date).days if today > ovulation_date else None
        },
        "fertile_window": {
            "start": fertile_start.isoformat(),
            "end": fertile_end.isoformat(),
            "is_in_window": fertile_start <= today <= fertile_end,
            "days_in_window": 7
        },
        "next_period": {
            "predicted_date": predicted_period.isoformat(),
            "days_until": (predicted_period - today).days
        },
        "pms": {
            "is_pms_window": is_pms_window,
            "pms_start": pms_start.isoformat()
        },
        "calendar": calendar_days,
        "insights": {
            "avg_cycle_length": round(avg_cycle, 1),
            "ovulation_day": ovulation_day,
            "fertile_window_days": 7,
            "best_conception_days": [
                (ovulation_date - timedelta(days=1)).isoformat(),
                ovulation_date.isoformat()
            ]
        }
    }


@router.get("/patterns", response_model=schemas.CyclePatterns)
async def get_cycle_patterns(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed cycle pattern analysis.
    """
    cycles = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(models.CycleEntry.start_date).all()
    
    if not cycles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No cycle data available"
        )
    
    # Calculate statistics
    cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
    period_lengths = [c.period_length for c in cycles if c.period_length]
    
    avg_cycle = np.mean(cycle_lengths) if cycle_lengths else 28
    std_cycle = np.std(cycle_lengths) if len(cycle_lengths) > 1 else 0
    avg_period = np.mean(period_lengths) if period_lengths else 5
    
    # Regularity score (inverse of coefficient of variation)
    if avg_cycle > 0 and std_cycle >= 0:
        cv = std_cycle / avg_cycle
        regularity_score = max(0, min(1, 1 - cv))
    else:
        regularity_score = 0.5
    
    # Is regular if std < 7 and all cycles between 21-35 days
    is_regular = std_cycle < 7 and all(21 <= l <= 35 for l in cycle_lengths) if cycle_lengths else False
    
    # Get common symptoms
    symptoms = db.query(models.Symptom).filter(
        models.Symptom.user_id == current_user.id
    ).all()
    
    symptom_counts = {}
    for symptom in symptoms:
        key = symptom.symptom_type
        if key in symptom_counts:
            symptom_counts[key]["count"] += 1
            symptom_counts[key]["total_severity"] += symptom.severity
        else:
            symptom_counts[key] = {"count": 1, "total_severity": symptom.severity}
    
    common_symptoms = [
        {
            "symptom": k,
            "count": v["count"],
            "avg_severity": round(v["total_severity"] / v["count"], 1)
        }
        for k, v in sorted(symptom_counts.items(), key=lambda x: -x[1]["count"])[:5]
    ]
    
    return {
        "average_cycle_length": round(avg_cycle, 1),
        "cycle_length_std": round(std_cycle, 1),
        "average_period_length": round(avg_period, 1),
        "is_regular": is_regular,
        "regularity_score": round(regularity_score, 2),
        "total_cycles_tracked": len(cycles),
        "longest_cycle": max(cycle_lengths) if cycle_lengths else 0,
        "shortest_cycle": min(cycle_lengths) if cycle_lengths else 0,
        "common_symptoms": common_symptoms,
        "cycle_phase_patterns": {
            "menstrual": {"typical_days": "1-5"},
            "follicular": {"typical_days": "6-13"},
            "ovulation": {"typical_days": "14-16"},
            "luteal": {"typical_days": "17-28"}
        }
    }


@router.put("/{cycle_id}", response_model=schemas.CycleResponse)
async def update_cycle(
    cycle_id: int,
    update_data: schemas.CycleUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a cycle entry.
    """
    cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.id == cycle_id,
        models.CycleEntry.user_id == current_user.id
    ).first()
    
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        if field == "flow_level" and value:
            setattr(cycle, field, value.value)
        else:
            setattr(cycle, field, value)
    
    # Recalculate period length if end_date updated
    if cycle.end_date and cycle.start_date:
        cycle.period_length = (cycle.end_date - cycle.start_date).days + 1
    
    db.commit()
    db.refresh(cycle)
    
    return cycle


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(
    cycle_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a cycle entry.
    """
    cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.id == cycle_id,
        models.CycleEntry.user_id == current_user.id
    ).first()
    
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    db.delete(cycle)
    db.commit()
    
    return None
