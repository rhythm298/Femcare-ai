/**
 * Activity Page - Exercise suggestions and logging
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Activity as ActivityIcon,
    Play,
    Clock,
    Flame,
    Calendar,
    Trophy,
    ChevronRight,
    Star,
    TrendingUp,
    Youtube,
    X,
    Check
} from 'lucide-react';
import './Activity.css';

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const activityApi = {
    getSuggestions: async () => {
        const response = await fetch(`${API_BASE_URL}/activity/suggestions`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch suggestions');
        return response.json();
    },
    getExercises: async (params?: { category?: string; search?: string }) => {
        const searchParams = new URLSearchParams();
        if (params?.category) searchParams.set('category', params.category);
        if (params?.search) searchParams.set('search', params.search);
        const response = await fetch(`${API_BASE_URL}/activity/exercises?${searchParams}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch exercises');
        return response.json();
    },
    logExercise: async (data: {
        exercise_name: string;
        duration_minutes: number;
        exercise_id?: number;
        intensity?: string;
        notes?: string;
        youtube_video_watched?: string;
    }) => {
        const params = new URLSearchParams();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined) params.set(key, String(value));
        });
        const response = await fetch(`${API_BASE_URL}/activity/log?${params}`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to log exercise');
        return response.json();
    },
    getLogs: async () => {
        const response = await fetch(`${API_BASE_URL}/activity/logs`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch logs');
        return response.json();
    },
    getStats: async () => {
        const response = await fetch(`${API_BASE_URL}/activity/stats`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch stats');
        return response.json();
    }
};

interface Exercise {
    id: number;
    name: string;
    category: string;
    intensity_level: string;
    duration_minutes: number;
    description: string;
    benefits: string;
    instructions: string[];
    youtube_video_id: string;
    youtube_video_title: string;
    youtube_url: string;
    calories_per_minute: number;
}

const phaseColors: Record<string, string> = {
    menstrual: 'var(--color-menstrual)',
    follicular: 'var(--color-follicular)',
    ovulation: 'var(--color-ovulation)',
    luteal: 'var(--color-luteal)'
};

const intensityColors: Record<string, string> = {
    low: '#4ade80',
    medium: '#fbbf24',
    high: '#f87171'
};

export default function Activity() {
    const queryClient = useQueryClient();
    const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);
    const [showVideoModal, setShowVideoModal] = useState(false);
    const [showLogModal, setShowLogModal] = useState(false);
    const [logDuration, setLogDuration] = useState(30);
    const [logNotes, setLogNotes] = useState('');
    const [activeCategory, setActiveCategory] = useState<string | null>(null);

    const { data: suggestions, isLoading: suggestionsLoading } = useQuery({
        queryKey: ['activitySuggestions'],
        queryFn: activityApi.getSuggestions
    });

    const { data: allExercises } = useQuery({
        queryKey: ['exercises', activeCategory],
        queryFn: () => activityApi.getExercises({ category: activeCategory || undefined })
    });

    const { data: stats } = useQuery({
        queryKey: ['exerciseStats'],
        queryFn: activityApi.getStats
    });

    const { data: logs } = useQuery({
        queryKey: ['exerciseLogs'],
        queryFn: activityApi.getLogs
    });

    const logMutation = useMutation({
        mutationFn: activityApi.logExercise,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['exerciseLogs'] });
            queryClient.invalidateQueries({ queryKey: ['exerciseStats'] });
            setShowLogModal(false);
            setSelectedExercise(null);
            setLogDuration(30);
            setLogNotes('');
        }
    });

    const handleWatchVideo = (exercise: Exercise) => {
        setSelectedExercise(exercise);
        setShowVideoModal(true);
    };

    const handleLogExercise = (exercise: Exercise) => {
        setSelectedExercise(exercise);
        setLogDuration(exercise.duration_minutes);
        setShowLogModal(true);
    };

    const submitLog = () => {
        if (!selectedExercise) return;
        logMutation.mutate({
            exercise_name: selectedExercise.name,
            duration_minutes: logDuration,
            exercise_id: selectedExercise.id,
            intensity: selectedExercise.intensity_level,
            notes: logNotes || undefined,
            youtube_video_watched: showVideoModal ? selectedExercise.youtube_video_id : undefined
        });
    };

    const categories = [
        { id: 'yoga', name: 'Yoga', emoji: '🧘' },
        { id: 'cardio', name: 'Cardio', emoji: '🏃' },
        { id: 'strength', name: 'Strength', emoji: '💪' },
        { id: 'stretching', name: 'Stretching', emoji: '🤸' },
        { id: 'meditation', name: 'Meditation', emoji: '🧠' },
        { id: 'dance', name: 'Dance', emoji: '💃' }
    ];

    if (suggestionsLoading) {
        return (
            <div className="activity-page">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading exercise suggestions...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="activity-page animate-fade-in">
            {/* Header */}
            <div className="activity-header">
                <div>
                    <h1><ActivityIcon size={28} /> Activity & Exercise</h1>
                    <p className="phase-indicator" style={{ color: phaseColors[suggestions?.current_phase] }}>
                        {suggestions?.current_phase?.charAt(0).toUpperCase() + suggestions?.current_phase?.slice(1)} Phase
                    </p>
                </div>
                <div className="streak-badge">
                    <Trophy size={24} />
                    <span className="streak-count">{stats?.current_streak || 0}</span>
                    <span className="streak-label">Day Streak</span>
                </div>
            </div>

            {/* Phase Tip */}
            {suggestions?.phase_tip && (
                <div className="phase-tip-card" style={{ borderColor: phaseColors[suggestions?.current_phase] }}>
                    <p>{suggestions.phase_tip}</p>
                </div>
            )}

            {/* Stats Overview */}
            <div className="stats-grid">
                <div className="stat-card">
                    <ActivityIcon size={20} />
                    <div className="stat-value">{stats?.total_workouts || 0}</div>
                    <div className="stat-label">Workouts</div>
                </div>
                <div className="stat-card">
                    <Clock size={20} />
                    <div className="stat-value">{stats?.total_duration_minutes || 0}</div>
                    <div className="stat-label">Minutes</div>
                </div>
                <div className="stat-card">
                    <Flame size={20} />
                    <div className="stat-value">{stats?.total_calories_burned || 0}</div>
                    <div className="stat-label">Calories</div>
                </div>
                <div className="stat-card">
                    <TrendingUp size={20} />
                    <div className="stat-value">{stats?.longest_streak || 0}</div>
                    <div className="stat-label">Best Streak</div>
                </div>
            </div>

            {/* Suggested Exercises */}
            <section className="suggested-section">
                <h2>Recommended For You</h2>
                <div className="exercise-carousel">
                    {suggestions?.suggestions?.slice(0, 6).map((exercise: Exercise) => (
                        <div key={exercise.id} className="exercise-card">
                            <div className="exercise-thumbnail" onClick={() => handleWatchVideo(exercise)}>
                                {exercise.youtube_video_id ? (
                                    <img
                                        src={`https://img.youtube.com/vi/${exercise.youtube_video_id}/mqdefault.jpg`}
                                        alt={exercise.name}
                                    />
                                ) : (
                                    <div className="thumbnail-placeholder">
                                        <ActivityIcon size={40} />
                                    </div>
                                )}
                                <div className="play-overlay">
                                    <Play size={32} />
                                </div>
                                <span
                                    className="intensity-badge"
                                    style={{ backgroundColor: intensityColors[exercise.intensity_level] }}
                                >
                                    {exercise.intensity_level}
                                </span>
                            </div>
                            <div className="exercise-info">
                                <h3>{exercise.name}</h3>
                                <p className="exercise-meta">
                                    <Clock size={14} /> {exercise.duration_minutes} min
                                    <Flame size={14} /> ~{Math.round(exercise.calories_per_minute * exercise.duration_minutes)} cal
                                </p>
                                <p className="exercise-category">{exercise.category}</p>
                            </div>
                            <div className="exercise-actions">
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => handleWatchVideo(exercise)}
                                >
                                    <Youtube size={16} /> Watch
                                </button>
                                <button
                                    className="btn btn-primary btn-sm"
                                    onClick={() => handleLogExercise(exercise)}
                                >
                                    <Check size={16} /> Log
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Categories */}
            <section className="categories-section">
                <h2>Browse by Category</h2>
                <div className="category-tabs">
                    <button
                        className={`category-tab ${!activeCategory ? 'active' : ''}`}
                        onClick={() => setActiveCategory(null)}
                    >
                        All
                    </button>
                    {categories.map(cat => (
                        <button
                            key={cat.id}
                            className={`category-tab ${activeCategory === cat.id ? 'active' : ''}`}
                            onClick={() => setActiveCategory(cat.id)}
                        >
                            {cat.emoji} {cat.name}
                        </button>
                    ))}
                </div>
                <div className="exercise-list">
                    {allExercises?.exercises?.map((exercise: Exercise) => (
                        <div key={exercise.id} className="exercise-list-item">
                            <div className="exercise-list-info">
                                <h4>{exercise.name}</h4>
                                <p>{exercise.description?.substring(0, 80)}...</p>
                                <div className="exercise-tags">
                                    <span className="tag">{exercise.category}</span>
                                    <span
                                        className="tag intensity"
                                        style={{ backgroundColor: intensityColors[exercise.intensity_level] }}
                                    >
                                        {exercise.intensity_level}
                                    </span>
                                    <span className="tag">{exercise.duration_minutes} min</span>
                                </div>
                            </div>
                            <div className="exercise-list-actions">
                                <button
                                    className="btn-view-details"
                                    onClick={() => {
                                        setSelectedExercise(exercise);
                                        setShowVideoModal(true);
                                    }}
                                >
                                    View Details
                                </button>
                                <button onClick={() => handleLogExercise(exercise)}>
                                    <ChevronRight size={20} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Recent Activity */}
            {logs?.logs && logs.logs.length > 0 && (
                <section className="recent-section">
                    <h2>Recent Activity</h2>
                    <div className="recent-logs">
                        {logs.logs.slice(0, 5).map((log: any) => (
                            <div key={log.id} className="log-item">
                                <div className="log-icon">
                                    <ActivityIcon size={18} />
                                </div>
                                <div className="log-info">
                                    <h4>{log.exercise_name}</h4>
                                    <p>
                                        <Clock size={12} /> {log.duration_minutes} min
                                        {log.calories_burned && (
                                            <><Flame size={12} /> {Math.round(log.calories_burned)} cal</>
                                        )}
                                    </p>
                                </div>
                                <div className="log-date">
                                    <Calendar size={14} />
                                    {new Date(log.date).toLocaleDateString()}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Video Modal */}
            {showVideoModal && selectedExercise && (
                <div className="modal-overlay" onClick={() => setShowVideoModal(false)}>
                    <div className="modal video-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>{selectedExercise.name}</h3>
                            <button className="close-btn" onClick={() => setShowVideoModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="video-container">
                            <iframe
                                src={`https://www.youtube.com/embed/${selectedExercise.youtube_video_id}?autoplay=1`}
                                title={selectedExercise.youtube_video_title}
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />
                        </div>
                        <div className="modal-footer">
                            <div className="exercise-details">
                                <p><strong>Benefits:</strong> {selectedExercise.benefits}</p>
                                {selectedExercise.instructions && selectedExercise.instructions.length > 0 && (
                                    <div className="instructions">
                                        <strong>Instructions:</strong>
                                        <ul>
                                            {selectedExercise.instructions.map((step, i) => (
                                                <li key={i}>{step}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                            <button
                                className="btn btn-primary"
                                onClick={() => {
                                    setShowVideoModal(false);
                                    handleLogExercise(selectedExercise);
                                }}
                            >
                                <Check size={18} /> Mark as Complete
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Log Modal */}
            {showLogModal && selectedExercise && (
                <div className="modal-overlay" onClick={() => setShowLogModal(false)}>
                    <div className="modal log-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Log Exercise</h3>
                            <button className="close-btn" onClick={() => setShowLogModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="log-exercise-preview">
                                <ActivityIcon size={32} />
                                <div>
                                    <h4>{selectedExercise.name}</h4>
                                    <p>{selectedExercise.category} • {selectedExercise.intensity_level}</p>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Duration (minutes)</label>
                                <div className="duration-input">
                                    <button onClick={() => setLogDuration(Math.max(5, logDuration - 5))}>-</button>
                                    <input
                                        type="number"
                                        value={logDuration}
                                        onChange={e => setLogDuration(parseInt(e.target.value) || 0)}
                                    />
                                    <button onClick={() => setLogDuration(logDuration + 5)}>+</button>
                                </div>
                            </div>

                            <div className="calorie-estimate">
                                <Flame size={18} />
                                <span>Estimated calories burned: </span>
                                <strong>{Math.round(selectedExercise.calories_per_minute * logDuration)}</strong>
                            </div>

                            <div className="form-group">
                                <label>Notes (optional)</label>
                                <textarea
                                    value={logNotes}
                                    onChange={e => setLogNotes(e.target.value)}
                                    placeholder="How did it go?"
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowLogModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={submitLog}
                                disabled={logMutation.isPending}
                            >
                                {logMutation.isPending ? 'Logging...' : 'Log Exercise'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
