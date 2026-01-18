"""
Mood Journal router for FemCare AI.
Enhanced mood tracking with prompts, triggers, insights, and cycle correlation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, timedelta
from typing import List, Optional
import numpy as np

from app.database import get_db
from app import models
from app.security import get_current_user

router = APIRouter(prefix="/api/mood", tags=["Mood Journal"])


# Mood options with emojis
MOOD_OPTIONS = [
    {"mood": "happy", "emoji": "😊", "energy": "high"},
    {"mood": "calm", "emoji": "😌", "energy": "medium"},
    {"mood": "energetic", "emoji": "⚡", "energy": "high"},
    {"mood": "tired", "emoji": "😴", "energy": "low"},
    {"mood": "anxious", "emoji": "😰", "energy": "high"},
    {"mood": "sad", "emoji": "😢", "energy": "low"},
    {"mood": "irritated", "emoji": "😤", "energy": "medium"},
    {"mood": "grateful", "emoji": "🙏", "energy": "medium"},
    {"mood": "excited", "emoji": "🤩", "energy": "high"},
    {"mood": "stressed", "emoji": "😓", "energy": "high"},
    {"mood": "peaceful", "emoji": "☮️", "energy": "low"},
    {"mood": "hopeful", "emoji": "🌟", "energy": "medium"},
]

# Common triggers
COMMON_TRIGGERS = [
    {"id": "work", "label": "Work/Study", "emoji": "💼"},
    {"id": "relationship", "label": "Relationship", "emoji": "❤️"},
    {"id": "family", "label": "Family", "emoji": "👨‍👩‍👧"},
    {"id": "health", "label": "Health", "emoji": "🏥"},
    {"id": "sleep", "label": "Sleep Quality", "emoji": "😴"},
    {"id": "exercise", "label": "Exercise", "emoji": "🏃‍♀️"},
    {"id": "food", "label": "Diet/Food", "emoji": "🍎"},
    {"id": "period", "label": "Period/Cycle", "emoji": "🌸"},
    {"id": "weather", "label": "Weather", "emoji": "🌤️"},
    {"id": "social", "label": "Social Life", "emoji": "👥"},
    {"id": "money", "label": "Finances", "emoji": "💰"},
    {"id": "achievement", "label": "Achievement", "emoji": "🏆"},
]

# Journal prompts
JOURNAL_PROMPTS = [
    "What made you smile today?",
    "What are you grateful for right now?",
    "What's one small win you had today?",
    "How is your body feeling?",
    "What's on your mind?",
    "What would make today better?",
    "Who made a positive impact on your day?",
    "What are you looking forward to?",
    "What's something you did well today?",
    "How did you practice self-care today?",
]


@router.get("/options")
async def get_mood_options():
    """Get all mood options with emojis and triggers for the UI."""
    import random
    return {
        "moods": MOOD_OPTIONS,
        "triggers": COMMON_TRIGGERS,
        "daily_prompt": random.choice(JOURNAL_PROMPTS)
    }


@router.post("/log")
async def log_mood(
    mood: str = Query(..., description="Mood type (happy, sad, anxious, etc.)"),
    energy_level: int = Query(3, ge=1, le=5, description="Energy level 1-5"),
    notes: Optional[str] = Query(None, description="Journal notes"),
    triggers: Optional[str] = Query(None, description="Comma-separated trigger IDs"),
    gratitude: Optional[str] = Query(None, description="What are you grateful for?"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a mood entry with optional triggers and journal notes.
    """
    # Find emoji for mood
    mood_info = next((m for m in MOOD_OPTIONS if m["mood"] == mood.lower()), None)
    emoji = mood_info["emoji"] if mood_info else "😐"
    
    # Build notes with gratitude if provided
    full_notes = notes or ""
    if gratitude:
        full_notes = f"Grateful for: {gratitude}\n\n{full_notes}" if full_notes else f"Grateful for: {gratitude}"
    if triggers:
        full_notes = f"Triggers: {triggers}\n\n{full_notes}" if full_notes else f"Triggers: {triggers}"
    
    # Create mood log
    mood_log = models.MoodLog(
        user_id=current_user.id,
        date=date.today(),
        mood=mood.lower(),
        mood_emoji=emoji,
        energy_level=energy_level,
        notes=full_notes if full_notes else None
    )
    
    db.add(mood_log)
    db.commit()
    db.refresh(mood_log)
    
    return {
        "success": True,
        "id": mood_log.id,
        "mood": mood_log.mood,
        "emoji": emoji,
        "energy_level": energy_level,
        "message": "Mood logged successfully! 💜"
    }


