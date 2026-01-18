/**
 * Family View Page - Public view for family members to see shared data
 * Supports real-time WebSocket updates
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
    Heart,
    Activity,
    Moon,
    Calendar,
    Flame,
    TrendingUp,
    Clock,
    AlertCircle,
    CheckCircle,
    Lightbulb,
    RefreshCw,
    Wifi,
    WifiOff
} from 'lucide-react';
import './FamilyView.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// WebSocket URL - convert http to ws
const getWebSocketUrl = () => {
    const apiUrl = API_BASE_URL.replace('/api', '');
    if (apiUrl.startsWith('https://')) {
        return apiUrl.replace('https://', 'wss://') + '/api';
    } else if (apiUrl.startsWith('http://')) {
        return apiUrl.replace('http://', 'ws://') + '/api';
    }
    // For relative URLs, construct based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/api`;
};

interface SharedData {
    user_name: string;
    relationship: string;
    current_phase: string;
    phase_description: string;
    permissions: Record<string, boolean>;
    mood?: { mood: string; emoji: string; energy_level: number; date: string };
    recent_symptoms?: Array<{ symptom: string; severity: number; date: string }>;
    exercise?: { recent: Array<any>; current_streak: number };
    cycle?: {
        current_day: number;
        predicted_next: string | null;
        days_until_period: number;
        is_on_period: boolean;
        period_days_remaining: number;
        flow_level: string;
        avg_cycle_length: number;
        avg_period_length: number;
        phase_info: string;
        start_date: string;
    };
    water?: { today_ml: number; goal_ml: number; percent: number };
    nutrition?: {
        today_calories: number;
        goal_calories: number;
        protein: number;
        carbs: number;
        fat: number;
        meals_logged: number;
    };
    weekly_summary?: {
        exercise_days: number;
        avg_water_percent: number;
        avg_calories: number;
        mood_trend: string;
    };
    last_updated: string;
}

interface CareSuggestion {
    type: string;
    title: string;
    description: string;
    priority: number;
}

const phaseEmojis: Record<string, string> = {
    menstrual: '🌙',
    follicular: '🌱',
    ovulation: '🌸',
    luteal: '🍂',
    late_luteal: '⛈️',
    unknown: '❓'
};

const phaseColors: Record<string, string> = {
    menstrual: '#e74c3c',
    follicular: '#2ecc71',
    ovulation: '#f39c12',
    luteal: '#9b59b6',
    late_luteal: '#8e44ad',
    unknown: '#95a5a6'
};

export default function FamilyView() {
    const { inviteCode } = useParams<{ inviteCode: string }>();
    const [sharedData, setSharedData] = useState<SharedData | null>(null);
    const [careSuggestions, setCareSuggestions] = useState<CareSuggestion[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [inviteAccepted, setInviteAccepted] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // WebSocket connection
    const connectWebSocket = useCallback(() => {
        if (!inviteCode || !inviteAccepted) return;

        const wsUrl = `${getWebSocketUrl()}/family/realtime/${inviteCode}`;
        console.log('Connecting WebSocket to:', wsUrl);

        try {
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                console.log('✅ WebSocket connected - Real-time updates active');
                setIsConnected(true);
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📩 Real-time update received:', data);

                    if (data.type === 'health_update') {
                        // Update shared data with new info
                        setSharedData(prev => prev ? { ...prev, ...data.data, last_updated: new Date().toISOString() } : prev);
                        setLastUpdate(new Date());
                    } else if (data.type === 'care_suggestions') {
                        setCareSuggestions(data.suggestions || []);
                    }
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            wsRef.current.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);
                // Attempt reconnect after 5 seconds
                reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
            };

            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setIsConnected(false);
            };
        } catch (e) {
            console.error('Failed to create WebSocket:', e);
        }
    }, [inviteCode, inviteAccepted]);

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, []);

    // Connect WebSocket when invite is accepted
    useEffect(() => {
        if (inviteAccepted && inviteCode) {
            connectWebSocket();
        }
    }, [inviteAccepted, inviteCode, connectWebSocket]);

    useEffect(() => {
        if (inviteCode) {
            fetchSharedData();
            fetchCareSuggestions();
        }
    }, [inviteCode]);

    const fetchSharedData = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/family/shared/${inviteCode}`);
            const data = await response.json();

            if (data.status === 'pending') {
                setInviteAccepted(false);
            } else {
                setInviteAccepted(true);
                setSharedData(data);
            }
        } catch (err) {
            setError('Failed to load shared data');
        } finally {
            setLoading(false);
        }
    };

    const fetchCareSuggestions = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/family/care-suggestions/${inviteCode}`);
            if (response.ok) {
                const data = await response.json();
                setCareSuggestions(data.suggestions || []);
            }
        } catch (err) {
            console.error('Failed to fetch care suggestions');
        }
    };

    const acceptInvite = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/family/accept-invite/${inviteCode}`, {
                method: 'POST'
            });
            if (response.ok) {
                setInviteAccepted(true);
                fetchSharedData();
            }
        } catch (err) {
            setError('Failed to accept invite');
        }
    };

    if (loading) {
        return (
            <div className="family-view-page">
                <div className="loading-state">
                    <RefreshCw size={32} className="spin" />
                    <p>Loading health data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="family-view-page">
                <div className="error-state">
                    <AlertCircle size={48} />
                    <h2>Oops!</h2>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (!inviteAccepted) {
        return (
            <div className="family-view-page">
                <div className="accept-invite-card">
                    <Heart size={48} className="heart-icon" />
                    <h2>You've Been Invited</h2>
                    <p>Someone wants to share their health journey with you.</p>
                    <p className="privacy-note">
                        By accepting, you'll receive updates about their well-being and
                        personalized suggestions on how to support them.
                    </p>
                    <button className="btn btn-primary btn-lg" onClick={acceptInvite}>
                        <CheckCircle size={20} /> Accept Invitation
                    </button>
                </div>
            </div>
        );
    }

    if (!sharedData) return null;

    return (
        <div className="family-view-page">
            {/* Connection Status Banner */}
            <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
                {isConnected ? (
                    <>
                        <Wifi size={14} />
                        <span>Live Updates Active</span>
                        {lastUpdate && <span className="last-update">• Updated {lastUpdate.toLocaleTimeString()}</span>}
                    </>
                ) : (
                    <>
                        <WifiOff size={14} />
                        <span>Connecting...</span>
                    </>
                )}
            </div>

            {/* Header */}
            <div className="fv-header">
                <div className="fv-avatar">
                    <Heart size={28} />
                </div>
                <div className="fv-info">
                    <h1>{sharedData.user_name}'s Health</h1>
                    <p>You're viewing as {sharedData.relationship}</p>
                </div>
                <button className="refresh-btn" onClick={fetchSharedData}>
                    <RefreshCw size={20} />
                </button>
            </div>

            {/* Current Phase */}
            <div
                className="phase-card"
                style={{ borderColor: phaseColors[sharedData.current_phase] }}
            >
                <div className="phase-emoji">{phaseEmojis[sharedData.current_phase]}</div>
                <div className="phase-info">
                    <h2>{sharedData.current_phase.replace('_', ' ')} Phase</h2>
                    <p>{sharedData.phase_description}</p>
                </div>
            </div>

            {/* Mood */}
            {sharedData.permissions.can_view_mood && sharedData.mood && (
                <div className="data-card mood-card">
                    <div className="card-header">
                        <Moon size={20} />
                        <h3>Current Mood</h3>
                    </div>
                    <div className="mood-display">
                        <span className="mood-emoji">{sharedData.mood.emoji}</span>
                        <span className="mood-name">{sharedData.mood.mood}</span>
                    </div>
                    <div className="energy-bar">
                        <span>Energy Level</span>
                        <div className="bar">
                            <div
                                className="fill"
                                style={{ width: `${(sharedData.mood.energy_level / 5) * 100}%` }}
                            />
                        </div>
                        <span>{sharedData.mood.energy_level}/5</span>
                    </div>
                </div>
            )}

            {/* Symptoms */}
            {sharedData.permissions.can_view_symptoms && sharedData.recent_symptoms && sharedData.recent_symptoms.length > 0 && (
                <div className="data-card symptoms-card">
                    <div className="card-header">
                        <Activity size={20} />
                        <h3>Recent Symptoms</h3>
                    </div>
                    <div className="symptoms-list">
                        {sharedData.recent_symptoms.map((symptom, i) => (
                            <div key={i} className="symptom-item">
                                <span className="symptom-name">{symptom.symptom}</span>
                                <div className="severity-dots">
                                    {[1, 2, 3, 4, 5].map(level => (
                                        <span
                                            key={level}
                                            className={`dot ${level <= symptom.severity ? 'filled' : ''}`}
                                        />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Exercise */}
            {sharedData.permissions.can_view_exercise && sharedData.exercise && (
                <div className="data-card exercise-card">
                    <div className="card-header">
                        <Flame size={20} />
                        <h3>Exercise Activity</h3>
                    </div>
                    <div className="streak-display">
                        <TrendingUp size={24} />
                        <span className="streak-number">{sharedData.exercise.current_streak}</span>
                        <span className="streak-label">Day Streak!</span>
                    </div>
                    {sharedData.exercise.recent.length > 0 && (
                        <div className="recent-exercises">
                            {sharedData.exercise.recent.slice(0, 3).map((ex, i) => (
                                <div key={i} className="exercise-item">
                                    <span className="ex-name">{ex.name}</span>
                                    <span className="ex-meta">
                                        <Clock size={12} /> {ex.duration} min
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Cycle Info - ENHANCED */}
            {sharedData.permissions.can_view_cycle && sharedData.cycle && (
                <div className="data-card cycle-card">
                    <div className="card-header">
                        <Calendar size={20} />
                        <h3>Cycle Status</h3>
                    </div>

                    {/* Period Status Banner */}
                    {sharedData.cycle.is_on_period && (
                        <div className="period-banner">
                            <span className="period-emoji">🩸</span>
                            <div className="period-info">
                                <strong>Currently on Period</strong>
                                <span>{sharedData.cycle.period_days_remaining} days remaining</span>
                            </div>
                        </div>
                    )}

                    <div className="cycle-details-grid">
                        <div className="cycle-stat">
                            <span className="stat-value">{sharedData.cycle.current_day}</span>
                            <span className="stat-label">Cycle Day</span>
                        </div>
                        <div className="cycle-stat">
                            <span className="stat-value">{sharedData.cycle.days_until_period || '—'}</span>
                            <span className="stat-label">Days to Period</span>
                        </div>
                        <div className="cycle-stat">
                            <span className="stat-value">{sharedData.cycle.flow_level || '—'}</span>
                            <span className="stat-label">Flow Level</span>
                        </div>
                        <div className="cycle-stat">
                            <span className="stat-value">{sharedData.cycle.avg_cycle_length}</span>
                            <span className="stat-label">Avg Cycle</span>
                        </div>
                    </div>

                    <div className="phase-insight">
                        <Lightbulb size={16} />
                        <span>{sharedData.cycle.phase_info}</span>
                    </div>

                    {sharedData.cycle.predicted_next && (
                        <p className="next-period">
                            📅 Next period expected: {new Date(sharedData.cycle.predicted_next).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                    )}
                </div>
            )}

            {/* Water Tracking */}
            {sharedData.water && (
                <div className="data-card water-card">
                    <div className="card-header">
                        <span className="water-icon">💧</span>
                        <h3>Today's Hydration</h3>
                    </div>
                    <div className="water-visual">
                        <div className="water-glass">
                            <div
                                className="water-fill"
                                style={{ height: `${Math.min(sharedData.water.percent, 100)}%` }}
                            />
                            <span className="water-percent">{sharedData.water.percent}%</span>
                        </div>
                        <div className="water-stats">
                            <div className="water-amount">
                                <span className="amount">{sharedData.water.today_ml}</span>
                                <span className="unit">ml</span>
                            </div>
                            <div className="water-goal">
                                of {sharedData.water.goal_ml}ml goal
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Nutrition Tracking */}
            {sharedData.permissions.can_view_nutrition && sharedData.nutrition && (
                <div className="data-card nutrition-card">
                    <div className="card-header">
                        <span className="nutrition-icon">🍎</span>
                        <h3>Today's Nutrition</h3>
                    </div>
                    <div className="nutrition-content">
                        {/* Calorie Ring */}
                        <div className="calorie-ring-container">
                            <svg className="calorie-ring" viewBox="0 0 120 120">
                                <circle className="ring-bg" cx="60" cy="60" r="50" />
                                <circle
                                    className="ring-fill"
                                    cx="60" cy="60" r="50"
                                    style={{
                                        strokeDasharray: `${(sharedData.nutrition.today_calories / sharedData.nutrition.goal_calories) * 314} 314`
                                    }}
                                />
                            </svg>
                            <div className="calorie-text">
                                <span className="cal-amount">{sharedData.nutrition.today_calories}</span>
                                <span className="cal-label">kcal</span>
                            </div>
                        </div>

                        {/* Macro Bars */}
                        <div className="macro-bars">
                            <div className="macro-item">
                                <span className="macro-label">Protein</span>
                                <div className="macro-bar">
                                    <div className="macro-fill protein" style={{ width: `${Math.min((sharedData.nutrition.protein / 50) * 100, 100)}%` }} />
                                </div>
                                <span className="macro-value">{sharedData.nutrition.protein}g</span>
                            </div>
                            <div className="macro-item">
                                <span className="macro-label">Carbs</span>
                                <div className="macro-bar">
                                    <div className="macro-fill carbs" style={{ width: `${Math.min((sharedData.nutrition.carbs / 200) * 100, 100)}%` }} />
                                </div>
                                <span className="macro-value">{sharedData.nutrition.carbs}g</span>
                            </div>
                            <div className="macro-item">
                                <span className="macro-label">Fat</span>
                                <div className="macro-bar">
                                    <div className="macro-fill fat" style={{ width: `${Math.min((sharedData.nutrition.fat / 65) * 100, 100)}%` }} />
                                </div>
                                <span className="macro-value">{sharedData.nutrition.fat}g</span>
                            </div>
                        </div>
                        <div className="meals-logged">
                            {sharedData.nutrition.meals_logged} meals logged today
                        </div>
                    </div>
                </div>
            )}

            {/* Weekly Summary */}
            {sharedData.weekly_summary && (
                <div className="data-card summary-card">
                    <div className="card-header">
                        <TrendingUp size={20} />
                        <h3>This Week's Overview</h3>
                    </div>
                    <div className="weekly-stats-grid">
                        <div className="weekly-stat">
                            <span className="stat-icon">🏃‍♀️</span>
                            <span className="stat-value">{sharedData.weekly_summary.exercise_days}</span>
                            <span className="stat-label">Active Days</span>
                        </div>
                        <div className="weekly-stat">
                            <span className="stat-icon">💧</span>
                            <span className="stat-value">{sharedData.weekly_summary.avg_water_percent}%</span>
                            <span className="stat-label">Avg Hydration</span>
                        </div>
                        <div className="weekly-stat">
                            <span className="stat-icon">🔥</span>
                            <span className="stat-value">{sharedData.weekly_summary.avg_calories}</span>
                            <span className="stat-label">Avg Calories</span>
                        </div>
                        <div className="weekly-stat">
                            <span className="stat-icon">😊</span>
                            <span className="stat-value">{sharedData.weekly_summary.mood_trend}</span>
                            <span className="stat-label">Mood Trend</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Care Suggestions */}
            {careSuggestions.length > 0 && (
                <div className="care-suggestions-section">
                    <h2><Lightbulb size={24} /> How You Can Help</h2>
                    <div className="suggestions-list">
                        {careSuggestions.map((suggestion, i) => (
                            <div key={i} className={`suggestion-card priority-${suggestion.priority >= 8 ? 'high' : suggestion.priority >= 5 ? 'medium' : 'low'}`}>
                                <div className="suggestion-type">{suggestion.type.replace('_', ' ')}</div>
                                <h3>{suggestion.title}</h3>
                                <p>{suggestion.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Last Updated */}
            <div className="last-updated">
                Last updated: {new Date(sharedData.last_updated).toLocaleString()}
            </div>
        </div>
    );
}
