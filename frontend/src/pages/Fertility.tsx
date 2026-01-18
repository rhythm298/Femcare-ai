/**
 * Fertility Tracker Page - Comprehensive fertility window visualization
 */

import { useState, useEffect } from 'react';
import {
    Calendar,
    Target,
    Heart,
    Moon,
    Sun,
    ChevronLeft,
    ChevronRight,
    Info,
    Zap,
} from 'lucide-react';
import './Fertility.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

interface FertilityDay {
    date: string;
    cycle_day: number | null;
    fertility_level: string;
    conception_chance: number;
    is_today: boolean;
    is_ovulation: boolean;
    is_period: boolean;
}

interface FertilityData {
    enabled: boolean;
    has_data: boolean;
    message?: string;
    today?: {
        date: string;
        cycle_day: number;
        status: string;
        status_message: string;
        status_emoji: string;
    };
    ovulation?: {
        predicted_date: string;
        cycle_day: number;
        days_until: number | null;
        days_since: number | null;
    };
    fertile_window?: {
        start: string;
        end: string;
        is_in_window: boolean;
        days_in_window: number;
    };
    next_period?: {
        predicted_date: string;
        days_until: number;
    };
    pms?: {
        is_pms_window: boolean;
        pms_start: string;
    };
    calendar?: FertilityDay[];
    insights?: {
        avg_cycle_length: number;
        ovulation_day: number;
        fertile_window_days: number;
        best_conception_days: string[];
    };
}

const getFertilityColor = (level: string): string => {
    switch (level) {
        case 'peak': return '#ef4444';
        case 'very_high': return '#f97316';
        case 'high': return '#fb923c';
        case 'fertile': return '#fbbf24';
        case 'fertile_start': return '#fcd34d';
        case 'menstrual': return '#ec4899';
        case 'low': return '#94a3b8';
        default: return 'transparent';
    }
};

const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
};

