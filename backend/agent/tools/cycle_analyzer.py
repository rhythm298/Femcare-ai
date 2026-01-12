"""
Cycle Analyzer Tool for FemCare AI Agent.
Analyzes menstrual cycle patterns, detects irregularities, and predicts future cycles.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class CycleData:
    """Represents a single menstrual cycle entry."""
    start_date: date
    end_date: Optional[date] = None
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None
    flow_level: str = "medium"


class CycleAnalyzer:
    """
    Analyzes menstrual cycle patterns and provides predictions.
    Uses statistical analysis and weighted moving averages.
    """
    
    # Normal cycle range according to medical guidelines
    MIN_NORMAL_CYCLE = 21
    MAX_NORMAL_CYCLE = 35
    IDEAL_CYCLE = 28
    
    def __init__(self):
        self.min_cycles_for_prediction = 2
        self.min_cycles_for_confidence = 6
    
    def analyze(self, cycles: List[CycleData]) -> Dict:
        """
        Comprehensive cycle analysis.
        
        Returns:
            Dict containing:
            - average_length: float
            - std_deviation: float
            - is_regular: bool
            - regularity_score: float (0-1)
            - irregularity_reasons: List[str]
            - next_prediction: date
            - prediction_confidence: float
            - ovulation_estimate: date
            - fertile_window: Tuple[date, date]
            - phase_info: Dict
        """
        if not cycles:
            return self._empty_analysis()
        
        # Sort cycles by date
        sorted_cycles = sorted(cycles, key=lambda c: c.start_date)
        
        # Calculate cycle lengths
        cycle_lengths = self._calculate_cycle_lengths(sorted_cycles)
        
        if not cycle_lengths:
            return self._minimum_analysis(sorted_cycles[-1])
        
        # Statistical analysis
        avg_length = np.mean(cycle_lengths)
        std_dev = np.std(cycle_lengths) if len(cycle_lengths) > 1 else 0
        
        # Regularity assessment
        regularity = self._assess_regularity(cycle_lengths, avg_length, std_dev)
        
        # Prediction
        prediction = self._predict_next_cycle(sorted_cycles, cycle_lengths)
        
        # Fertility analysis
        fertility = self._analyze_fertility(sorted_cycles[-1], avg_length)
        
        # Current phase
        phase = self._determine_current_phase(sorted_cycles[-1], avg_length)
        
        # Period length analysis
        period_analysis = self._analyze_period_lengths(sorted_cycles)
        
        return {
            "average_cycle_length": round(avg_length, 1),
            "std_deviation": round(std_dev, 1),
            "is_regular": regularity["is_regular"],
            "regularity_score": regularity["score"],
            "irregularity_reasons": regularity["reasons"],
            "next_prediction": prediction["date"],
            "prediction_confidence": prediction["confidence"],
            "prediction_range": prediction["range"],
            "ovulation_estimate": fertility["ovulation_date"],
            "fertile_window": fertility["fertile_window"],
            "current_phase": phase["phase"],
            "cycle_day": phase["day"],
            "phase_description": phase["description"],
            "average_period_length": period_analysis["average"],
            "total_cycles_analyzed": len(cycle_lengths),
            "longest_cycle": max(cycle_lengths),
            "shortest_cycle": min(cycle_lengths),
            "cycle_lengths": cycle_lengths[-6:],  # Last 6 for visualization
            "insights": self._generate_insights(cycle_lengths, regularity, period_analysis)
        }
    
    def _calculate_cycle_lengths(self, sorted_cycles: List[CycleData]) -> List[int]:
        """Calculate cycle lengths from consecutive cycles."""
        lengths = []
        for i in range(1, len(sorted_cycles)):
            length = (sorted_cycles[i].start_date - sorted_cycles[i-1].start_date).days
            # Filter unrealistic values
            if 15 <= length <= 60:
                lengths.append(length)
        return lengths
    
    def _assess_regularity(self, lengths: List[int], avg: float, std: float) -> Dict:
        """Assess cycle regularity based on medical criteria."""
        reasons = []
        score = 1.0
        
        # Check variability
        if std > 7:
            score -= 0.3
            reasons.append(f"High cycle variability (±{std:.1f} days)")
        elif std > 4:
            score -= 0.1
        
        # Check if cycles are in normal range
        out_of_range = [l for l in lengths if l < self.MIN_NORMAL_CYCLE or l > self.MAX_NORMAL_CYCLE]
        if out_of_range:
            ratio = len(out_of_range) / len(lengths)
            score -= ratio * 0.4
            if any(l < self.MIN_NORMAL_CYCLE for l in lengths):
                reasons.append("Some cycles are shorter than 21 days (possible anovulation)")
            if any(l > self.MAX_NORMAL_CYCLE for l in lengths):
                reasons.append("Some cycles are longer than 35 days (extended cycles)")
        
        # Check for extreme values
        if lengths:
            range_span = max(lengths) - min(lengths)
            if range_span > 14:
                score -= 0.2
                reasons.append(f"Large variation between shortest and longest cycle ({range_span} days)")
        
        score = max(0, min(1, score))
        
        return {
            "is_regular": score >= 0.7 and std <= 7,
            "score": round(score, 2),
            "reasons": reasons if reasons else ["Your cycles appear regular!"]
        }
    
    def _predict_next_cycle(self, sorted_cycles: List[CycleData], lengths: List[int]) -> Dict:
        """Predict next cycle using weighted moving average."""
        last_cycle = sorted_cycles[-1]
        
        if not lengths:
            # No historical data, use default
            predicted_date = last_cycle.start_date + timedelta(days=self.IDEAL_CYCLE)
            return {
                "date": predicted_date,
                "confidence": 0.3,
                "range": (predicted_date - timedelta(days=5), predicted_date + timedelta(days=5))
            }
        
        # Weighted moving average (recent cycles weighted more)
        weights = np.array([i + 1 for i in range(len(lengths))])
        weights = weights / weights.sum()
        avg_length = np.average(lengths, weights=weights)
        
        # Confidence calculation
        std = np.std(lengths)
        consistency_score = max(0, 1 - (std / 10))
        sample_score = min(1, len(lengths) / self.min_cycles_for_confidence)
        confidence = (consistency_score * 0.6 + sample_score * 0.4)
        
        predicted_date = last_cycle.start_date + timedelta(days=round(avg_length))
        
        # Prediction range based on std
        margin = max(2, round(std))
        range_start = predicted_date - timedelta(days=margin)
        range_end = predicted_date + timedelta(days=margin)
        
        return {
            "date": predicted_date,
            "confidence": round(confidence, 2),
            "range": (range_start, range_end)
        }
    
    def _analyze_fertility(self, last_cycle: CycleData, avg_length: float) -> Dict:
        """Estimate ovulation and fertile window."""
        # Ovulation typically occurs 14 days before next period
        ovulation_day = round(avg_length - 14)
        ovulation_date = last_cycle.start_date + timedelta(days=ovulation_day)
        
        # Fertile window: 5 days before ovulation to 1 day after
        fertile_start = ovulation_date - timedelta(days=5)
        fertile_end = ovulation_date + timedelta(days=1)
        
        return {
            "ovulation_date": ovulation_date,
            "fertile_window": (fertile_start, fertile_end),
            "ovulation_day_of_cycle": ovulation_day
        }
    
    def _determine_current_phase(self, last_cycle: CycleData, avg_length: float) -> Dict:
        """Determine current menstrual cycle phase."""
        today = date.today()
        cycle_day = (today - last_cycle.start_date).days + 1
        
        # Standard phase breakdown (adjustable based on cycle length)
        if cycle_day <= 5:
            phase = "menstrual"
            description = "Menstruation Phase - Your body is shedding the uterine lining. Rest is important."
        elif cycle_day <= 13:
            phase = "follicular"
            description = "Follicular Phase - Estrogen rises, energy typically increases. Great time for new projects!"
        elif cycle_day <= 16:
            phase = "ovulation"
            description = "Ovulation Phase - Peak fertility. You may feel more social and energetic."
        elif cycle_day <= round(avg_length):
            phase = "luteal"
            description = "Luteal Phase - Progesterone rises. PMS symptoms may appear towards the end."
        else:
            phase = "late_luteal"
            description = "Late Luteal Phase - Your period may start soon. Practice self-care."
        
        return {
            "phase": phase,
            "day": cycle_day,
            "description": description
        }
    
    def _analyze_period_lengths(self, cycles: List[CycleData]) -> Dict:
        """Analyze period (bleeding) durations."""
        period_lengths = [c.period_length for c in cycles if c.period_length]
        
        if not period_lengths:
            return {"average": 5, "std": 0, "trend": "unknown"}
        
        avg = np.mean(period_lengths)
        std = np.std(period_lengths) if len(period_lengths) > 1 else 0
        
        # Trend analysis
        if len(period_lengths) >= 3:
            recent = np.mean(period_lengths[-2:])
            earlier = np.mean(period_lengths[:-2])
            if recent > earlier + 0.5:
                trend = "increasing"
            elif recent < earlier - 0.5:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "unknown"
        
        return {
            "average": round(avg, 1),
            "std": round(std, 1),
            "trend": trend
        }
    
    def _generate_insights(self, lengths: List[int], regularity: Dict, period: Dict) -> List[str]:
        """Generate actionable insights based on analysis."""
        insights = []
        
        # Regularity insights
        if regularity["is_regular"]:
            insights.append("✅ Your cycle is regular, which is a positive sign of hormonal balance.")
        else:
            insights.append("📊 Your cycle shows some variability. Track consistently to identify patterns.")
        
        # Length insights
        if lengths:
            avg = np.mean(lengths)
            if avg > 35:
                insights.append("⚠️ Your cycles tend to be longer than average. This could indicate PCOS or other hormonal factors.")
            elif avg < 21:
                insights.append("⚠️ Your cycles are shorter than typical. Consider discussing with a healthcare provider.")
            else:
                insights.append(f"📅 Your average cycle length of {avg:.0f} days is within the normal range.")
        
        # Period length insights
        if period["average"] > 7:
            insights.append("🩸 Your periods tend to be longer than average. Monitor for heavy bleeding.")
        
        return insights
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis when no data available."""
        return {
            "average_cycle_length": None,
            "std_deviation": None,
            "is_regular": None,
            "regularity_score": 0,
            "irregularity_reasons": ["No cycle data available"],
            "next_prediction": None,
            "prediction_confidence": 0,
            "insights": ["Start tracking your cycles to get personalized insights!"]
        }
    
    def _minimum_analysis(self, last_cycle: CycleData) -> Dict:
        """Return minimal analysis with only one cycle."""
        predicted = last_cycle.start_date + timedelta(days=self.IDEAL_CYCLE)
        return {
            "average_cycle_length": self.IDEAL_CYCLE,
            "std_deviation": 0,
            "is_regular": None,
            "regularity_score": 0.5,
            "irregularity_reasons": ["Need more data for accurate analysis"],
            "next_prediction": predicted,
            "prediction_confidence": 0.3,
            "current_phase": self._determine_current_phase(last_cycle, self.IDEAL_CYCLE),
            "insights": ["Track at least 3 cycles for accurate predictions."]
        }


# Singleton instance
cycle_analyzer = CycleAnalyzer()
