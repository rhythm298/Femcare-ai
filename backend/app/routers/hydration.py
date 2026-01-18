"""
Hydration and Sleep Tracker router for FemCare AI.
Provides water intake tracking with phase-based goals and sleep logging.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import get_db
from app import models
from app.security import get_current_user

router = APIRouter(prefix="/api/hydration", tags=["Hydration & Sleep"])


def get_current_cycle_phase(user_id: int, db: Session) -> str:
    """Get the current cycle phase for a user."""
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == user_id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if not latest_cycle:
        return "follicular"
    
    today = date.today()
    days_since_start = (today - latest_cycle.start_date).days
    
    if days_since_start <= 5:
        return "menstrual"
    elif days_since_start <= 13:
        return "follicular"
    elif days_since_start <= 16:
        return "ovulation"
    else:
        return "luteal"


def get_daily_goal(user_id: int, db: Session) -> int:
    """Get daily hydration goal with phase adjustment."""
    goal = db.query(models.DailyHydrationGoal).filter(
        models.DailyHydrationGoal.user_id == user_id
    ).first()
    
    base_goal = goal.daily_goal_ml if goal else 2500
    
    # Adjust for cycle phase
    if goal and goal.adjust_for_phase:
        phase = get_current_cycle_phase(user_id, db)
        if phase == "menstrual":
            base_goal = int(base_goal * (goal.menstrual_multiplier or 1.2))
    
    return base_goal


@router.post("/log")
async def log_water_intake(
    amount_ml: int = Query(..., ge=50, le=2000, description="Amount in ml"),
    drink_type: str = Query("water", regex="^(water|tea|coffee|juice|infused_water|other)$"),
    log_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log water intake.
    """
    water_log = models.WaterLog(
        user_id=current_user.id,
        date=log_date or date.today(),
        amount_ml=amount_ml,
        drink_type=drink_type,
        logged_at=datetime.now()
    )
    
    db.add(water_log)
    db.commit()
    db.refresh(water_log)
    
    # Get today's total
    today_total = db.query(func.sum(models.WaterLog.amount_ml)).filter(
        models.WaterLog.user_id == current_user.id,
        models.WaterLog.date == (log_date or date.today())
    ).scalar() or 0
    
    daily_goal = get_daily_goal(current_user.id, db)
    progress = (today_total / daily_goal) * 100
    
    # Encouragement messages
    messages = {
        25: "Great start! Keep sipping 💧",
        50: "Halfway there! You're doing great 💪",
        75: "Almost at your goal! 🎯",
        100: "🎉 Daily goal achieved! Stay hydrated!"
    }
    
    message = "Logged successfully!"
    for threshold, msg in sorted(messages.items()):
        if progress >= threshold:
            message = msg
    
    return {
        "id": water_log.id,
        "amount_ml": amount_ml,
        "drink_type": drink_type,
        "today_total_ml": today_total,
        "daily_goal_ml": daily_goal,
        "progress_percentage": round(progress, 1),
        "remaining_ml": max(0, daily_goal - today_total),
        "message": message
    }