export default function Fertility() {
    const [fertilityData, setFertilityData] = useState<FertilityData | null>(null);
    const [loading, setLoading] = useState(true);
    const [weekOffset, setWeekOffset] = useState(0);

    useEffect(() => {
        fetchFertilityData();
    }, []);

    const fetchFertilityData = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/cycles/fertility`, {
                headers: getAuthHeader()
            });
            if (response.ok) {
                const data = await response.json();
                setFertilityData(data);
            }
        } catch (error) {
            console.error('Failed to fetch fertility data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getVisibleCalendarDays = (): FertilityDay[] => {
        if (!fertilityData?.calendar) return [];
        const startIdx = Math.max(0, 7 + weekOffset * 7);
        return fertilityData.calendar.slice(startIdx, startIdx + 7);
    };

    if (loading) {
        return (
            <div className="fertility-page animate-fade-in">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading fertility data...</p>
                </div>
            </div>
        );
    }

    if (!fertilityData?.enabled) {
        return (
            <div className="fertility-page animate-fade-in">
                <div className="page-header">
                    <h1><Target size={28} /> Fertility Tracker</h1>
                </div>
                <div className="disabled-message card">
                    <Info size={48} />
                    <h2>Fertility Tracking Disabled</h2>
                    <p>Fertility tracking is currently disabled because you indicated you're on birth control.</p>
                    <p>Update your profile in Settings to enable fertility tracking.</p>
                </div>
            </div>
        );
    }

    if (!fertilityData?.has_data) {
        return (
            <div className="fertility-page animate-fade-in">
                <div className="page-header">
                    <h1><Target size={28} /> Fertility Tracker</h1>
                </div>
                <div className="no-data-message card">
                    <Calendar size={48} />
                    <h2>No Cycle Data Yet</h2>
                    <p>Log at least one cycle to get fertility predictions.</p>
                    <a href="/cycles" className="btn btn-primary">Start Tracking Cycles</a>
                </div>
            </div>
        );
    }

    const visibleDays = getVisibleCalendarDays();

    return (
        <div className="fertility-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1><Target size={28} /> Fertility Tracker</h1>
                    <p>Track your fertile window and ovulation</p>
                </div>
            </div>

            {/* Today's Status Card */}
            <div className="today-status card glass">
                <div className="status-main">
                    <span className="status-emoji">{fertilityData.today?.status_emoji}</span>
                    <div className="status-info">
                        <h2>Day {fertilityData.today?.cycle_day}</h2>
                        <p className="status-message">{fertilityData.today?.status_message}</p>
                    </div>
                </div>
                <div className="status-badges">
                    {fertilityData.fertile_window?.is_in_window && (
                        <span className="badge fertile-badge">
                            <Zap size={14} /> Fertile Window
                        </span>
                    )}
                    {fertilityData.pms?.is_pms_window && (
                        <span className="badge pms-badge">
                            <Moon size={14} /> PMS Phase
                        </span>
                    )}
                </div>
            </div>

            {/* Quick Stats */}
            <div className="fertility-stats">
                <div className="stat-card glass">
                    <Target size={24} className="stat-icon ovulation" />
                    <div className="stat-content">
                        <span className="stat-label">Ovulation</span>
                        {fertilityData.ovulation?.days_until !== null && (fertilityData.ovulation?.days_until ?? -1) >= 0 ? (
                            <span className="stat-value">In {fertilityData.ovulation?.days_until} days</span>
                        ) : (
                            <span className="stat-value">{fertilityData.ovulation?.days_since} days ago</span>
                        )}
                    </div>
                </div>
                <div className="stat-card glass">
                    <Heart size={24} className="stat-icon period" />
                    <div className="stat-content">
                        <span className="stat-label">Next Period</span>
                        <span className="stat-value">In {fertilityData.next_period?.days_until} days</span>
                    </div>
                </div>
                <div className="stat-card glass">
                    <Sun size={24} className="stat-icon cycle" />
                    <div className="stat-content">
                        <span className="stat-label">Cycle Length</span>
                        <span className="stat-value">{fertilityData.insights?.avg_cycle_length} days</span>
                    </div>
                </div>
            </div>

            {/* Fertility Calendar */}
            <div className="fertility-calendar card">
                <div className="calendar-header">
                    <h3><Calendar size={18} /> Fertility Calendar</h3>
                    <div className="calendar-nav">
                        <button
                            className="btn btn-icon"
                            onClick={() => setWeekOffset(w => w - 1)}
                            disabled={weekOffset <= -1}
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <span>
                            {weekOffset === 0 ? 'This Week' : weekOffset > 0 ? `Week +${weekOffset}` : `Week ${weekOffset}`}
                        </span>
                        <button
                            className="btn btn-icon"
                            onClick={() => setWeekOffset(w => w + 1)}
                            disabled={weekOffset >= 3}
                        >
                            <ChevronRight size={20} />
                        </button>
                    </div>
                </div>
                <div className="calendar-grid">
                    {visibleDays.map((day) => (
                        <div
                            key={day.date}
                            className={`calendar-day ${day.is_today ? 'today' : ''} ${day.is_ovulation ? 'ovulation' : ''}`}
                        >
                            <span className="day-date">
                                {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                            </span>
                            <span className="day-number">
                                {new Date(day.date).getDate()}
                            </span>
                            <div
                                className="fertility-indicator"
                                style={{ backgroundColor: getFertilityColor(day.fertility_level) }}
                            >
                                {day.is_ovulation && '🎯'}
                                {day.is_period && '🩸'}
                            </div>
                            <span className="conception-chance">
                                {day.conception_chance > 0 ? `${day.conception_chance}%` : '-'}
                            </span>
                            {day.cycle_day && <span className="cycle-day">Day {day.cycle_day}</span>}
                        </div>
                    ))}
                </div>
            </div>

            {/* Legend */}
            <div className="fertility-legend card">
                <h4>Fertility Levels</h4>
                <div className="legend-grid">
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
                        <span>Peak (Ovulation)</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#f97316' }}></span>
                        <span>Very High</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#fb923c' }}></span>
                        <span>High</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#fbbf24' }}></span>
                        <span>Fertile</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#ec4899' }}></span>
                        <span>Period</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#94a3b8' }}></span>
                        <span>Low</span>
                    </div>
                </div>
            </div>

            {/* Best Days */}
            {fertilityData.insights?.best_conception_days && (
                <div className="best-days card">
                    <h4><Heart size={18} /> Best Conception Days</h4>
                    <div className="best-days-list">
                        {fertilityData.insights.best_conception_days.map((day, i) => (
                            <div key={i} className="best-day">
                                <Target size={16} />
                                <span>{formatDate(day)}</span>
                            </div>
                        ))}
                    </div>
                    <p className="best-days-note">
                        These are your most fertile days based on ovulation prediction.
                    </p>
                </div>
            )}
        </div>
    );
}
