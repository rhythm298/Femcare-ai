"""
FemCare AI Agent Core
Main agent class that orchestrates all tools for health analysis and recommendations.
"""

from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from dataclasses import dataclass
import numpy as np

from agent.tools.cycle_analyzer import CycleAnalyzer, CycleData


@dataclass
class UserContext:
    """User health context for agent reasoning."""
    user_id: int
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    is_pregnant: bool = False
    is_trying_to_conceive: bool = False
    is_on_birth_control: bool = False
    medical_conditions: List[str] = None


@dataclass
class HealthObservation:
    """Represents a health observation for agent processing."""
    cycles: List[CycleData]
    symptoms: List[Dict]
    lifestyle: Optional[Dict] = None


class FemCareAgent:
    """
    Main agentic AI class for women's health management.
    
    Implements a perception-reasoning-action loop:
    1. Perception: Process multi-modal health inputs
    2. Reasoning: Analyze patterns and assess risks
    3. Action: Generate insights and recommendations
    """
    
    def __init__(self):
        self.cycle_analyzer = CycleAnalyzer()
        self.confidence_threshold = 0.7
    
    async def reason_and_act(
        self,
        user_input: str,
        user_context: UserContext,
        observation: HealthObservation
    ) -> Dict:
        """
        Main reasoning loop - processes user input and generates response.
        
        Args:
            user_input: User's query or command
            user_context: User profile data
            observation: Current health observations
            
        Returns:
            Dict with response, actions taken, and confidence
        """
        # Step 1: Classify intent
        intent = self._classify_intent(user_input)
        
        # Step 2: Gather relevant data based on intent
        context_data = await self._gather_context(intent, user_context, observation)
        
        # Step 3: Reason about the situation
        reasoning_result = self._reason(intent, context_data, user_context)
        
        # Step 4: Plan actions
        action_plan = self._plan_actions(reasoning_result)
        
        # Step 5: Execute actions and generate response
        result = await self._execute_and_respond(action_plan, reasoning_result)
        
        return result
    
    def _classify_intent(self, user_input: str) -> str:
        """Classify user intent from natural language input."""
        input_lower = user_input.lower()
        
        # Intent patterns
        patterns = {
            "cycle_query": ["when", "period", "cycle", "ovulation", "fertile"],
            "symptom_report": ["feeling", "pain", "cramp", "symptom", "hurts"],
            "risk_query": ["risk", "pcos", "endometriosis", "anemia", "thyroid"],
            "recommendation": ["should", "recommend", "help", "what can", "tips"],
            "health_check": ["health", "score", "how am i", "status", "summary"],
            "education": ["what is", "explain", "tell me", "learn about"]
        }
        
        for intent, keywords in patterns.items():
            if any(kw in input_lower for kw in keywords):
                return intent
        
        return "general"
    
    async def _gather_context(
        self,
        intent: str,
        user_context: UserContext,
        observation: HealthObservation
    ) -> Dict:
        """Gather relevant context based on intent."""
        context = {"intent": intent}
        
        if intent in ["cycle_query", "health_check"]:
            # Analyze cycles
            if observation.cycles:
                context["cycle_analysis"] = self.cycle_analyzer.analyze(observation.cycles)
        
        if intent in ["symptom_report", "risk_query", "health_check"]:
            # Analyze symptoms
            if observation.symptoms:
                context["symptom_analysis"] = self._analyze_symptoms(observation.symptoms)
        
        if intent in ["risk_query", "health_check"]:
            # Calculate risk scores
            context["risk_scores"] = self._calculate_all_risks(
                user_context, observation
            )
        
        return context
    
    def _reason(
        self,
        intent: str,
        context: Dict,
        user_context: UserContext
    ) -> Dict:
        """Apply reasoning to the gathered context."""
        reasoning = {
            "intent": intent,
            "confidence": 0.8,
            "concerns": [],
            "positive_findings": [],
            "action_items": []
        }
        
        # Cycle-based reasoning
        if "cycle_analysis" in context:
            cycle = context["cycle_analysis"]
            
            if cycle.get("is_regular") is False:
                reasoning["concerns"].append({
                    "type": "cycle_irregularity",
                    "severity": "medium",
                    "detail": cycle.get("irregularity_reasons", [])
                })
            
            if cycle.get("regularity_score", 0) >= 0.8:
                reasoning["positive_findings"].append("Cycles are regular and healthy")
        
        # Risk-based reasoning
        if "risk_scores" in context:
            risks = context["risk_scores"]
            for condition, data in risks.items():
                if data["score"] >= 0.6:
                    reasoning["concerns"].append({
                        "type": f"{condition}_risk",
                        "severity": "high" if data["score"] >= 0.8 else "medium",
                        "score": data["score"],
                        "factors": data.get("factors", [])
                    })
                    reasoning["action_items"].append(f"Consider consulting a healthcare provider about {condition}")
        
        # Symptom-based reasoning
        if "symptom_analysis" in context:
            symptoms = context["symptom_analysis"]
            if symptoms.get("average_severity", 0) >= 7:
                reasoning["concerns"].append({
                    "type": "severe_symptoms",
                    "severity": "high",
                    "detail": "Recent symptoms have been quite severe"
                })
        
        # Adjust confidence based on data availability
        data_points = sum([
            1 if "cycle_analysis" in context else 0,
            1 if "symptom_analysis" in context else 0,
            1 if user_context.age else 0,
            1 if user_context.weight and user_context.height else 0
        ])
        reasoning["confidence"] = min(0.95, 0.5 + (data_points * 0.1))
        
        return reasoning
    
    def _plan_actions(self, reasoning: Dict) -> List[Dict]:
        """Plan actions based on reasoning results."""
        actions = []
        
        # Always provide a response
        actions.append({"type": "respond", "priority": 1})
        
        # Generate insights for concerns
        for concern in reasoning.get("concerns", []):
            if concern["severity"] == "high":
                actions.append({
                    "type": "generate_insight",
                    "priority": 2,
                    "data": concern
                })
        
        # Add recommendations
        if reasoning.get("action_items"):
            actions.append({
                "type": "generate_recommendations",
                "priority": 3,
                "items": reasoning["action_items"]
            })
        
        return sorted(actions, key=lambda x: x["priority"])
    
    async def _execute_and_respond(
        self,
        action_plan: List[Dict],
        reasoning: Dict
    ) -> Dict:
        """Execute action plan and generate response."""
        actions_taken = []
        response_parts = []
        
        for action in action_plan:
            if action["type"] == "respond":
                # Generate natural language response
                response_parts.append(self._generate_response_text(reasoning))
                actions_taken.append("generated_response")
            
            elif action["type"] == "generate_insight":
                actions_taken.append(f"flagged_{action['data']['type']}")
            
            elif action["type"] == "generate_recommendations":
                response_parts.append("\n\n**Recommendations:**")
                for item in action["items"]:
                    response_parts.append(f"• {item}")
                actions_taken.append("generated_recommendations")
        
        return {
            "response": "\n".join(response_parts),
            "actions_taken": actions_taken,
            "confidence": reasoning["confidence"],
            "reasoning_summary": {
                "concerns": len(reasoning.get("concerns", [])),
                "positive_findings": len(reasoning.get("positive_findings", []))
            }
        }
    
    def _generate_response_text(self, reasoning: Dict) -> str:
        """Generate natural language response from reasoning."""
        intent = reasoning.get("intent", "general")
        
        if intent == "health_check":
            if reasoning.get("positive_findings"):
                return "Based on your data, things are looking good! " + " ".join(reasoning["positive_findings"])
            elif reasoning.get("concerns"):
                concern_types = [c["type"] for c in reasoning["concerns"]]
                return f"I've noticed some areas to pay attention to: {', '.join(concern_types)}."
            return "Keep tracking your health data for more personalized insights!"
        
        return "I'm here to help with your health questions!"
    
    def _analyze_symptoms(self, symptoms: List[Dict]) -> Dict:
        """Analyze symptom patterns."""
        if not symptoms:
            return {}
        
        severities = [s.get("severity", 5) for s in symptoms]
        categories = {}
        
        for symptom in symptoms:
            cat = symptom.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_count": len(symptoms),
            "average_severity": np.mean(severities),
            "max_severity": max(severities),
            "by_category": categories
        }
    
    def _calculate_all_risks(
        self,
        user_context: UserContext,
        observation: HealthObservation
    ) -> Dict:
        """Calculate risk scores for all conditions."""
        cycles = observation.cycles
        symptoms = observation.symptoms or []
        
        return {
            "pcos": self._calculate_pcos_risk(user_context, cycles, symptoms),
            "endometriosis": self._calculate_endo_risk(symptoms, cycles),
            "anemia": self._calculate_anemia_risk(symptoms, cycles),
            "thyroid": self._calculate_thyroid_risk(user_context, symptoms)
        }
    
    def _calculate_pcos_risk(
        self,
        user: UserContext,
        cycles: List[CycleData],
        symptoms: List[Dict]
    ) -> Dict:
        """Calculate PCOS risk score."""
        factors = []
        score = 0.1
        
        # Cycle analysis
        if cycles and len(cycles) >= 3:
            cycle_lengths = []
            sorted_cycles = sorted(cycles, key=lambda c: c.start_date)
            for i in range(1, len(sorted_cycles)):
                length = (sorted_cycles[i].start_date - sorted_cycles[i-1].start_date).days
                if 15 <= length <= 60:
                    cycle_lengths.append(length)
            
            if cycle_lengths:
                avg = np.mean(cycle_lengths)
                std = np.std(cycle_lengths)
                
                if avg > 35:
                    score += 0.25
                    factors.append({"factor": "Long cycles", "impact": "high"})
                if std > 7:
                    score += 0.15
                    factors.append({"factor": "Irregular cycles", "impact": "medium"})
        
        # Symptom analysis
        hormonal = [s for s in symptoms if s.get("category") == "hormonal"]
        if len(hormonal) >= 3:
            score += 0.2
            factors.append({"factor": "Hormonal symptoms", "impact": "medium"})
        
        # BMI factor
        if user.weight and user.height:
            bmi = user.weight / ((user.height / 100) ** 2)
            if bmi > 30:
                score += 0.15
                factors.append({"factor": "BMI > 30", "impact": "medium"})
        
        return {
            "score": min(0.95, score),
            "confidence": 0.7 if len(cycles) >= 6 else 0.5,
            "factors": factors
        }
    
    def _calculate_endo_risk(self, symptoms: List[Dict], cycles: List[CycleData]) -> Dict:
        """Calculate endometriosis risk score."""
        factors = []
        score = 0.1
        
        pain = [s for s in symptoms if "pain" in s.get("symptom_type", "").lower()]
        if pain:
            avg_severity = np.mean([s.get("severity", 5) for s in pain])
            if avg_severity >= 7:
                score += 0.3
                factors.append({"factor": "Severe pain", "impact": "high"})
        
        heavy_flow = [c for c in cycles if c.flow_level in ["heavy", "very_heavy"]]
        if len(heavy_flow) >= 2:
            score += 0.15
            factors.append({"factor": "Heavy bleeding", "impact": "medium"})
        
        return {
            "score": min(0.95, score),
            "confidence": 0.6,
            "factors": factors
        }
    
    def _calculate_anemia_risk(self, symptoms: List[Dict], cycles: List[CycleData]) -> Dict:
        """Calculate anemia risk score."""
        factors = []
        score = 0.1
        
        fatigue = [s for s in symptoms if "fatigue" in s.get("symptom_type", "").lower()]
        if len(fatigue) >= 3:
            score += 0.2
            factors.append({"factor": "Frequent fatigue", "impact": "medium"})
        
        heavy_flow = [c for c in cycles if c.flow_level in ["heavy", "very_heavy"]]
        if heavy_flow:
            ratio = len(heavy_flow) / max(len(cycles), 1)
            if ratio > 0.5:
                score += 0.25
                factors.append({"factor": "Heavy periods", "impact": "high"})
        
        return {
            "score": min(0.95, score),
            "confidence": 0.6,
            "factors": factors
        }
    
    def _calculate_thyroid_risk(self, user: UserContext, symptoms: List[Dict]) -> Dict:
        """Calculate thyroid risk indicators."""
        factors = []
        score = 0.1
        
        weight = [s for s in symptoms if "weight" in s.get("symptom_type", "").lower()]
        if len(weight) >= 2:
            score += 0.15
            factors.append({"factor": "Weight changes", "impact": "medium"})
        
        fatigue = [s for s in symptoms if "fatigue" in s.get("symptom_type", "").lower()]
        mood = [s for s in symptoms if s.get("category") == "emotional"]
        
        if len(fatigue) >= 3 and len(mood) >= 3:
            score += 0.2
            factors.append({"factor": "Fatigue + mood changes", "impact": "medium"})
        
        return {
            "score": min(0.95, score),
            "confidence": 0.5,
            "factors": factors
        }


# Singleton instance
femcare_agent = FemCareAgent()