@router.get("/today")
async def get_today_hydration(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get today's hydration summary.
    """
    today = date.today()
    
    logs = db.query(models.WaterLog).filter(
        models.WaterLog.user_id == current_user.id,
        models.WaterLog.date == today
    ).order_by(desc(models.WaterLog.logged_at)).all()
    
    total_ml = sum(log.amount_ml for log in logs)
    daily_goal = get_daily_goal(current_user.id, db)
    current_phase = get_current_cycle_phase(current_user.id, db)
    
    # Group by drink type
    by_type = {}
    for log in logs:
        by_type[log.drink_type] = by_type.get(log.drink_type, 0) + log.amount_ml
    
    # Calculate glasses (250ml each)
    glasses = total_ml / 250
    
    phase_tips = {
        "menstrual": "💧 During your period, aim for extra hydration to help with bloating and fatigue.",
        "follicular": "💧 Good hydration supports rising energy levels!",
        "ovulation": "💧 Stay hydrated for optimal energy and focus.",
        "luteal": "💧 Water helps reduce PMS symptoms like bloating."
    }
    
    return {
        "date": str(today),
        "current_phase": current_phase,
        "total_ml": total_ml,
        "daily_goal_ml": daily_goal,
        "progress_percentage": round((total_ml / daily_goal) * 100, 1),
        "remaining_ml": max(0, daily_goal - total_ml),
        "glasses": round(glasses, 1),
        "logs": [{
            "id": log.id,
            "amount_ml": log.amount_ml,
            "drink_type": log.drink_type,
            "logged_at": log.logged_at.isoformat() if log.logged_at else None
        } for log in logs],
        "by_type": by_type,
        "phase_tip": phase_tips.get(current_phase, ""),
        "goal_achieved": total_ml >= daily_goal
    }


@router.get("/history")
async def get_hydration_history(
    days: int = Query(7, ge=1, le=30),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get hydration history for past days.
    """
    start_date = date.today() - timedelta(days=days - 1)
    daily_goal = get_daily_goal(current_user.id, db)
    
    # Get all logs
    logs = db.query(models.WaterLog).filter(
        models.WaterLog.user_id == current_user.id,
        models.WaterLog.date >= start_date
    ).all()
    
    # Group by date
    daily_totals = {}
    for log in logs:
        day_str = str(log.date)
        daily_totals[day_str] = daily_totals.get(day_str, 0) + log.amount_ml
    
    # Build history with all days
    history = []
    current_date = start_date
    today = date.today()
    streak = 0
    temp_streak = 0
    
    while current_date <= today:
        day_str = str(current_date)
        total = daily_totals.get(day_str, 0)
        met_goal = total >= daily_goal
        
        history.append({
            "date": day_str,
            "total_ml": total,
            "goal_ml": daily_goal,
            "progress_percentage": round((total / daily_goal) * 100, 1) if daily_goal > 0 else 0,
            "met_goal": met_goal
        })
        
        if met_goal:
            temp_streak += 1
            streak = max(streak, temp_streak)
        else:
            temp_streak = 0
            
        current_date += timedelta(days=1)
    
    # Calculate averages
    total_values = [d["total_ml"] for d in history if d["total_ml"] > 0]
    avg_daily = sum(total_values) / len(total_values) if total_values else 0
    days_met_goal = sum(1 for d in history if d["met_goal"])
    
    return {
        "history": history,
        "summary": {
            "avg_daily_ml": round(avg_daily, 0),
            "days_tracked": len(total_values),
            "days_met_goal": days_met_goal,
            "current_streak": temp_streak,
            "best_streak": streak,
            "success_rate": round((days_met_goal / len(history)) * 100, 1) if history else 0
        }
    }


@router.get("/goal")
async def get_hydration_goal(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's hydration goal settings.
    """
    goal = db.query(models.DailyHydrationGoal).filter(
        models.DailyHydrationGoal.user_id == current_user.id
    ).first()
    
    current_phase = get_current_cycle_phase(current_user.id, db)
    
    if not goal:
        # Return defaults
        return {
            "daily_goal_ml": 2500,
            "reminder_enabled": True,
            "reminder_interval_hours": 2,
            "adjust_for_phase": True,
            "menstrual_multiplier": 1.2,
            "current_phase": current_phase,
            "effective_goal_ml": 3000 if current_phase == "menstrual" else 2500
        }
    
    effective_goal = goal.daily_goal_ml
    if goal.adjust_for_phase and current_phase == "menstrual":
        effective_goal = int(goal.daily_goal_ml * goal.menstrual_multiplier)
    
    return {
        "daily_goal_ml": goal.daily_goal_ml,
        "reminder_enabled": goal.reminder_enabled,
        "reminder_interval_hours": goal.reminder_interval_hours,
        "adjust_for_phase": goal.adjust_for_phase,
        "menstrual_multiplier": goal.menstrual_multiplier,
        "current_phase": current_phase,
        "effective_goal_ml": effective_goal
    }


@router.put("/goal")
async def update_hydration_goal(
    daily_goal_ml: int = Query(2500, ge=1000, le=5000),
    reminder_enabled: bool = True,
    reminder_interval_hours: int = Query(2, ge=1, le=6),
    adjust_for_phase: bool = True,
    menstrual_multiplier: float = Query(1.2, ge=1.0, le=2.0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update hydration goal settings.
    """
    goal = db.query(models.DailyHydrationGoal).filter(
        models.DailyHydrationGoal.user_id == current_user.id
    ).first()
    
    if not goal:
        goal = models.DailyHydrationGoal(user_id=current_user.id)
        db.add(goal)
    
    goal.daily_goal_ml = daily_goal_ml
    goal.reminder_enabled = reminder_enabled
    goal.reminder_interval_hours = reminder_interval_hours
    goal.adjust_for_phase = adjust_for_phase
    goal.menstrual_multiplier = menstrual_multiplier
    
    db.commit()
    db.refresh(goal)
    
    return {
        "daily_goal_ml": goal.daily_goal_ml,
        "reminder_enabled": goal.reminder_enabled,
        "message": "Hydration goal updated successfully"
    }


@router.delete("/log/{log_id}")
async def delete_water_log(
    log_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a water log entry.
    """
    log = db.query(models.WaterLog).filter(
        models.WaterLog.id == log_id,
        models.WaterLog.user_id == current_user.id
    ).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    db.delete(log)
    db.commit()
    
    return {"message": "Log deleted successfully"}


# ============== Sleep Tracking ==============

@router.post("/sleep")
async def log_sleep(
    duration_hours: float = Query(..., ge=0, le=24),
    quality_rating: int = Query(..., ge=1, le=5),
    bedtime: Optional[str] = None,
    wake_time: Optional[str] = None,
    had_cramps: bool = False,
    had_hot_flashes: bool = False,
    notes: Optional[str] = None,
    log_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log sleep data.
    """
    sleep_log = models.SleepLog(
        user_id=current_user.id,
        date=log_date or date.today(),
        duration_hours=duration_hours,
        quality_rating=quality_rating,
        had_cramps=had_cramps,
        had_hot_flashes=had_hot_flashes,
        notes=notes
    )
    
    if bedtime:
        try:
            sleep_log.bedtime = datetime.fromisoformat(bedtime)
        except:
            pass
    
    if wake_time:
        try:
            sleep_log.wake_time = datetime.fromisoformat(wake_time)
        except:
            pass
    
    db.add(sleep_log)
    db.commit()
    db.refresh(sleep_log)
    
    return {
        "id": sleep_log.id,
        "duration_hours": duration_hours,
        "quality_rating": quality_rating,
        "date": str(sleep_log.date),
        "message": "Sleep logged successfully"
    }


@router.get("/sleep/history")
async def get_sleep_history(
    days: int = Query(7, ge=1, le=30),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sleep history.
    """
    start_date = date.today() - timedelta(days=days - 1)
    
    logs = db.query(models.SleepLog).filter(
        models.SleepLog.user_id == current_user.id,
        models.SleepLog.date >= start_date
    ).order_by(desc(models.SleepLog.date)).all()
    
    if not logs:
        return {
            "history": [],
            "avg_duration": 0,
            "avg_quality": 0,
            "days_with_cramps": 0
        }
    
    avg_duration = sum(l.duration_hours or 0 for l in logs) / len(logs)
    avg_quality = sum(l.quality_rating or 0 for l in logs) / len(logs)
    days_with_cramps = sum(1 for l in logs if l.had_cramps)
    
    return {
        "history": [{
            "id": log.id,
            "date": str(log.date),
            "duration_hours": log.duration_hours,
            "quality_rating": log.quality_rating,
            "had_cramps": log.had_cramps,
            "had_hot_flashes": log.had_hot_flashes,
            "notes": log.notes
        } for log in logs],
        "avg_duration": round(avg_duration, 1),
        "avg_quality": round(avg_quality, 1),
        "days_with_cramps": days_with_cramps
    }
