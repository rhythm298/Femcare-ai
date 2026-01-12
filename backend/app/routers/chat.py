"""
Chat router for FemCare AI.
Handles AI health assistant conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta, datetime
from typing import List, Optional
import re
import numpy as np

from app.database import get_db
from app import models, schemas
from app.security import get_current_user

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


# Intent patterns for classification
INTENT_PATTERNS = {
    "cycle_query": [
        r"when.*period", r"next.*period", r"cycle", r"menstrual",
        r"ovulation", r"fertile", r"tracking"
    ],
    "symptom_query": [
        r"symptom", r"pain", r"cramp", r"headache", r"fatigue",
        r"feeling", r"hurt", r"ache", r"bloat"
    ],
    "risk_query": [
        r"pcos", r"endometriosis", r"anemia", r"thyroid", r"risk",
        r"diagnosis", r"condition", r"health score"
    ],
    "recommendation_query": [
        r"recommend", r"suggest", r"should i", r"what can i",
        r"help with", r"tips", r"advice"
    ],
    "education_query": [
        r"what is", r"explain", r"tell me about", r"learn",
        r"understand", r"why do", r"how does"
    ],
    "greeting": [
        r"^hi$", r"^hello$", r"^hey$", r"good morning", r"good evening",
        r"how are you"
    ],
    "gratitude": [
        r"thank", r"thanks", r"appreciate"
    ]
}


def classify_intent(message: str) -> str:
    """Classify the user's intent from their message."""
    message_lower = message.lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return intent
    
    return "general"


def extract_entities(message: str) -> dict:
    """Extract relevant entities from the message."""
    entities = {}
    message_lower = message.lower()
    
    # Symptom mentions
    symptom_keywords = ["cramps", "headache", "fatigue", "bloating", "pain", 
                        "nausea", "mood", "anxiety", "stress", "acne"]
    mentioned_symptoms = [s for s in symptom_keywords if s in message_lower]
    if mentioned_symptoms:
        entities["symptoms"] = mentioned_symptoms
    
    # Condition mentions
    conditions = ["pcos", "endometriosis", "anemia", "thyroid"]
    mentioned_conditions = [c for c in conditions if c in message_lower]
    if mentioned_conditions:
        entities["conditions"] = mentioned_conditions
    
    # Time mentions
    if "today" in message_lower:
        entities["time_reference"] = "today"
    elif "yesterday" in message_lower:
        entities["time_reference"] = "yesterday"
    elif "week" in message_lower:
        entities["time_reference"] = "week"
    elif "month" in message_lower:
        entities["time_reference"] = "month"
    
    return entities


