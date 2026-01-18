/**
 * Water Tracker Page - Hydration tracking with phase-based goals
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Droplets,
    Plus,
    Target,
    TrendingUp,
    Calendar,
    Trash2,
    Settings,
    X,
    Check,
    Coffee,
    Leaf
} from 'lucide-react';
import './WaterTracker.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const hydrationApi = {
    logWater: async (data: { amount_ml: number; drink_type: string }) => {
        const params = new URLSearchParams();
        params.set('amount_ml', String(data.amount_ml));
        params.set('drink_type', data.drink_type);
        const response = await fetch(`${API_BASE_URL}/hydration/log?${params}`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to log water');
        return response.json();
    },
    getToday: async () => {
        const response = await fetch(`${API_BASE_URL}/hydration/today`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch today');
        return response.json();
    },
    getHistory: async (days: number = 7) => {
        const response = await fetch(`${API_BASE_URL}/hydration/history?days=${days}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch history');
        return response.json();
    },
    getGoal: async () => {
        const response = await fetch(`${API_BASE_URL}/hydration/goal`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch goal');
        return response.json();
    },
    updateGoal: async (data: { daily_goal_ml: number; adjust_for_phase: boolean }) => {
        const params = new URLSearchParams();
        params.set('daily_goal_ml', String(data.daily_goal_ml));
        params.set('adjust_for_phase', String(data.adjust_for_phase));
        const response = await fetch(`${API_BASE_URL}/hydration/goal?${params}`, {
            method: 'PUT',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to update goal');
        return response.json();
    },
    deleteLog: async (logId: number) => {
        const response = await fetch(`${API_BASE_URL}/hydration/log/${logId}`, {
            method: 'DELETE',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to delete log');
        return response.json();
    }
};

const quickAmounts = [
    { ml: 250, label: '1 Glass', icon: '🥛' },
    { ml: 500, label: '1 Bottle', icon: '🍶' },
    { ml: 750, label: 'Large Bottle', icon: '🧴' },
    { ml: 1000, label: '1 Liter', icon: '💧' }
];

const drinkTypes = [
    { id: 'water', label: 'Water', icon: '💧', color: '#3b82f6' },
    { id: 'tea', label: 'Tea', icon: '🍵', color: '#22c55e' },
    { id: 'coffee', label: 'Coffee', icon: '☕', color: '#92400e' },
    { id: 'juice', label: 'Juice', icon: '🧃', color: '#f97316' },
    { id: 'infused_water', label: 'Infused', icon: '🍋', color: '#eab308' }
];

export default function WaterTracker() {
    const queryClient = useQueryClient();
    const [showGoalModal, setShowGoalModal] = useState(false);
    const [customAmount, setCustomAmount] = useState(250);
    const [selectedDrink, setSelectedDrink] = useState('water');
    const [goalAmount, setGoalAmount] = useState(2500);
    const [adjustForPhase, setAdjustForPhase] = useState(true);

    const { data: todayData, isLoading } = useQuery({
        queryKey: ['hydrationToday'],
        queryFn: hydrationApi.getToday,
        refetchInterval: 30000 // Refresh every 30 seconds
    });

    const { data: historyData } = useQuery({
        queryKey: ['hydrationHistory'],
        queryFn: () => hydrationApi.getHistory(7)
    });

    const { data: goalData } = useQuery({
        queryKey: ['hydrationGoal'],
        queryFn: hydrationApi.getGoal
    });

    const logMutation = useMutation({
        mutationFn: hydrationApi.logWater,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['hydrationToday'] });
            queryClient.invalidateQueries({ queryKey: ['hydrationHistory'] });
        }
    });

    const deleteMutation = useMutation({
        mutationFn: hydrationApi.deleteLog,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['hydrationToday'] });
            queryClient.invalidateQueries({ queryKey: ['hydrationHistory'] });
        }
    });

    const goalMutation = useMutation({
        mutationFn: hydrationApi.updateGoal,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['hydrationGoal'] });
            queryClient.invalidateQueries({ queryKey: ['hydrationToday'] });
            setShowGoalModal(false);
        }
    });

    const handleQuickAdd = (amount: number) => {
        logMutation.mutate({ amount_ml: amount, drink_type: selectedDrink });
    };

    const handleCustomAdd = () => {
        if (customAmount > 0) {
            logMutation.mutate({ amount_ml: customAmount, drink_type: selectedDrink });
        }
    };

    const progressPercentage = todayData?.progress_percentage || 0;
    const circumference = 2 * Math.PI * 90;
    const strokeDashoffset = circumference - (Math.min(progressPercentage, 100) / 100) * circumference;

    if (isLoading) {
        return (
            <div className="water-page">
                <div className="loading-container">
                    <Droplets size={40} className="loading-icon" />
                    <p>Loading hydration data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="water-page animate-fade-in">
            {/* Header */}
            <div className="water-header">
                <div>
                    <h1><Droplets size={28} /> Water Tracker</h1>
                    <p className="phase-info">
                        {todayData?.current_phase} phase
                        {goalData?.adjust_for_phase && todayData?.current_phase === 'menstrual' && (
                            <span className="phase-boost"> (+20% goal)</span>
                        )}
                    </p>
                </div>
                <button className="btn btn-secondary" onClick={() => {
                    setGoalAmount(goalData?.daily_goal_ml || 2500);
                    setAdjustForPhase(goalData?.adjust_for_phase ?? true);
                    setShowGoalModal(true);
                }}>
                    <Settings size={18} /> Goal
                </button>
            </div>

            {/* Main Progress Ring */}
            <div className="progress-section">
                <div className="progress-ring-container">
                    <svg className="progress-ring" viewBox="0 0 200 200">
                        <circle
                            className="ring-bg"
                            cx="100"
                            cy="100"
                            r="90"
                            fill="none"
                            strokeWidth="12"
                        />
                        <circle
                            className="ring-progress"
                            cx="100"
                            cy="100"
                            r="90"
                            fill="none"
                            strokeWidth="12"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            style={{
                                stroke: progressPercentage >= 100 ? '#22c55e' : '#3b82f6'
                            }}
                        />
                    </svg>
                    <div className="ring-content">
                        <Droplets size={32} className="water-icon" />
                        <span className="amount">{todayData?.total_ml || 0}</span>
                        <span className="unit">ml</span>
                        <span className="percentage">{Math.round(progressPercentage)}%</span>
                    </div>
                </div>

                <div className="goal-info">
                    <div className="goal-stat">
                        <Target size={18} />
                        <span>{todayData?.daily_goal_ml || 2500} ml goal</span>
                    </div>
                    <div className="goal-stat">
                        <span className="glasses-icon">🥛</span>
                        <span>{todayData?.glasses || 0} glasses</span>
                    </div>
                    <div className="goal-stat remaining">
                        <span>{todayData?.remaining_ml || 0} ml remaining</span>
                    </div>
                </div>

                {todayData?.goal_achieved && (
                    <div className="goal-achieved">
                        <span>🎉</span> Daily goal achieved!
                    </div>
                )}
            </div>

            {/* Phase Tip */}
            {todayData?.phase_tip && (
                <div className="phase-tip">
                    <Leaf size={16} />
                    <p>{todayData.phase_tip}</p>
                </div>
            )}

            {/* Drink Type Selector */}
            <div className="drink-selector">
                {drinkTypes.map(drink => (
                    <button
                        key={drink.id}
                        className={`drink-option ${selectedDrink === drink.id ? 'active' : ''}`}
                        onClick={() => setSelectedDrink(drink.id)}
                        style={{ '--drink-color': drink.color } as React.CSSProperties}
                    >
                        <span className="drink-icon">{drink.icon}</span>
                        <span className="drink-label">{drink.label}</span>
                    </button>
                ))}
            </div>

            {/* Quick Add Buttons */}
            <div className="quick-add-section">
                <h3>Quick Add</h3>
                <div className="quick-buttons">
                    {quickAmounts.map(({ ml, label, icon }) => (
                        <button
                            key={ml}
                            className="quick-btn"
                            onClick={() => handleQuickAdd(ml)}
                            disabled={logMutation.isPending}
                        >
                            <span className="quick-icon">{icon}</span>
                            <span className="quick-ml">+{ml}ml</span>
                            <span className="quick-label">{label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Custom Amount */}
            <div className="custom-add-section">
                <div className="custom-input-group">
                    <button onClick={() => setCustomAmount(Math.max(50, customAmount - 50))}>−</button>
                    <input
                        type="number"
                        value={customAmount}
                        onChange={e => setCustomAmount(parseInt(e.target.value) || 0)}
                        min={50}
                        max={2000}
                    />
                    <span className="unit-label">ml</span>
                    <button onClick={() => setCustomAmount(Math.min(2000, customAmount + 50))}>+</button>
                </div>
                <button
                    className="btn btn-primary add-custom-btn"
                    onClick={handleCustomAdd}
                    disabled={logMutation.isPending || customAmount < 50}
                >
                    <Plus size={18} /> Add
                </button>
            </div>

            {/* Today's Logs */}
            {todayData?.logs && todayData.logs.length > 0 && (
                <div className="today-logs-section">
                    <h3>Today's Intake</h3>
                    <div className="logs-list">
                        {todayData.logs.map((log: any) => {
                            const drink = drinkTypes.find(d => d.id === log.drink_type);
                            return (
                                <div key={log.id} className="log-item">
                                    <span className="log-icon">{drink?.icon || '💧'}</span>
                                    <div className="log-info">
                                        <span className="log-amount">{log.amount_ml} ml</span>
                                        <span className="log-type">{drink?.label || log.drink_type}</span>
                                    </div>
                                    <span className="log-time">
                                        {log.logged_at ? new Date(log.logged_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                                    </span>
                                    <button
                                        className="delete-btn"
                                        onClick={() => deleteMutation.mutate(log.id)}
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Weekly Summary */}
            {historyData?.history && (
                <div className="history-section">
                    <h3>
                        <Calendar size={18} /> This Week
                    </h3>
                    <div className="history-chart">
                        {historyData.history.map((day: any, i: number) => {
                            const height = Math.min((day.total_ml / (todayData?.daily_goal_ml || 2500)) * 100, 100);
                            const isToday = day.date === todayData?.date;
                            return (
                                <div key={day.date} className={`chart-bar ${isToday ? 'today' : ''}`}>
                                    <div
                                        className={`bar-fill ${day.met_goal ? 'met' : ''}`}
                                        style={{ height: `${height}%` }}
                                    >
                                        {day.met_goal && <Check size={12} />}
                                    </div>
                                    <span className="bar-label">
                                        {new Date(day.date).toLocaleDateString('en', { weekday: 'short' }).charAt(0)}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                    <div className="history-stats">
                        <div className="stat">
                            <TrendingUp size={16} />
                            <span>{historyData.summary?.current_streak || 0} day streak</span>
                        </div>
                        <div className="stat">
                            <Target size={16} />
                            <span>{historyData.summary?.success_rate || 0}% success rate</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Goal Settings Modal */}
            {showGoalModal && (
                <div className="modal-overlay" onClick={() => setShowGoalModal(false)}>
                    <div className="modal goal-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Hydration Goal</h3>
                            <button className="close-btn" onClick={() => setShowGoalModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Daily Goal (ml)</label>
                                <div className="goal-input">
                                    <button onClick={() => setGoalAmount(Math.max(1000, goalAmount - 250))}>−</button>
                                    <input
                                        type="number"
                                        value={goalAmount}
                                        onChange={e => setGoalAmount(parseInt(e.target.value) || 2500)}
                                    />
                                    <button onClick={() => setGoalAmount(Math.min(5000, goalAmount + 250))}>+</button>
                                </div>
                                <p className="hint">{(goalAmount / 250).toFixed(0)} glasses per day</p>
                            </div>

                            <label className="toggle-group">
                                <input
                                    type="checkbox"
                                    checked={adjustForPhase}
                                    onChange={e => setAdjustForPhase(e.target.checked)}
                                />
                                <span className="toggle-label">
                                    <strong>Adjust for cycle phase</strong>
                                    <small>+20% during menstrual phase for better hydration</small>
                                </span>
                            </label>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowGoalModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => goalMutation.mutate({ daily_goal_ml: goalAmount, adjust_for_phase: adjustForPhase })}
                                disabled={goalMutation.isPending}
                            >
                                Save Goal
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
