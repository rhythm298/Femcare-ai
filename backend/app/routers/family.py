"""
Family Sharing router for FemCare AI.
Enables sharing health data with family members with real-time updates.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict
import json
import secrets
import asyncio

from app.database import get_db
from app import models
from app.security import get_current_user

router = APIRouter(prefix="/api/family", tags=["Family Sharing"])

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, invite_code: str):
        await websocket.accept()
        if invite_code not in self.active_connections:
            self.active_connections[invite_code] = []
        self.active_connections[invite_code].append(websocket)
    
    def disconnect(self, websocket: WebSocket, invite_code: str):
        if invite_code in self.active_connections:
            if websocket in self.active_connections[invite_code]:
                self.active_connections[invite_code].remove(websocket)
    
    async def broadcast(self, invite_code: str, message: dict):
        if invite_code in self.active_connections:
            for connection in self.active_connections[invite_code]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


def generate_invite_code() -> str:
    """Generate a unique invite code."""
    return secrets.token_urlsafe(16)


def get_current_phase(user_id: int, db: Session) -> str:
    """Get current cycle phase for a user."""
    latest_cycle = db.query(models.CycleEntry).filter(
        models.CycleEntry.user_id == user_id
    ).order_by(desc(models.CycleEntry.start_date)).first()
    
    if not latest_cycle:
        return "unknown"
    
    today = date.today()
    days_since_start = (today - latest_cycle.start_date).days
    
    if days_since_start <= 5:
        return "menstrual"
    elif days_since_start <= 13:
        return "follicular"
    elif days_since_start <= 16:
        return "ovulation"
    elif days_since_start <= 25:
        return "luteal"
    else:
        return "late_luteal"


def generate_care_suggestions(phase: str) -> List[dict]:
    """Generate care suggestions based on cycle phase."""
    suggestions = {
        "menstrual": [
            {
                "type": "emotional_support",
                "title": "Extra Understanding Needed",
                "description": "She may be experiencing cramps or fatigue. Offer to help with tasks and be patient.",
                "priority": 9
            },
            {
                "type": "physical_care",
                "title": "Warm Comfort",
                "description": "A heating pad or warm water bottle can help with cramps. Consider making her a warm drink.",
                "priority": 8
            },
            {
                "type": "dietary",
                "title": "Iron-Rich Foods",
                "description": "Help prepare iron-rich meals like spinach, lentils, or lean meat to replenish blood loss.",
                "priority": 7
            },
            {
                "type": "activity",
                "title": "Gentle Activities",
                "description": "Suggest light activities like walks or gentle yoga instead of intense exercise.",
                "priority": 6
            }
        ],
        "follicular": [
            {
                "type": "activity",
                "title": "Great Time for Activities",
                "description": "Energy is rising! Good time to plan active outings or exercise together.",
                "priority": 6
            },
            {
                "type": "emotional_support",
                "title": "Support New Initiatives",
                "description": "She may be feeling creative and motivated. Encourage new projects or goals.",
                "priority": 5
            }
        ],
        "ovulation": [
            {
                "type": "activity",
                "title": "Peak Energy Time",
                "description": "This is when energy and mood are typically highest. Great for social activities!",
                "priority": 5
            },
            {
                "type": "emotional_support",
                "title": "Communication is Key",
                "description": "She may be more communicative. Good time for important conversations.",
                "priority": 4
            }
        ],
        "luteal": [
            {
                "type": "emotional_support",
                "title": "PMS Awareness",
                "description": "Mood swings may occur. Be extra patient and avoid unnecessary conflicts.",
                "priority": 8
            },
            {
                "type": "dietary",
                "title": "Healthy Snacks Ready",
                "description": "Keep healthy snacks available. She may have cravings - dark chocolate is a good option!",
                "priority": 7
            },
            {
                "type": "physical_care",
                "title": "Comfort Measures",
                "description": "Bloating and breast tenderness may occur. Loose, comfortable clothing appreciated.",
                "priority": 6
            }
        ],
        "late_luteal": [
            {
                "type": "emotional_support",
                "title": "Extra Patience Required",
                "description": "She may be more sensitive. Offer support without judgment.",
                "priority": 9
            },
            {
                "type": "physical_care",
                "title": "Rest and Relaxation",
                "description": "Help create a calm environment. Reduce stressors where possible.",
                "priority": 8
            },
            {
                "type": "dietary",
                "title": "Period Prep",
                "description": "Stock up on comfort foods and essentials she may need.",
                "priority": 7
            }
        ]
    }
    
    return suggestions.get(phase, suggestions.get("follicular", []))


@router.post("/invite")
async def invite_family_member(
    member_email: str,
    member_name: str,
    relation_type: str = Query(..., regex="^(mother|father|sister|brother|partner|husband|wife|friend|other)$"),
    can_view_mood: bool = True,
    can_view_symptoms: bool = True,
    can_view_exercise: bool = True,
    can_view_cycle: bool = True,
    can_view_nutrition: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invite a family member to view health data.
    """
    # Check if already invited
    existing = db.query(models.FamilyMember).filter(
        models.FamilyMember.user_id == current_user.id,
        models.FamilyMember.member_email == member_email
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="This email is already invited. Use update permissions to modify access."
        )
    
    # Generate unique invite code
    invite_code = generate_invite_code()
    
    # Create family member entry
    family_member = models.FamilyMember(
        user_id=current_user.id,
        member_email=member_email,
        member_name=member_name,
        relation_type=relation_type,
        invite_code=invite_code,
        invite_status="pending",
        permissions={
            "can_view_mood": can_view_mood,
            "can_view_symptoms": can_view_symptoms,
            "can_view_exercise": can_view_exercise,
            "can_view_cycle": can_view_cycle,
            "can_view_nutrition": can_view_nutrition
        }
    )
    
    db.add(family_member)
    db.commit()
    db.refresh(family_member)
    
    # Generate shareable link
    share_link = f"/family-view/{invite_code}"
    
    return {
        "id": family_member.id,
        "member_name": member_name,
        "member_email": member_email,
        "relationship": relation_type,
        "invite_code": invite_code,
        "share_link": share_link,
        "status": "pending",
        "message": f"Invitation created for {member_name}. Share this link with them to provide access."
    }


