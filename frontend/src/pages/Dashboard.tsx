/**
 * Dashboard Page - Main Health Overview
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { insightsApi, cyclesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
    Calendar,
    Heart,
    Activity,
    TrendingUp,
    MessageCircle,
    Flame,
    AlertCircle,
    ChevronRight,
    Droplets,
    Moon,
    Sun,
    Sparkles,
} from 'lucide-react';
import './Dashboard.css';

const phaseInfo: Record<string, { icon: typeof Sun; color: string; tip: string }> = {
    menstrual: {
        icon: Droplets,
        color: 'var(--color-menstrual)',
        tip: 'Rest and self-care are important during this phase.',
    },
    follicular: {
        icon: Sun,
        color: 'var(--color-follicular)',
        tip: 'Energy is rising! Great time for new projects.',
    },
    ovulation: {
        icon: Sparkles,
        color: 'var(--color-ovulation)',
        tip: 'Peak energy and fertility window.',
    },
    luteal: {
        icon: Moon,
        color: 'var(--color-luteal)',
        tip: 'Prepare for your period, practice self-care.',
    },
};

export default function Dashboard() {
    const { user } = useAuth();

    const { data: dashboard, isLoading: dashboardLoading } = useQuery({
        queryKey: ['dashboard'],
        queryFn: insightsApi.getDashboard,
    });

    const { data: currentCycle } = useQuery({
        queryKey: ['currentCycle'],
        queryFn: cyclesApi.getCurrent,
    });

    const getRiskLevel = (score: number) => {
        if (score < 0.3) return { level: 'Low', class: 'risk-low' };
        if (score < 0.6) return { level: 'Medium', class: 'risk-medium' };
        return { level: 'High', class: 'risk-high' };
    };

    const phase = currentCycle?.phase || 'follicular';
    const PhaseIcon = phaseInfo[phase]?.icon || Sun;

    if (dashboardLoading) {
        return (
            <div className="dashboard">
                <div className="dashboard-header">
                    <div className="skeleton" style={{ width: 200, height: 32 }}></div>
                    <div className="skeleton" style={{ width: 300, height: 20 }}></div>
                </div>
                <div className="dashboard-grid">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="card skeleton-card">
                            <div className="skeleton" style={{ width: '100%', height: 150 }}></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard animate-fade-in">
            {/* Header */}
            <div className="dashboard-header">
                <div>
                    <h1>Welcome back, {user?.name?.split(' ')[0]}! 👋</h1>
                    <p>Here's your health overview for today</p>
                </div>
                <div className="health-score-badge">
                    <Heart className="pulse-icon" />
                    <span className="score">{dashboard?.health_score?.toFixed(0) || 85}</span>
                    <span className="label">Health Score</span>
                </div>
            </div>

            {/* Main Grid */}
            <div className="dashboard-grid">
                {/* Cycle Status Card */}
                <div className="card cycle-card gradient-border">
                    <div className="card-body">
                        <div className="cycle-header">
                            <PhaseIcon
                                size={40}
                                style={{ color: phaseInfo[phase]?.color }}
                                className="phase-icon animate-float"
                            />
                            <div>
                                <h3>{phase.charAt(0).toUpperCase() + phase.slice(1)} Phase</h3>
                                <p className="cycle-day">
                                    Day {currentCycle?.cycle_day || dashboard?.current_cycle_day || '--'}
                                </p>
                            </div>
                        </div>

                        {currentCycle?.has_data !== false ? (
                            <>
                                <div className="cycle-progress">
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{
                                                width: `${Math.min((dashboard?.current_cycle_day || 14) / 28 * 100, 100)}%`
                                            }}
                                        ></div>
                                    </div>
                                    <div className="progress-labels">
                                        <span>Day 1</span>
                                        <span>Day 28</span>
                                    </div>
                                </div>

                                <div className="cycle-info">
                                    <div className="info-item">
                                        <Calendar size={16} />
                                        <span>
                                            {dashboard?.days_until_next_period !== undefined
                                                ? `${dashboard.days_until_next_period} days until period`
                                                : 'Tracking...'}
                                        </span>
                                    </div>
                                    <p className="phase-tip">{phaseInfo[phase]?.tip}</p>
                                </div>
                            </>
                        ) : (
                            <div className="no-data-prompt">
                                <p>Start tracking to see your cycle insights!</p>
                                <Link to="/cycles" className="btn btn-primary">
                                    Log Period <ChevronRight size={16} />
                                </Link>
                            </div>
                        )}
                    </div>
                </div>

                {/* Risk Overview Card */}
                <div className="card risks-card">
                    <div className="card-header">
                        <h3><Activity size={20} /> Health Risks</h3>
                        <Link to="/insights" className="btn btn-ghost btn-sm">
                            View All <ChevronRight size={14} />
                        </Link>
                    </div>
                    <div className="card-body">
                        <div className="risk-gauges">
                            {['pcos', 'endometriosis', 'anemia', 'thyroid'].map((condition) => {
                                const score = dashboard?.risk_summary?.[condition as keyof typeof dashboard.risk_summary] || 0;
                                const risk = getRiskLevel(score);
                                return (
                                    <div key={condition} className="risk-item">
                                        <div className="risk-header">
                                            <span className="risk-name">{condition.toUpperCase()}</span>
                                            <span className={`risk-badge badge ${risk.class}`}>{risk.level}</span>
                                        </div>
                                        <div className="risk-gauge">
                                            <div
                                                className={`risk-gauge-fill ${risk.class}`}
                                                style={{ width: `${score * 100}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Quick Actions Card */}
                <div className="card actions-card">
                    <div className="card-header">
                        <h3><TrendingUp size={20} /> Quick Actions</h3>
                    </div>
                    <div className="card-body">
                        <div className="quick-actions">
                            <Link to="/symptoms" className="action-btn">
                                <Activity size={24} />
                                <span>Log Symptom</span>
                            </Link>
                            <Link to="/cycles" className="action-btn">
                                <Calendar size={24} />
                                <span>Track Cycle</span>
                            </Link>
                            <Link to="/chat" className="action-btn">
                                <MessageCircle size={24} />
                                <span>Ask AI</span>
                            </Link>
                        </div>

                        {/* Streak */}
                        <div className="streak-section">
                            <Flame size={24} className="streak-icon" />
                            <div className="streak-info">
                                <span className="streak-count">{dashboard?.current_streak || 0}</span>
                                <span className="streak-label">Day Streak</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recent Activity Card */}
                <div className="card activity-card">
                    <div className="card-header">
                        <h3><AlertCircle size={20} /> Recent Activity</h3>
                    </div>
                    <div className="card-body">
                        {dashboard?.recent_symptoms && dashboard.recent_symptoms.length > 0 ? (
                            <ul className="activity-list">
                                {dashboard.recent_symptoms.slice(0, 4).map((symptom) => (
                                    <li key={symptom.id} className="activity-item">
                                        <div className="activity-icon">
                                            <Activity size={16} />
                                        </div>
                                        <div className="activity-content">
                                            <span className="activity-title">
                                                {symptom.symptom_type.replace(/_/g, ' ')}
                                            </span>
                                            <span className="activity-meta">
                                                Severity: {symptom.severity}/10 • {symptom.category}
                                            </span>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <div className="empty-activity">
                                <p>No recent symptoms logged</p>
                                <Link to="/symptoms" className="btn btn-secondary btn-sm">
                                    Log a Symptom
                                </Link>
                            </div>
                        )}

                        {/* Notifications */}
                        <div className="notifications-summary">
                            {dashboard?.unread_insights ? (
                                <Link to="/insights" className="notification-badge">
                                    <span>{dashboard.unread_insights}</span> new insights
                                </Link>
                            ) : null}
                            {dashboard?.pending_recommendations ? (
                                <Link to="/insights" className="notification-badge">
                                    <span>{dashboard.pending_recommendations}</span> recommendations
                                </Link>
                            ) : null}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