def generate_response(intent: str, entities: dict, user: models.User, db: Session) -> dict:
    """Generate a contextual response based on intent and user data."""
    
    response_content = ""
    actions_taken = []
    confidence = 0.8
    
    if intent == "greeting":
        # Get user's current cycle info for personalized greeting
        latest_cycle = db.query(models.CycleEntry).filter(
            models.CycleEntry.user_id == user.id
        ).order_by(desc(models.CycleEntry.start_date)).first()
        
        if latest_cycle:
            cycle_day = (date.today() - latest_cycle.start_date).days + 1
            if cycle_day <= 5:
                response_content = f"Hi {user.name}! 👋 I see you're on day {cycle_day} of your cycle. How are you feeling? I'm here to help with any questions about your health."
            elif cycle_day <= 14:
                response_content = f"Hello {user.name}! 🌸 You're in your follicular phase (day {cycle_day}). Energy levels often increase during this time! What can I help you with today?"
            else:
                response_content = f"Hey {user.name}! 💜 You're on day {cycle_day} of your cycle. How are you doing? Let me know if you need any health insights!"
        else:
            response_content = f"Hi {user.name}! 👋 Welcome to FemCare AI! I'm your personal health assistant. I can help you track your cycle, understand your symptoms, and provide personalized health insights. How can I help you today?"
        
        confidence = 0.95
    
    elif intent == "cycle_query":
        latest_cycle = db.query(models.CycleEntry).filter(
            models.CycleEntry.user_id == user.id
        ).order_by(desc(models.CycleEntry.start_date)).first()
        
        if latest_cycle:
            cycle_day = (date.today() - latest_cycle.start_date).days + 1
            
            # Determine phase
            if cycle_day <= 5:
                phase = "menstrual phase"
                phase_info = "This is when you have your period. It's normal to experience cramps, fatigue, and mood changes."
            elif cycle_day <= 13:
                phase = "follicular phase"
                phase_info = "Your body is preparing for ovulation. Many women feel more energetic during this time."
            elif cycle_day <= 16:
                phase = "ovulation phase"
                phase_info = "This is your most fertile window. You might notice increased energy and libido."
            else:
                phase = "luteal phase"
                phase_info = "Your body is preparing for your next period. PMS symptoms may occur."
            
            days_until = (latest_cycle.predicted_next_start - date.today()).days if latest_cycle.predicted_next_start else None
            
            response_content = f"📅 **Your Cycle Status**\n\n"
            response_content += f"• **Cycle Day:** {cycle_day}\n"
            response_content += f"• **Current Phase:** {phase.title()}\n"
            if days_until and days_until > 0:
                response_content += f"• **Days Until Next Period:** {days_until}\n"
                response_content += f"• **Predicted Start:** {latest_cycle.predicted_next_start.strftime('%B %d')}\n"
            response_content += f"\n{phase_info}"
            
            actions_taken.append({"action": "retrieved_cycle_info", "data": {"cycle_day": cycle_day}})
        else:
            response_content = "I don't have any cycle data yet! 📝\n\nTo get personalized cycle insights, please log your first period in the Cycle Tracker. Once I have your data, I can predict your next period, track your cycle phases, and provide relevant health tips!"
        
        confidence = 0.9
    
    elif intent == "symptom_query":
        # Get recent symptoms
        week_ago = date.today() - timedelta(days=7)
        recent_symptoms = db.query(models.Symptom).filter(
            models.Symptom.user_id == user.id,
            models.Symptom.date >= week_ago
        ).order_by(desc(models.Symptom.date)).all()
        
        if entities.get("symptoms"):
            # User asked about specific symptoms
            symptom_name = entities["symptoms"][0]
            user_symptoms = [s for s in recent_symptoms if symptom_name in s.symptom_type.lower()]
            
            if user_symptoms:
                avg_severity = np.mean([s.severity for s in user_symptoms])
                response_content = f"Looking at your {symptom_name} over the past week:\n\n"
                response_content += f"• **Occurrences:** {len(user_symptoms)}\n"
                response_content += f"• **Average Severity:** {avg_severity:.1f}/10\n\n"
                
                if avg_severity >= 7:
                    response_content += "⚠️ Your symptoms have been quite severe. If they persist, consider consulting a healthcare provider."
                else:
                    response_content += "💡 **Tips:** Stay hydrated, get enough rest, and try gentle exercise. Would you like more specific recommendations?"
            else:
                response_content = f"I don't see any recent {symptom_name} symptoms logged. If you're currently experiencing this, you can log it in the Symptom Tracker for better insights!"
        else:
            if recent_symptoms:
                response_content = "📊 **Your Recent Symptoms (Last 7 Days)**\n\n"
                symptom_summary = {}
                for s in recent_symptoms:
                    if s.symptom_type not in symptom_summary:
                        symptom_summary[s.symptom_type] = {"count": 0, "total_severity": 0}
                    symptom_summary[s.symptom_type]["count"] += 1
                    symptom_summary[s.symptom_type]["total_severity"] += s.severity
                
                for symptom, data in sorted(symptom_summary.items(), key=lambda x: -x[1]["count"])[:5]:
                    avg = data["total_severity"] / data["count"]
                    response_content += f"• {symptom.replace('_', ' ').title()}: {data['count']}x (avg severity: {avg:.1f})\n"
                
                response_content += "\nWould you like tips for managing any of these symptoms?"
            else:
                response_content = "No symptoms logged in the past week. That's great if you're feeling well! 🌟\n\nRemember, tracking symptoms helps me understand your patterns better. Even mild symptoms are worth logging!"
        
        actions_taken.append({"action": "analyzed_symptoms"})
        confidence = 0.85
    
    elif intent == "risk_query":
        # Get latest risk scores
        risks = {}
        for condition in ["pcos", "endometriosis", "anemia", "thyroid"]:
            latest = db.query(models.RiskScore).filter(
                models.RiskScore.user_id == user.id,
                models.RiskScore.condition_type == condition
            ).order_by(desc(models.RiskScore.calculated_at)).first()
            
            if latest:
                risks[condition] = latest
        
        if entities.get("conditions"):
            # User asked about specific condition
            condition = entities["conditions"][0]
            if condition in risks:
                risk = risks[condition]
                response_content = f"**{condition.upper()} Risk Assessment**\n\n"
                response_content += f"• **Risk Score:** {risk.score * 100:.0f}%\n"
                response_content += f"• **Confidence:** {risk.confidence * 100:.0f}%\n"
                if risk.trend:
                    trend_emoji = "📈" if risk.trend == "worsening" else "📉" if risk.trend == "improving" else "➡️"
                    response_content += f"• **Trend:** {trend_emoji} {risk.trend.title()}\n"
                
                if risk.contributing_factors:
                    response_content += "\n**Contributing Factors:**\n"
                    for factor in risk.contributing_factors[:3]:
                        response_content += f"• {factor['factor']}: {factor['value']}\n"
                
                if risk.score >= 0.6:
                    response_content += f"\n⚠️ Your {condition.upper()} risk is elevated. I recommend discussing this with a healthcare provider."
                else:
                    response_content += f"\n✅ Your {condition.upper()} risk is currently in a healthy range."
            else:
                response_content = f"I don't have enough data yet to assess your {condition.upper()} risk. Keep tracking your cycles and symptoms for more accurate insights!"
        else:
            if risks:
                response_content = "**Your Health Risk Summary**\n\n"
                for condition, risk in risks.items():
                    level = "🟢 Low" if risk.score < 0.3 else "🟡 Medium" if risk.score < 0.6 else "🔴 Elevated"
                    response_content += f"• **{condition.upper()}:** {level} ({risk.score * 100:.0f}%)\n"
                
                # Overall health score
                avg_risk = np.mean([r.score for r in risks.values()])
                health_score = (1 - avg_risk) * 100
                response_content += f"\n**Overall Health Score:** {health_score:.0f}/100\n"
                response_content += "\nWould you like details about any specific condition?"
            else:
                response_content = "I need more data to calculate your health risks. Please:\n\n1. Track at least 3 menstrual cycles\n2. Log your symptoms regularly\n3. Complete your health profile\n\nThis helps me provide accurate risk assessments!"
        
        actions_taken.append({"action": "retrieved_risk_scores"})
        confidence = 0.88
    
    elif intent == "recommendation_query":
        recommendations = db.query(models.Recommendation).filter(
            models.Recommendation.user_id == user.id,
            models.Recommendation.is_completed == False
        ).order_by(desc(models.Recommendation.priority)).limit(3).all()
        
        if recommendations:
            response_content = "**Your Top Recommendations** 💡\n\n"
            for i, rec in enumerate(recommendations, 1):
                response_content += f"**{i}. {rec.title}**\n"
                response_content += f"{rec.description}\n\n"
        else:
            response_content = "Great job! You've completed all your recommendations! 🎉\n\n"
            response_content += "Keep up with your tracking, and I'll generate new personalized recommendations based on your updated data."
        
        actions_taken.append({"action": "retrieved_recommendations"})
        confidence = 0.9
    
    elif intent == "education_query":
        # Provide educational content based on keywords
        response_content = "Great question! 📚\n\n"
        
        if "pcos" in str(entities.get("conditions", [])):
            response_content += "**What is PCOS?**\n\n"
            response_content += "Polycystic Ovary Syndrome (PCOS) is a hormonal disorder affecting about 1 in 10 women. Common signs include:\n\n"
            response_content += "• Irregular or missed periods\n"
            response_content += "• Excess androgen (acne, facial hair)\n"
            response_content += "• Polycystic ovaries on ultrasound\n\n"
            response_content += "**Key Fact:** PCOS is very manageable with lifestyle changes and medical care. Early detection helps!"
        elif "endometriosis" in str(entities.get("conditions", [])):
            response_content += "**What is Endometriosis?**\n\n"
            response_content += "Endometriosis occurs when tissue similar to the uterine lining grows outside the uterus. Signs include:\n\n"
            response_content += "• Severe menstrual cramps\n"
            response_content += "• Pain during/after intercourse\n"
            response_content += "• Heavy periods\n"
            response_content += "• Chronic pelvic pain\n\n"
            response_content += "**Key Fact:** Diagnosis often takes 7-10 years. Tracking your symptoms helps identify it earlier!"
        else:
            response_content += "I can help explain various women's health topics! Ask me about:\n\n"
            response_content += "• **PCOS** - Polycystic Ovary Syndrome\n"
            response_content += "• **Endometriosis** - Chronic pelvic condition\n"
            response_content += "• **Menstrual Cycle** - Phases and what to expect\n"
            response_content += "• **Symptoms** - What various symptoms might mean\n\n"
            response_content += "What would you like to learn about?"
        
        confidence = 0.85
    
    elif intent == "gratitude":
        response_content = "You're very welcome! 💜 I'm always here to help with your health questions. Remember, I'm your personal health companion on this journey. Take care of yourself! 🌸"
        confidence = 0.95
    
    else:
        # General response
        response_content = "I'm here to help with your health! 🩺\n\n"
        response_content += "I can assist you with:\n\n"
        response_content += "📅 **Cycle Tracking** - \"When is my next period?\"\n"
        response_content += "🩹 **Symptoms** - \"Tell me about my recent symptoms\"\n"
        response_content += "📊 **Health Risks** - \"What's my PCOS risk?\"\n"
        response_content += "💡 **Recommendations** - \"What should I do for my health?\"\n"
        response_content += "📚 **Education** - \"What is endometriosis?\"\n\n"
        response_content += "What would you like to know about?"
        confidence = 0.7
    
    return {
        "content": response_content,
        "actions_taken": actions_taken,
        "confidence": confidence
    }


@router.post("/", response_model=schemas.ChatResponse)
async def send_message(
    message: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI health assistant.
    """
    # Classify intent
    intent = classify_intent(message.content)
    
    # Extract entities
    entities = extract_entities(message.content)
    
    # Save user message
    user_message = models.ChatMessage(
        user_id=current_user.id,
        role="user",
        content=message.content,
        intent=intent,
        entities=entities
    )
    db.add(user_message)
    
    # Generate response
    response_data = generate_response(intent, entities, current_user, db)
    
    # Save assistant message
    assistant_message = models.ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response_data["content"],
        intent=intent,
        actions_taken=response_data["actions_taken"],
        confidence=response_data["confidence"]
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message


@router.get("/history", response_model=List[schemas.ChatResponse])
async def get_chat_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent chat history.
    """
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id
    ).order_by(desc(models.ChatMessage.created_at)).limit(limit).all()
    
    # Return in chronological order
    return list(reversed(messages))


@router.delete("/history", status_code=204)
async def clear_chat_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all chat history.
    """
    db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id
    ).delete()
    db.commit()
    
    return None