@router.get("/members")
async def get_family_members(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all family members with sharing access.
    """
    members = db.query(models.FamilyMember).filter(
        models.FamilyMember.user_id == current_user.id
    ).all()
    
    return {
        "members": [{
            "id": member.id,
            "member_name": member.member_name,
            "member_email": member.member_email,
            "relationship": member.relation_type,
            "invite_code": member.invite_code,
            "invite_status": member.invite_status,
            "permissions": member.permissions or {},
            "created_at": str(member.created_at),
            "accepted_at": str(member.accepted_at) if member.accepted_at else None
        } for member in members],
        "total": len(members)
    }


@router.post("/accept-invite/{invite_code}")
async def accept_invite(
    invite_code: str,
    db: Session = Depends(get_db)
):
    """
    Accept a family sharing invitation (public endpoint).
    """
    family_member = db.query(models.FamilyMember).filter(
        models.FamilyMember.invite_code == invite_code
    ).first()
    
    if not family_member:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    
    family_member.invite_status = "accepted"
    family_member.accepted_at = datetime.now()
    db.commit()
    
    # Get user name
    user = db.query(models.User).filter(models.User.id == family_member.user_id).first()
    
    return {
        "message": "Invitation accepted successfully",
        "user_name": user.name if user else "User",
        "relationship": family_member.relation_type,
        "permissions": family_member.permissions
    }


@router.put("/permissions/{member_id}")
async def update_permissions(
    member_id: int,
    can_view_mood: Optional[bool] = None,
    can_view_symptoms: Optional[bool] = None,
    can_view_exercise: Optional[bool] = None,
    can_view_cycle: Optional[bool] = None,
    can_view_nutrition: Optional[bool] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update sharing permissions for a family member.
    """
    member = db.query(models.FamilyMember).filter(
        models.FamilyMember.id == member_id,
        models.FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    permissions = member.permissions or {}
    
    if can_view_mood is not None:
        permissions["can_view_mood"] = can_view_mood
    if can_view_symptoms is not None:
        permissions["can_view_symptoms"] = can_view_symptoms
    if can_view_exercise is not None:
        permissions["can_view_exercise"] = can_view_exercise
    if can_view_cycle is not None:
        permissions["can_view_cycle"] = can_view_cycle
    if can_view_nutrition is not None:
        permissions["can_view_nutrition"] = can_view_nutrition
    
    member.permissions = permissions
    db.commit()
    
    return {
        "id": member.id,
        "member_name": member.member_name,
        "permissions": permissions,
        "message": "Permissions updated successfully"
    }


@router.delete("/members/{member_id}")
async def remove_family_member(
    member_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a family member's access.
    """
    member = db.query(models.FamilyMember).filter(
        models.FamilyMember.id == member_id,
        models.FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    db.delete(member)
    db.commit()
    
    return {"message": "Family member access removed successfully"}


@router.get("/shared/{invite_code}")
async def get_shared_data(
    invite_code: str,
    db: Session = Depends(get_db)
):
    """
    Get shared health data for a family member (public endpoint with invite code).
    """
    family_member = db.query(models.FamilyMember).filter(
        models.FamilyMember.invite_code == invite_code
    ).first()
    
    if not family_member:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    
    if family_member.invite_status != "accepted":
        return {
            "status": "pending",
            "message": "Please accept the invitation first",
            "accept_url": f"/api/family/accept-invite/{invite_code}"
        }
    
    user = db.query(models.User).filter(models.User.id == family_member.user_id).first()
    permissions = family_member.permissions or {}
    
    shared_data = {
        "user_name": user.name if user else "User",
        "relationship": family_member.relation_type,
        "permissions": permissions,
        "last_updated": datetime.now().isoformat()
    }
    
    # Get current phase
    current_phase = get_current_phase(family_member.user_id, db)
    shared_data["current_phase"] = current_phase
    
    phase_descriptions = {
        "menstrual": "During her period - may experience cramps, fatigue, and mood changes",
        "follicular": "Post-period phase - energy is building up",
        "ovulation": "Most energetic time - feeling great!",
        "luteal": "Pre-period phase - PMS symptoms may start",
        "late_luteal": "Just before period - may need extra care",
        "unknown": "Cycle data not available"
    }
    shared_data["phase_description"] = phase_descriptions.get(current_phase, "")
    
    # Get mood if permitted
    if permissions.get("can_view_mood", False):
        recent_mood = db.query(models.MoodLog).filter(
            models.MoodLog.user_id == family_member.user_id
        ).order_by(desc(models.MoodLog.date)).first()
        
        if recent_mood:
            shared_data["mood"] = {
                "mood": recent_mood.mood,
                "emoji": recent_mood.mood_emoji,
                "energy_level": recent_mood.energy_level,
                "date": str(recent_mood.date)
            }
    
    # Get symptoms if permitted
    if permissions.get("can_view_symptoms", False):
        recent_symptoms = db.query(models.Symptom).filter(
            models.Symptom.user_id == family_member.user_id,
            models.Symptom.date >= date.today() - timedelta(days=7)
        ).order_by(desc(models.Symptom.date)).limit(5).all()
        
        shared_data["recent_symptoms"] = [{
            "symptom": s.symptom_type.replace("_", " ").title(),
            "severity": s.severity,
            "date": str(s.date)
        } for s in recent_symptoms]
    
    # Get exercise if permitted
    if permissions.get("can_view_exercise", False):
        recent_exercises = db.query(models.ExerciseLog).filter(
            models.ExerciseLog.user_id == family_member.user_id,
            models.ExerciseLog.date >= date.today() - timedelta(days=7)
        ).order_by(desc(models.ExerciseLog.date)).limit(5).all()
        
        exercise_streak = db.query(models.HealthStreak).filter(
            models.HealthStreak.user_id == family_member.user_id,
            models.HealthStreak.streak_type == "exercise"
        ).first()
        
        shared_data["exercise"] = {
            "recent": [{
                "name": e.exercise_name,
                "duration": e.duration_minutes,
                "calories": e.calories_burned,
                "date": str(e.date)
            } for e in recent_exercises],
            "current_streak": exercise_streak.current_streak if exercise_streak else 0
        }
    
    # Get cycle info if permitted - ENHANCED with detailed period insights
    if permissions.get("can_view_cycle", False):
        latest_cycle = db.query(models.CycleEntry).filter(
            models.CycleEntry.user_id == family_member.user_id
        ).order_by(desc(models.CycleEntry.start_date)).first()
        
        if latest_cycle:
            days_since_start = (date.today() - latest_cycle.start_date).days + 1
            avg_cycle_length = latest_cycle.cycle_length or 28
            avg_period_length = latest_cycle.period_length or 5
            
            # Calculate days until next period
            days_until_period = None
            if latest_cycle.predicted_next_start:
                days_until_period = (latest_cycle.predicted_next_start - date.today()).days
            else:
                days_until_period = avg_cycle_length - days_since_start
            
            # Is she currently on her period?
            is_on_period = days_since_start <= avg_period_length
            
            # Period days remaining (if on period)
            period_days_remaining = max(0, avg_period_length - days_since_start) if is_on_period else 0
            
            # Current phase details
            phase_info = ""
            if days_since_start <= avg_period_length:
                phase_info = f"Day {days_since_start} of period - likely experiencing menstrual symptoms"
            elif days_since_start <= 13:
                phase_info = "Follicular phase - energy is building up"
            elif days_since_start <= 16:
                phase_info = "Ovulation phase - peak energy and mood"
            elif days_until_period and days_until_period <= 7:
                phase_info = f"PMS likely - about {days_until_period} days until next period"
            else:
                phase_info = "Luteal phase - preparing for next cycle"
            
            shared_data["cycle"] = {
                "current_day": days_since_start,
                "predicted_next": str(latest_cycle.predicted_next_start) if latest_cycle.predicted_next_start else None,
                "days_until_period": days_until_period if days_until_period and days_until_period > 0 else 0,
                "is_on_period": is_on_period,
                "period_days_remaining": period_days_remaining,
                "flow_level": latest_cycle.flow_level or "unknown",
                "avg_cycle_length": avg_cycle_length,
                "avg_period_length": avg_period_length,
                "phase_info": phase_info,
                "start_date": str(latest_cycle.start_date)
            }
    
    # Get water tracking data
    today = date.today()
    water_logs = db.query(models.WaterLog).filter(
        models.WaterLog.user_id == family_member.user_id,
        models.WaterLog.date == today
    ).all()
    
    total_water = sum(log.amount_ml for log in water_logs) if water_logs else 0
    water_goal = 2500  # Default goal in ml
    
    shared_data["water"] = {
        "today_ml": total_water,
        "goal_ml": water_goal,
        "percent": round((total_water / water_goal) * 100) if water_goal > 0 else 0
    }
    
    # Get nutrition data if permitted
    if permissions.get("can_view_nutrition", False):
        calorie_logs = db.query(models.CalorieLog).filter(
            models.CalorieLog.user_id == family_member.user_id,
            models.CalorieLog.date == today
        ).all()
        
        today_calories = sum(log.total_calories for log in calorie_logs) if calorie_logs else 0
        today_protein = sum(log.total_protein or 0 for log in calorie_logs) if calorie_logs else 0
        today_carbs = sum(log.total_carbs or 0 for log in calorie_logs) if calorie_logs else 0
        today_fat = sum(log.total_fat or 0 for log in calorie_logs) if calorie_logs else 0
        
        # Calculate BMR-based goal
        calorie_goal = 2000  # Default
        if user and user.weight and user.height and user.date_of_birth:
            age = (date.today() - user.date_of_birth).days // 365
            # Mifflin-St Jeor for women
            calorie_goal = round(10 * user.weight + 6.25 * user.height - 5 * age - 161)
        
        shared_data["nutrition"] = {
            "today_calories": round(today_calories),
            "goal_calories": calorie_goal,
            "protein": round(today_protein, 1),
            "carbs": round(today_carbs, 1),
            "fat": round(today_fat, 1),
            "meals_logged": len(calorie_logs)
        }
    
    # Weekly summary
    week_ago = today - timedelta(days=7)
    
    # Exercise days this week
    exercise_days = db.query(func.count(func.distinct(models.ExerciseLog.date))).filter(
        models.ExerciseLog.user_id == family_member.user_id,
        models.ExerciseLog.date >= week_ago
    ).scalar() or 0
    
    # Average water this week
    weekly_water = db.query(func.avg(models.WaterLog.amount_ml)).filter(
        models.WaterLog.user_id == family_member.user_id,
        models.WaterLog.date >= week_ago
    ).scalar() or 0
    
    # Average calories this week
    weekly_cal = db.query(func.avg(models.CalorieLog.total_calories)).filter(
        models.CalorieLog.user_id == family_member.user_id,
        models.CalorieLog.date >= week_ago
    ).scalar() or 0
    
    # Mood trend (most common mood)
    recent_moods = db.query(models.MoodLog.mood).filter(
        models.MoodLog.user_id == family_member.user_id,
        models.MoodLog.date >= week_ago
    ).all()
    mood_trend = "Stable"
    if recent_moods:
        moods = [m[0] for m in recent_moods]
        mood_trend = max(set(moods), key=moods.count).title()
    
    shared_data["weekly_summary"] = {
        "exercise_days": exercise_days,
        "avg_water_percent": round((weekly_water / water_goal) * 100) if weekly_water else 0,
        "avg_calories": round(weekly_cal) if weekly_cal else 0,
        "mood_trend": mood_trend
    }
    
    return shared_data


@router.get("/care-suggestions/{invite_code}")
async def get_care_suggestions(
    invite_code: str,
    db: Session = Depends(get_db)
):
    """
    Get care suggestions for family members based on current cycle phase.
    """
    family_member = db.query(models.FamilyMember).filter(
        models.FamilyMember.invite_code == invite_code
    ).first()
    
    if not family_member:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    
    user = db.query(models.User).filter(models.User.id == family_member.user_id).first()
    current_phase = get_current_phase(family_member.user_id, db)
    suggestions = generate_care_suggestions(current_phase)
    
    # Save suggestions to database
    for suggestion in suggestions:
        care_suggestion = models.CareSuggestion(
            user_id=family_member.user_id,
            phase=current_phase,
            suggestion_type=suggestion["type"],
            title=suggestion["title"],
            description=suggestion["description"],
            priority=suggestion["priority"]
        )
        db.add(care_suggestion)
    db.commit()
    
    return {
        "user_name": user.name if user else "User",
        "current_phase": current_phase,
        "suggestions": suggestions,
        "message": f"Here's how you can support {user.name if user else 'her'} during this phase"
    }


@router.post("/mood")
async def log_mood(
    mood: str = Query(..., regex="^(happy|sad|anxious|calm|irritated|tired|energetic|neutral)$"),
    energy_level: int = Query(..., ge=1, le=5),
    mood_emoji: Optional[str] = None,
    notes: Optional[str] = None,
    log_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log mood for the day (quick emoji-based logging).
    """
    emoji_map = {
        "happy": "😊",
        "sad": "😢",
        "anxious": "😰",
        "calm": "😌",
        "irritated": "😤",
        "tired": "😴",
        "energetic": "⚡",
        "neutral": "😐"
    }
    
    mood_log = models.MoodLog(
        user_id=current_user.id,
        date=log_date or date.today(),
        mood=mood,
        mood_emoji=mood_emoji or emoji_map.get(mood, "😐"),
        energy_level=energy_level,
        notes=notes
    )
    
    db.add(mood_log)
    db.commit()
    db.refresh(mood_log)
    
    # Notify connected family members
    family_members = db.query(models.FamilyMember).filter(
        models.FamilyMember.user_id == current_user.id,
        models.FamilyMember.invite_status == "accepted"
    ).all()
    
    for member in family_members:
        permissions = member.permissions or {}
        if permissions.get("can_view_mood", False):
            asyncio.create_task(manager.broadcast(member.invite_code, {
                "type": "mood_update",
                "mood": mood,
                "emoji": mood_log.mood_emoji,
                "energy_level": energy_level,
                "timestamp": datetime.now().isoformat()
            }))
    
    return {
        "id": mood_log.id,
        "mood": mood,
        "emoji": mood_log.mood_emoji,
        "energy_level": energy_level,
        "date": str(mood_log.date),
        "message": f"Mood logged: {mood_log.mood_emoji} {mood}"
    }


@router.get("/mood/history")
async def get_mood_history(
    days: int = Query(30, ge=7, le=90),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get mood history for the current user.
    """
    start_date = date.today() - timedelta(days=days)
    
    moods = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == current_user.id,
        models.MoodLog.date >= start_date
    ).order_by(desc(models.MoodLog.date)).all()
    
    return {
        "moods": [{
            "id": m.id,
            "date": str(m.date),
            "mood": m.mood,
            "emoji": m.mood_emoji,
            "energy_level": m.energy_level,
            "notes": m.notes
        } for m in moods],
        "total": len(moods)
    }


@router.websocket("/realtime/{invite_code}")
async def websocket_endpoint(
    websocket: WebSocket,
    invite_code: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates to family members.
    """
    # Verify invite code
    family_member = db.query(models.FamilyMember).filter(
        models.FamilyMember.invite_code == invite_code,
        models.FamilyMember.invite_status == "accepted"
    ).first()
    
    if not family_member:
        await websocket.close(code=4001)
        return
    
    await manager.connect(websocket, invite_code)
    
    try:
        # Send initial data
        user = db.query(models.User).filter(models.User.id == family_member.user_id).first()
        current_phase = get_current_phase(family_member.user_id, db)
        
        await websocket.send_json({
            "type": "connected",
            "user_name": user.name if user else "User",
            "current_phase": current_phase,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, invite_code)