@router.get("/today")
async def get_today_mood(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's mood entries."""
    today = date.today()
    moods = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == current_user.id,
        models.MoodLog.date == today
    ).order_by(desc(models.MoodLog.created_at)).all()
    
    return {
        "date": today.isoformat(),
        "entries": [
            {
                "id": m.id,
                "mood": m.mood,
                "emoji": m.mood_emoji,
                "energy_level": m.energy_level,
                "notes": m.notes,
                "logged_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in moods
        ],
        "has_logged_today": len(moods) > 0
    }


@router.get("/history")
async def get_mood_history(
    days: int = Query(30, ge=7, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mood history with daily summaries."""
    start_date = date.today() - timedelta(days=days)
    
    moods = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == current_user.id,
        models.MoodLog.date >= start_date
    ).order_by(desc(models.MoodLog.date)).all()
    
    # Group by date
    by_date = {}
    for m in moods:
        d = m.date.isoformat()
        if d not in by_date:
            by_date[d] = []
        by_date[d].append({
            "id": m.id,
            "mood": m.mood,
            "emoji": m.mood_emoji,
            "energy_level": m.energy_level,
            "notes": m.notes
        })
    
    return {
        "period_days": days,
        "total_entries": len(moods),
        "entries_by_date": by_date,
        "days_logged": len(by_date)
    }


@router.get("/insights")
async def get_mood_insights(
    days: int = Query(30, ge=7, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive mood insights including:
    - Mood distribution
    - Energy patterns
    - Cycle correlation
    - Trigger analysis
    - Trends over time
    """
    start_date = date.today() - timedelta(days=days)
    
    moods = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == current_user.id,
        models.MoodLog.date >= start_date
    ).all()
    
    if len(moods) < 3:
        return {
            "has_insights": False,
            "message": "Log more moods to get insights! Need at least 3 entries.",
            "entries_count": len(moods)
        }
    
    # Mood distribution
    mood_counts = {}
    energy_levels = []
    for m in moods:
        mood_counts[m.mood] = mood_counts.get(m.mood, 0) + 1
        if m.energy_level:
            energy_levels.append(m.energy_level)
    
    total = len(moods)
    mood_distribution = [
        {"mood": k, "count": v, "percentage": round((v/total)*100, 1)}
        for k, v in sorted(mood_counts.items(), key=lambda x: -x[1])
    ]
    
    # Add emoji to distribution
    for item in mood_distribution:
        mood_info = next((m for m in MOOD_OPTIONS if m["mood"] == item["mood"]), None)
        item["emoji"] = mood_info["emoji"] if mood_info else "😐"
    
    # Energy analysis
    avg_energy = np.mean(energy_levels) if energy_levels else 3
    
    # Most common mood
    most_common = mood_distribution[0]["mood"] if mood_distribution else "unknown"
    most_common_emoji = mood_distribution[0]["emoji"] if mood_distribution else "😐"
    
    # Trigger analysis (from notes)
    trigger_counts = {}
    for m in moods:
        if m.notes and "Triggers:" in m.notes:
            trigger_line = m.notes.split("Triggers:")[1].split("\n")[0]
            triggers = [t.strip() for t in trigger_line.split(",")]
            for t in triggers:
                trigger_counts[t] = trigger_counts.get(t, 0) + 1
    
    top_triggers = [
        {"trigger": k, "count": v}
        for k, v in sorted(trigger_counts.items(), key=lambda x: -x[1])[:5]
    ]
    
    # Cycle correlation
    cycle_correlation = None
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == current_user.id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if latest_cycle:
        # Group moods by cycle phase
        phase_moods = {"menstrual": [], "follicular": [], "ovulation": [], "luteal": []}
        cycle_lengths = db.query(models.CycleEntry.cycle_length).filter(
            models.CycleEntry.user_id == current_user.id,
            models.CycleEntry.cycle_length.isnot(None)
        ).all()
        avg_cycle = np.mean([c[0] for c in cycle_lengths]) if cycle_lengths else 28
        
        for m in moods:
            # Find which cycle this mood belongs to
            cycles = db.query(models.CycleEntry).filter(
                models.CycleEntry.user_id == current_user.id,
                models.CycleEntry.start_date <= m.date
            ).order_by(desc(models.CycleEntry.start_date)).first()
            
            if cycles:
                cycle_day = (m.date - cycles.start_date).days + 1
                if cycle_day <= 5:
                    phase = "menstrual"
                elif cycle_day <= 13:
                    phase = "follicular"
                elif cycle_day <= 16:
                    phase = "ovulation"
                else:
                    phase = "luteal"
                
                phase_moods[phase].append({
                    "mood": m.mood,
                    "energy": m.energy_level or 3
                })
        
        # Calculate average energy per phase
        cycle_correlation = {}
        for phase, entries in phase_moods.items():
            if entries:
                energies = [e["energy"] for e in entries]
                moods_in_phase = [e["mood"] for e in entries]
                most_common_in_phase = max(set(moods_in_phase), key=moods_in_phase.count) if moods_in_phase else "unknown"
                cycle_correlation[phase] = {
                    "avg_energy": round(np.mean(energies), 1),
                    "entries": len(entries),
                    "dominant_mood": most_common_in_phase
                }
    
    # Weekly trend
    weekly_data = []
    for i in range(min(4, days // 7)):
        week_start = date.today() - timedelta(days=(i+1)*7)
        week_end = date.today() - timedelta(days=i*7)
        week_moods = [m for m in moods if week_start <= m.date < week_end]
        if week_moods:
            week_energy = [m.energy_level for m in week_moods if m.energy_level]
            weekly_data.append({
                "week": f"Week {i+1}",
                "avg_energy": round(np.mean(week_energy), 1) if week_energy else 0,
                "entries": len(week_moods),
                "dominant_mood": max(set([m.mood for m in week_moods]), key=[m.mood for m in week_moods].count)
            })
    
    # Generate personalized insights
    insights = []
    
    # Energy insight
    if avg_energy >= 4:
        insights.append("🔥 Your energy levels have been great! Keep up the good work.")
    elif avg_energy <= 2:
        insights.append("💤 Energy has been low. Consider more rest and self-care.")
    
    # Mood pattern insight
    positive_moods = ["happy", "calm", "energetic", "grateful", "excited", "peaceful", "hopeful"]
    positive_count = sum(1 for m in moods if m.mood in positive_moods)
    positive_ratio = positive_count / total
    
    if positive_ratio >= 0.7:
        insights.append("🌟 You've had mostly positive moods! That's wonderful.")
    elif positive_ratio <= 0.3:
        insights.append("💜 Tough period. Remember, it's okay to not be okay. Consider talking to someone.")
    
    # Cycle correlation insight
    if cycle_correlation:
        lowest_energy_phase = min(cycle_correlation.items(), key=lambda x: x[1]["avg_energy"])[0]
        insights.append(f"🌸 Your energy tends to dip during {lowest_energy_phase} phase. Plan accordingly.")
    
    return {
        "has_insights": True,
        "period_days": days,
        "total_entries": total,
        "mood_distribution": mood_distribution,
        "most_common_mood": {
            "mood": most_common,
            "emoji": most_common_emoji,
            "percentage": round((mood_counts.get(most_common, 0)/total)*100, 1)
        },
        "energy": {
            "average": round(avg_energy, 1),
            "highest": max(energy_levels) if energy_levels else 0,
            "lowest": min(energy_levels) if energy_levels else 0
        },
        "top_triggers": top_triggers,
        "cycle_correlation": cycle_correlation,
        "weekly_trend": weekly_data,
        "personalized_insights": insights
    }


@router.get("/streak")
async def get_mood_streak(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mood journaling streak."""
    # Get all unique dates with mood logs
    mood_dates = db.query(func.distinct(models.MoodLog.date)).filter(
        models.MoodLog.user_id == current_user.id
    ).order_by(desc(models.MoodLog.date)).all()
    
    if not mood_dates:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_days_logged": 0
        }
    
    dates = sorted([d[0] for d in mood_dates], reverse=True)
    
    # Calculate current streak
    current_streak = 0
    today = date.today()
    
    for i, d in enumerate(dates):
        expected_date = today - timedelta(days=i)
        if d == expected_date or (i == 0 and d == today - timedelta(days=1)):
            current_streak += 1
        else:
            break
    
    # Calculate longest streak
    longest_streak = 1
    temp_streak = 1
    
    for i in range(1, len(dates)):
        if (dates[i-1] - dates[i]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_days_logged": len(dates),
        "last_logged": dates[0].isoformat() if dates else None
    }


@router.delete("/{log_id}")
async def delete_mood_log(
    log_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a mood log entry."""
    mood_log = db.query(models.MoodLog).filter(
        models.MoodLog.id == log_id,
        models.MoodLog.user_id == current_user.id
    ).first()
    
    if not mood_log:
        raise HTTPException(status_code=404, detail="Mood log not found")
    
    db.delete(mood_log)
    db.commit()
    
    return {"success": True, "message": "Mood log deleted"}
