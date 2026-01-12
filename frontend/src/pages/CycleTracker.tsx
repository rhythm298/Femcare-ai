/**
 * Cycle Tracker Page
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cyclesApi } from '../services/api';
import { format, parseISO, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isToday } from 'date-fns';
import type { FlowLevel, CycleCreate } from '../types';
import {
    Calendar,
    Plus,
    ChevronLeft,
    ChevronRight,
    Droplets,
    TrendingUp,
    Clock,
    X,
} from 'lucide-react';
import './CycleTracker.css';

const flowLevelOptions: { value: FlowLevel; label: string; emoji: string }[] = [
    { value: 'spotting', label: 'Spotting', emoji: '💧' },
    { value: 'light', label: 'Light', emoji: '💧💧' },
    { value: 'medium', label: 'Medium', emoji: '💧💧💧' },
    { value: 'heavy', label: 'Heavy', emoji: '💧💧💧💧' },
    { value: 'very_heavy', label: 'Very Heavy', emoji: '💧💧💧💧💧' },
];

export default function CycleTracker() {
    const queryClient = useQueryClient();
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const [showModal, setShowModal] = useState(false);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);
    const [flowLevel, setFlowLevel] = useState<FlowLevel>('medium');
    const [notes, setNotes] = useState('');

    const { data: cycles = [], isLoading } = useQuery({
        queryKey: ['cycles'],
        queryFn: () => cyclesApi.getAll(),
    });

    const { data: currentCycle } = useQuery({
        queryKey: ['currentCycle'],
        queryFn: cyclesApi.getCurrent,
    });

    const { data: patterns } = useQuery({
        queryKey: ['cyclePatterns'],
        queryFn: cyclesApi.getPatterns,
        enabled: cycles.length >= 2,
    });

    const createCycleMutation = useMutation({
        mutationFn: (data: CycleCreate) => cyclesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cycles'] });
            queryClient.invalidateQueries({ queryKey: ['currentCycle'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
            setShowModal(false);
            resetForm();
        },
    });

    const resetForm = () => {
        setSelectedDate(null);
        setFlowLevel('medium');
        setNotes('');
    };

    const handleDateClick = (date: Date) => {
        setSelectedDate(date);
        setShowModal(true);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedDate) return;

        createCycleMutation.mutate({
            start_date: format(selectedDate, 'yyyy-MM-dd'),
            flow_level: flowLevel,
            notes: notes || undefined,
        });
    };

    // Calendar generation
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const calendarDays = eachDayOfInterval({ start: monthStart, end: monthEnd });

    // Get day offset for first day of month
    const startDayOffset = monthStart.getDay();
    const emptyDays = Array(startDayOffset).fill(null);

    // Check if a day is a period day
    const isPeriodDay = (date: Date) => {
        return cycles.some((cycle) => {
            const start = parseISO(cycle.start_date);
            const end = cycle.end_date ? parseISO(cycle.end_date) : start;
            return date >= start && date <= end;
        });
    };

    const isPredictedPeriod = (date: Date) => {
        if (!currentCycle?.predicted_next_start) return false;
        const predictedStart = parseISO(currentCycle.predicted_next_start);
        const predictedEnd = new Date(predictedStart);
        predictedEnd.setDate(predictedEnd.getDate() + 5);
        return date >= predictedStart && date <= predictedEnd;
    };

    return (
        <div className="cycle-tracker animate-fade-in">
            <div className="page-header">
                <div>
                    <h1><Calendar size={28} /> Cycle Tracker</h1>
                    <p>Track your menstrual cycle and get predictions</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                    <Plus size={18} /> Log Period
                </button>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card glass">
                    <Droplets size={24} className="stat-icon" />
                    <div className="stat-content">
                        <span className="stat-value">
                            {patterns?.average_cycle_length?.toFixed(0) || '--'}
                        </span>
                        <span className="stat-label">Avg Cycle Length</span>
                    </div>
                </div>
                <div className="stat-card glass">
                    <Clock size={24} className="stat-icon" />
                    <div className="stat-content">
                        <span className="stat-value">
                            {patterns?.average_period_length?.toFixed(0) || '--'}
                        </span>
                        <span className="stat-label">Avg Period Length</span>
                    </div>
                </div>
                <div className="stat-card glass">
                    <TrendingUp size={24} className="stat-icon" />
                    <div className="stat-content">
                        <span className="stat-value">
                            {patterns?.regularity_score
                                ? `${(patterns.regularity_score * 100).toFixed(0)}%`
                                : '--'
                            }
                        </span>
                        <span className="stat-label">Regularity Score</span>
                    </div>
                </div>
                <div className="stat-card glass">
                    <Calendar size={24} className="stat-icon" />
                    <div className="stat-content">
                        <span className="stat-value">{cycles.length}</span>
                        <span className="stat-label">Cycles Tracked</span>
                    </div>
                </div>
            </div>

            {/* Calendar */}
            <div className="calendar-card card">
                <div className="calendar-header">
                    <button
                        className="btn btn-ghost btn-icon"
                        onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() - 1)))}
                    >
                        <ChevronLeft size={20} />
                    </button>
                    <h2>{format(currentMonth, 'MMMM yyyy')}</h2>
                    <button
                        className="btn btn-ghost btn-icon"
                        onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() + 1)))}
                    >
                        <ChevronRight size={20} />
                    </button>
                </div>

                <div className="calendar-grid">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                        <div key={day} className="calendar-day-name">{day}</div>
                    ))}

                    {emptyDays.map((_, index) => (
                        <div key={`empty-${index}`} className="calendar-day empty"></div>
                    ))}

                    {calendarDays.map((day) => {
                        const isPeriod = isPeriodDay(day);
                        const isPredicted = isPredictedPeriod(day);
                        const today = isToday(day);

                        return (
                            <button
                                key={day.toISOString()}
                                className={`calendar-day ${isPeriod ? 'period' : ''} ${isPredicted ? 'predicted' : ''} ${today ? 'today' : ''}`}
                                onClick={() => handleDateClick(day)}
                            >
                                <span className="day-number">{format(day, 'd')}</span>
                                {isPeriod && <span className="day-indicator">🔴</span>}
                                {isPredicted && !isPeriod && <span className="day-indicator predicted-dot"></span>}
                            </button>
                        );
                    })}
                </div>

                <div className="calendar-legend">
                    <div className="legend-item">
                        <span className="legend-dot period"></span>
                        <span>Period</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-dot predicted"></span>
                        <span>Predicted</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-dot today"></span>
                        <span>Today</span>
                    </div>
                </div>
            </div>

            {/* Recent Cycles */}
            {cycles.length > 0 && (
                <div className="recent-cycles card">
                    <div className="card-header">
                        <h3>Recent Cycles</h3>
                    </div>
                    <div className="card-body">
                        <div className="cycles-list">
                            {cycles.slice(0, 5).map((cycle) => (
                                <div key={cycle.id} className="cycle-item">
                                    <div className="cycle-dates">
                                        <span className="start-date">
                                            {format(parseISO(cycle.start_date), 'MMM d, yyyy')}
                                        </span>
                                        {cycle.end_date && (
                                            <span className="end-date">
                                                to {format(parseISO(cycle.end_date), 'MMM d')}
                                            </span>
                                        )}
                                    </div>
                                    <div className="cycle-meta">
                                        {cycle.cycle_length && (
                                            <span className="badge badge-primary">{cycle.cycle_length} days</span>
                                        )}
                                        <span className="flow-level">{cycle.flow_level}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Log Period Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal glass animate-slide-up" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Log Period</h2>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Start Date</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={selectedDate ? format(selectedDate, 'yyyy-MM-dd') : ''}
                                        onChange={(e) => setSelectedDate(new Date(e.target.value))}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Flow Level</label>
                                    <div className="flow-options">
                                        {flowLevelOptions.map((option) => (
                                            <button
                                                key={option.value}
                                                type="button"
                                                className={`flow-option ${flowLevel === option.value ? 'active' : ''}`}
                                                onClick={() => setFlowLevel(option.value)}
                                            >
                                                <span className="flow-emoji">{option.emoji}</span>
                                                <span className="flow-label">{option.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Notes (optional)</label>
                                    <textarea
                                        className="form-input form-textarea"
                                        placeholder="Any additional notes..."
                                        value={notes}
                                        onChange={(e) => setNotes(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={!selectedDate || createCycleMutation.isPending}
                                >
                                    {createCycleMutation.isPending ? 'Saving...' : 'Save Period'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
