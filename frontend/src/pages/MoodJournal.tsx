/**
 * Mood Journal Page - Enhanced mood tracking with insights
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Smile,
    TrendingUp,
    Calendar,
    Heart,
    Zap,
    X,
    ChevronRight,
    Award,
    BarChart3,
} from 'lucide-react';
import './MoodJournal.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

interface MoodOption {
    mood: string;
    emoji: string;
    energy: string;
}

interface Trigger {
    id: string;
    label: string;
    emoji: string;
}

interface MoodOptions {
    moods: MoodOption[];
    triggers: Trigger[];
    daily_prompt: string;
}

interface MoodInsights {
    has_insights: boolean;
    mood_distribution?: Array<{ mood: string; emoji: string; percentage: number }>;
    most_common_mood?: { mood: string; emoji: string; percentage: number };
    energy?: { average: number };
    cycle_correlation?: Record<string, { avg_energy: number; dominant_mood: string }>;
    personalized_insights?: string[];
}

export default function MoodJournal() {
    const queryClient = useQueryClient();
    const [showLogModal, setShowLogModal] = useState(false);
    const [selectedMood, setSelectedMood] = useState<MoodOption | null>(null);
    const [energyLevel, setEnergyLevel] = useState(3);
    const [selectedTriggers, setSelectedTriggers] = useState<string[]>([]);
    const [gratitude, setGratitude] = useState('');
    const [notes, setNotes] = useState('');
    const [isLogging, setIsLogging] = useState(false);

    // Fetch mood options
    const { data: options } = useQuery<MoodOptions>({
        queryKey: ['moodOptions'],
        queryFn: async () => {
            const res = await fetch(`${API_BASE_URL}/mood/options`, {
                headers: getAuthHeader()
            });
            return res.json();
        }
    });

    // Fetch today's mood
    const { data: todayMood } = useQuery({
        queryKey: ['todayMood'],
        queryFn: async () => {
            const res = await fetch(`${API_BASE_URL}/mood/today`, {
                headers: getAuthHeader()
            });
            return res.json();
        }
    });

    // Fetch insights
    const { data: insights } = useQuery<MoodInsights>({
        queryKey: ['moodInsights'],
        queryFn: async () => {
            const res = await fetch(`${API_BASE_URL}/mood/insights?days=30`, {
                headers: getAuthHeader()
            });
            return res.json();
        }
    });

    // Fetch streak
    const { data: streak } = useQuery({
        queryKey: ['moodStreak'],
        queryFn: async () => {
            const res = await fetch(`${API_BASE_URL}/mood/streak`, {
                headers: getAuthHeader()
            });
            return res.json();
        }
    });

    const logMood = async () => {
        if (!selectedMood) return;

        setIsLogging(true);
        try {
            const params = new URLSearchParams({
                mood: selectedMood.mood,
                energy_level: energyLevel.toString()
            });

            if (notes) params.append('notes', notes);
            if (gratitude) params.append('gratitude', gratitude);
            if (selectedTriggers.length > 0) {
                params.append('triggers', selectedTriggers.join(','));
            }

            const res = await fetch(`${API_BASE_URL}/mood/log?${params}`, {
                method: 'POST',
                headers: getAuthHeader()
            });

            if (res.ok) {
                queryClient.invalidateQueries({ queryKey: ['todayMood'] });
                queryClient.invalidateQueries({ queryKey: ['moodInsights'] });
                queryClient.invalidateQueries({ queryKey: ['moodStreak'] });
                resetForm();
                setShowLogModal(false);
            }
        } catch (error) {
            console.error('Failed to log mood:', error);
        } finally {
            setIsLogging(false);
        }
    };

    const resetForm = () => {
        setSelectedMood(null);
        setEnergyLevel(3);
        setSelectedTriggers([]);
        setGratitude('');
        setNotes('');
    };

    const toggleTrigger = (triggerId: string) => {
        setSelectedTriggers(prev =>
            prev.includes(triggerId)
                ? prev.filter(t => t !== triggerId)
                : [...prev, triggerId]
        );
    };

    return (
        <div className="mood-journal-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1><Smile size={28} /> Mood Journal</h1>
                    <p>Track your emotional wellbeing</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowLogModal(true)}>
                    <Heart size={18} /> Log Mood
                </button>
            </div>

            {/* Streak Card */}
            {streak && (
                <div className="streak-banner glass">
                    <div className="streak-info">
                        <Award size={32} className="streak-icon" />
                        <div>
                            <span className="streak-count">{streak.current_streak || 0}</span>
                            <span className="streak-label">day streak</span>
                        </div>
                    </div>
                    {streak.current_streak > 0 && (
                        <span className="streak-badge">🔥 Keep it going!</span>
                    )}
                </div>
            )}

            {/* Today's Mood */}
            <div className="today-mood card">
                <div className="card-header">
                    <h3><Calendar size={18} /> Today's Mood</h3>
                </div>
                <div className="card-body">
                    {todayMood?.has_logged_today ? (
                        <div className="mood-entries">
                            {todayMood.entries.map((entry: any) => (
                                <div key={entry.id} className="mood-entry">
                                    <span className="mood-emoji">{entry.emoji}</span>
                                    <div className="mood-details">
                                        <span className="mood-name">{entry.mood}</span>
                                        <span className="mood-energy">
                                            Energy: {'⚡'.repeat(entry.energy_level || 3)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="no-mood">
                            <p>You haven't logged your mood today</p>
                            <button className="btn btn-secondary" onClick={() => setShowLogModal(true)}>
                                Log Now
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Daily Prompt */}
            {options?.daily_prompt && (
                <div className="daily-prompt card glass">
                    <span className="prompt-icon">💭</span>
                    <p className="prompt-text">{options.daily_prompt}</p>
                </div>
            )}

            {/* Mood Distribution */}
            {insights?.has_insights && insights.mood_distribution && (
                <div className="mood-stats card">
                    <div className="card-header">
                        <h3><BarChart3 size={18} /> Mood Distribution (30 days)</h3>
                    </div>
                    <div className="card-body">
                        <div className="mood-bars">
                            {insights.mood_distribution.slice(0, 5).map((item) => (
                                <div key={item.mood} className="mood-bar-item">
                                    <span className="bar-emoji">{item.emoji}</span>
                                    <div className="bar-track">
                                        <div
                                            className="bar-fill"
                                            style={{ width: `${item.percentage}%` }}
                                        ></div>
                                    </div>
                                    <span className="bar-percent">{item.percentage}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Cycle Correlation */}
            {insights?.cycle_correlation && (
                <div className="cycle-mood card">
                    <div className="card-header">
                        <h3><TrendingUp size={18} /> Mood by Cycle Phase</h3>
                    </div>
                    <div className="card-body">
                        <div className="phase-moods">
                            {Object.entries(insights.cycle_correlation).map(([phase, data]) => (
                                <div key={phase} className="phase-mood-item">
                                    <span className="phase-name">{phase}</span>
                                    <span className="phase-dominant">{data.dominant_mood}</span>
                                    <div className="phase-energy">
                                        <Zap size={14} />
                                        <span>{data.avg_energy.toFixed(1)}/5</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Personalized Insights */}
            {insights?.personalized_insights && insights.personalized_insights.length > 0 && (
                <div className="insights-list card">
                    <div className="card-header">
                        <h3>💡 Insights</h3>
                    </div>
                    <div className="card-body">
                        {insights.personalized_insights.map((insight, i) => (
                            <div key={i} className="insight-item">
                                {insight}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Log Mood Modal */}
            {showLogModal && (
                <div className="modal-overlay" onClick={() => setShowLogModal(false)}>
                    <div className="modal mood-modal glass animate-slide-up" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>How are you feeling?</h2>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowLogModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="modal-body">
                            {/* Mood Selection */}
                            <div className="mood-grid">
                                {options?.moods.map((m) => (
                                    <button
                                        key={m.mood}
                                        className={`mood-option ${selectedMood?.mood === m.mood ? 'selected' : ''}`}
                                        onClick={() => setSelectedMood(m)}
                                    >
                                        <span className="mood-option-emoji">{m.emoji}</span>
                                        <span className="mood-option-label">{m.mood}</span>
                                    </button>
                                ))}
                            </div>

                            {/* Energy Level */}
                            <div className="form-group">
                                <label className="form-label">Energy Level</label>
                                <div className="energy-selector">
                                    {[1, 2, 3, 4, 5].map((level) => (
                                        <button
                                            key={level}
                                            className={`energy-btn ${energyLevel >= level ? 'active' : ''}`}
                                            onClick={() => setEnergyLevel(level)}
                                        >
                                            ⚡
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Triggers */}
                            <div className="form-group">
                                <label className="form-label">What's affecting your mood? (optional)</label>
                                <div className="trigger-grid">
                                    {options?.triggers.map((t) => (
                                        <button
                                            key={t.id}
                                            className={`trigger-btn ${selectedTriggers.includes(t.id) ? 'selected' : ''}`}
                                            onClick={() => toggleTrigger(t.id)}
                                        >
                                            <span>{t.emoji}</span>
                                            <span>{t.label}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Gratitude */}
                            <div className="form-group">
                                <label className="form-label">🙏 What are you grateful for today?</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g., My supportive friends..."
                                    value={gratitude}
                                    onChange={(e) => setGratitude(e.target.value)}
                                />
                            </div>

                            {/* Notes */}
                            <div className="form-group">
                                <label className="form-label">Additional notes (optional)</label>
                                <textarea
                                    className="form-input form-textarea"
                                    placeholder="How was your day?"
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowLogModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={logMood}
                                disabled={!selectedMood || isLogging}
                            >
                                {isLogging ? 'Saving...' : 'Save Mood'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
