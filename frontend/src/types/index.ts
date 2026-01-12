/**
 * TypeScript type definitions for FemCare AI
 */

// ============== User Types ==============

export interface User {
    id: number;
    email: string;
    name: string;
    date_of_birth?: string;
    weight?: number;
    height?: number;
    has_given_birth: boolean;
    is_pregnant: boolean;
    is_trying_to_conceive: boolean;
    is_on_birth_control: boolean;
    medical_conditions: string[];
    notification_enabled: boolean;
    partner_sharing_enabled: boolean;
    created_at: string;
}

export interface UserUpdate {
    name?: string;
    date_of_birth?: string;
    weight?: number;
    height?: number;
    has_given_birth?: boolean;
    is_pregnant?: boolean;
    is_trying_to_conceive?: boolean;
    is_on_birth_control?: boolean;
    medical_conditions?: string[];
    notification_enabled?: boolean;
    partner_sharing_enabled?: boolean;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterData extends LoginCredentials {
    name: string;
}

export interface AuthToken {
    access_token: string;
    token_type: string;
}

// ============== Cycle Types ==============

export type FlowLevel = 'spotting' | 'light' | 'medium' | 'heavy' | 'very_heavy';

export interface CycleEntry {
    id: number;
    user_id: number;
    start_date: string;
    end_date?: string;
    cycle_length?: number;
    period_length?: number;
    flow_level: FlowLevel;
    ovulation_date?: string;
    notes?: string;
    predicted_next_start?: string;
    prediction_confidence?: number;
    created_at: string;
}

export interface CycleCreate {
    start_date: string;
    end_date?: string;
    flow_level: FlowLevel;
    notes?: string;
}

export interface CyclePrediction {
    next_period_start: string;
    next_period_end: string;
    next_ovulation?: string;
    fertile_window_start?: string;
    fertile_window_end?: string;
    confidence: number;
    average_cycle_length: number;
    average_period_length: number;
}

export interface CyclePatterns {
    average_cycle_length: number;
    cycle_length_std: number;
    average_period_length: number;
    is_regular: boolean;
    regularity_score: number;
    total_cycles_tracked: number;
    longest_cycle: number;
    shortest_cycle: number;
    common_symptoms: Array<{
        symptom: string;
        count: number;
        avg_severity: number;
    }>;
    cycle_phase_patterns: Record<string, { typical_days: string }>;
}

export interface CurrentCycle {
    has_data: boolean;
    cycle_day?: number;
    phase?: CyclePhase;
    phase_description?: string;
    days_until_period?: number;
    predicted_next_start?: string;
    prediction_confidence?: number;
    average_cycle_length?: number;
    is_fertile_window?: boolean;
    fertile_window?: {
        start: string;
        end: string;
    };
    message?: string;
}

export type CyclePhase = 'menstrual' | 'follicular' | 'ovulation' | 'luteal' | 'late_luteal';

// ============== Symptom Types ==============

export type SymptomCategory = 'physical' | 'emotional' | 'hormonal' | 'reproductive' | 'digestive' | 'other';

export interface Symptom {
    id: number;
    user_id: number;
    cycle_id?: number;
    date: string;
    symptom_type: string;
    category: SymptomCategory;
    severity: number;
    description?: string;
    duration_hours?: number;
    ai_classification?: Record<string, unknown>;
    created_at: string;
}

export interface SymptomCreate {
    date: string;
    symptom_type: string;
    category: SymptomCategory;
    severity: number;
    description?: string;
    duration_hours?: number;
    cycle_id?: number;
}

export interface SymptomAnalysis {
    total_symptoms: number;
    symptoms_by_category: Record<string, number>;
    average_severity: number;
    most_common: Array<{
        symptom: string;
        count: number;
        avg_severity: number;
    }>;
    severity_trend: 'improving' | 'stable' | 'worsening';
    correlations: Array<{
        symptoms: string[];
        co_occurrence_count: number;
        insight: string;
    }>;
    recommendations: string[];
}

export interface SymptomTypes {
    physical: string[];
    emotional: string[];
    hormonal: string[];
    reproductive: string[];
    digestive: string[];
}

// ============== Risk & Insights Types ==============

export type ConditionType = 'pcos' | 'endometriosis' | 'anemia' | 'thyroid';

export interface RiskScore {
    score: number;
    confidence: number;
    factors: Array<{
        factor: string;
        value?: string;
        impact: 'low' | 'medium' | 'high';
    }>;
}

export interface RiskAssessment {
    pcos: RiskScore;
    endometriosis: RiskScore;
    anemia: RiskScore;
    thyroid: RiskScore;
    overall_health_score: number;
    priority_concerns: string[];
    calculated_at: string;
}

export interface HealthInsight {
    id: number;
    user_id: number;
    insight_type: 'pattern' | 'alert' | 'tip' | 'correlation';
    title: string;
    content: string;
    priority: 'low' | 'normal' | 'high' | 'urgent';
    is_read: boolean;
    is_dismissed: boolean;
    related_conditions: string[];
    evidence: Array<Record<string, unknown>>;
    created_at: string;
}

export interface Recommendation {
    id: number;
    user_id: number;
    category: string;
    title: string;
    description: string;
    priority: number;
    is_completed: boolean;
    completed_at?: string;
    action_steps: string[];
    expected_duration?: string;
    reason?: string;
    created_at: string;
}

// ============== Timeline Types ==============

export interface TimelineEvent {
    id: number;
    event_type: 'cycle_start' | 'cycle_end' | 'symptom' | 'insight' | 'recommendation';
    date: string;
    title: string;
    description?: string;
    metadata: Record<string, unknown>;
}

export interface HealthTimeline {
    events: TimelineEvent[];
    start_date: string;
    end_date: string;
    patterns_detected: Array<Record<string, unknown>>;
    correlations: Array<Record<string, unknown>>;
}

// ============== Chat Types ==============

export interface ChatMessage {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    intent?: string;
    actions_taken?: Array<Record<string, unknown>>;
    confidence?: number;
    created_at: string;
}

// ============== Dashboard Types ==============

export interface DashboardSummary {
    current_cycle_day?: number;
    days_until_next_period?: number;
    current_phase?: CyclePhase;
    recent_symptoms: Symptom[];
    risk_summary: Record<ConditionType, number>;
    unread_insights: number;
    pending_recommendations: number;
    current_streak: number;
    health_score: number;
}

// ============== Gamification Types ==============

export interface HealthStreak {
    id: number;
    streak_type: string;
    current_streak: number;
    longest_streak: number;
    last_activity_date?: string;
    total_activities: number;
}

export interface Achievement {
    id: number;
    achievement_type: string;
    title: string;
    description?: string;
    icon?: string;
    earned_at: string;
}

// ============== Education Types ==============

export interface EducationArticle {
    id: number;
    title: string;
    summary: string;
    content: string;
    category: string;
    tags: string[];
    is_myth_busting: boolean;
    difficulty_level: 'beginner' | 'intermediate' | 'advanced';
    reading_time_minutes: number;
    sources: string[];
}

// ============== API Response Types ==============

export interface ApiError {
    detail: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}
