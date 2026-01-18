/**
 * Symptoms Page - Log and track symptoms with personalized guidance
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { symptomsApi } from '../services/api';
import { format } from 'date-fns';
import type { SymptomCategory, SymptomCreate } from '../types';
import {
    Activity,
    Plus,
    X,
    TrendingUp,
    TrendingDown,
    Minus,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Lightbulb,
    UserCheck,
    ChevronRight,
    Heart,
} from 'lucide-react';
import './Symptoms.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

interface SymptomGuidance {
    name: string;
    emoji: string;
    description: string;
    do: string[];
    dont: string[];
    remedies: { name: string; how: string }[];
    see_doctor: string[];
    user_history: {
        times_logged: number;
        average_severity: number;
    };
}

const symptomCategories: { value: SymptomCategory; label: string; emoji: string }[] = [
    { value: 'physical', label: 'Physical', emoji: '💪' },
    { value: 'emotional', label: 'Emotional', emoji: '💭' },
    { value: 'hormonal', label: 'Hormonal', emoji: '⚡' },
    { value: 'reproductive', label: 'Reproductive', emoji: '🌸' },
    { value: 'digestive', label: 'Digestive', emoji: '🍽️' },
];

const commonSymptoms: Record<SymptomCategory, string[]> = {
    physical: ['cramps', 'headache', 'back_pain', 'fatigue', 'bloating', 'breast_tenderness'],
    emotional: ['mood_swings', 'anxiety', 'irritability', 'stress', 'depression'],
    hormonal: ['acne', 'weight_changes', 'hot_flashes', 'hair_loss'],
    reproductive: ['heavy_bleeding', 'spotting', 'painful_periods', 'irregular_periods'],
    digestive: ['nausea', 'constipation', 'food_cravings', 'diarrhea'],
    other: [],
};

export default function Symptoms() {
    const queryClient = useQueryClient();
    const [showModal, setShowModal] = useState(false);
    const [showGuidanceModal, setShowGuidanceModal] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState<SymptomCategory>('physical');
    const [selectedSymptom, setSelectedSymptom] = useState('');
    const [customSymptom, setCustomSymptom] = useState('');
    const [severity, setSeverity] = useState(5);
    const [description, setDescription] = useState('');
    const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [guidanceSymptom, setGuidanceSymptom] = useState('');
    const [guidance, setGuidance] = useState<SymptomGuidance | null>(null);
    const [loadingGuidance, setLoadingGuidance] = useState(false);

    const { data: symptoms = [] } = useQuery({
        queryKey: ['symptoms'],
        queryFn: () => symptomsApi.getAll(),
    });

    const { data: analysis } = useQuery({
        queryKey: ['symptomAnalysis'],
        queryFn: () => symptomsApi.getAnalysis(30),
    });

    const { data: todaySymptoms = [] } = useQuery({
        queryKey: ['todaySymptoms'],
        queryFn: symptomsApi.getToday,
    });

    // PMS Prediction Query
    const { data: pmsPrediction } = useQuery({
        queryKey: ['pmsPrediction'],
        queryFn: async () => {
            const response = await fetch(`${API_BASE_URL}/symptoms/pms-prediction`, {
                headers: getAuthHeader()
            });
            return response.json();
        }
    });

    const createMutation = useMutation({
        mutationFn: (data: SymptomCreate) => symptomsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['symptoms'] });
            queryClient.invalidateQueries({ queryKey: ['todaySymptoms'] });
            queryClient.invalidateQueries({ queryKey: ['symptomAnalysis'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
            resetForm();
            setShowModal(false);
        },
    });

    const resetForm = () => {
        setSelectedSymptom('');
        setCustomSymptom('');
        setSeverity(5);
        setDescription('');
        setSelectedDate(format(new Date(), 'yyyy-MM-dd'));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const symptomType = customSymptom || selectedSymptom;
        if (!symptomType) return;

        createMutation.mutate({
            date: selectedDate,
            symptom_type: symptomType,
            category: selectedCategory,
            severity,
            description: description || undefined,
        });
    };

    const fetchGuidance = async (symptomType: string) => {
        setLoadingGuidance(true);
        setGuidanceSymptom(symptomType);
        setShowGuidanceModal(true);
        try {
            const response = await fetch(`${API_BASE_URL}/symptoms/guidance/${symptomType}`, {
                headers: getAuthHeader()
            });
            if (response.ok) {
                const data = await response.json();
                setGuidance(data);
            }
        } catch (error) {
            console.error('Failed to fetch guidance:', error);
        } finally {
            setLoadingGuidance(false);
        }
    };

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'improving': return <TrendingDown className="trend-icon improving" />;
            case 'worsening': return <TrendingUp className="trend-icon worsening" />;
            default: return <Minus className="trend-icon stable" />;
        }
    };

    return (
        <div className="symptoms-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1><Activity size={28} /> Symptom Tracker</h1>
                    <p>Log and analyze your symptoms</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                    <Plus size={18} /> Log Symptom
                </button>
            </div>

            {/* Analysis Summary */}
            {analysis && (
                <div className="analysis-summary">
                    <div className="summary-card glass">
                        <span className="summary-value">{analysis.total_symptoms}</span>
                        <span className="summary-label">Total (30 days)</span>
                    </div>
                    <div className="summary-card glass">
                        <span className="summary-value">{analysis.average_severity.toFixed(1)}</span>
                        <span className="summary-label">Avg Severity</span>
                    </div>
                    <div className="summary-card glass">
                        {getTrendIcon(analysis.severity_trend)}
                        <span className="summary-label">{analysis.severity_trend}</span>
                    </div>
                    <div className="summary-card glass">
                        <span className="summary-value">{todaySymptoms.length}</span>
                        <span className="summary-label">Today</span>
                    </div>
                </div>
            )}

            {/* PMS Prediction */}
            {pmsPrediction?.has_predictions && (
                <div className="pms-prediction card">
                    <div className="card-header">
                        <h3>⚡ PMS Prediction - Coming Up</h3>
                        <span className="pms-phase-badge">
                            {pmsPrediction.is_pms_phase ? '🌙 In PMS Phase' : `Period in ${pmsPrediction.days_until_period} days`}
                        </span>
                    </div>
                    <div className="card-body">
                        {/* Proactive Recommendations */}
                        {pmsPrediction.proactive_recommendations?.length > 0 && (
                            <div className="proactive-tips">
                                {pmsPrediction.proactive_recommendations.map((rec: any, i: number) => (
                                    <div key={i} className="proactive-tip">
                                        <span className="tip-emoji">{rec.emoji}</span>
                                        <span>{rec.tip}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Predicted Symptoms */}
                        {pmsPrediction.predictions?.slice(0, 3).map((day: any) => (
                            <div key={day.date} className="prediction-day">
                                <div className="prediction-header">
                                    <span className="pred-date">
                                        {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                    </span>
                                    <span className="pred-cycle">Day {day.cycle_day}</span>
                                </div>
                                <div className="predicted-symptoms">
                                    {day.predicted_symptoms.map((sym: any, j: number) => (
                                        <div
                                            key={j}
                                            className="predicted-symptom clickable"
                                            onClick={() => fetchGuidance(sym.symptom)}
                                        >
                                            <span className="symptom-name">{sym.symptom.replace(/_/g, ' ')}</span>
                                            <span className="symptom-likelihood">{sym.likelihood}% likely</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}

                        <p className="prediction-note">
                            Based on {pmsPrediction.data_quality?.cycles_analyzed} cycles analyzed •
                            Confidence: {pmsPrediction.data_quality?.confidence}
                        </p>
                    </div>
                </div>
            )}

            {/* Quick Help - Common Symptoms with Guidance */}
            <div className="quick-help card">
                <div className="card-header">
                    <h3><Lightbulb size={18} /> Quick Help - What to Do</h3>
                    <span className="card-subtitle">Click a symptom for personalized guidance</span>
                </div>
                <div className="card-body">
                    <div className="quick-help-grid">
                        {['cramps', 'headache', 'fatigue', 'bloating', 'mood_swings', 'back_pain', 'nausea', 'breast_tenderness'].map(sym => (
                            <button
                                key={sym}
                                className="quick-help-btn"
                                onClick={() => fetchGuidance(sym)}
                            >
                                <span className="quick-help-name">{sym.replace(/_/g, ' ')}</span>
                                <ChevronRight size={16} />
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Today's Symptoms */}
            {todaySymptoms.length > 0 && (
                <div className="today-symptoms card">
                    <div className="card-header">
                        <h3>Today's Symptoms</h3>
                        <span className="card-subtitle">Click for guidance</span>
                    </div>
                    <div className="card-body">
                        <div className="symptom-chips">
                            {todaySymptoms.map((symptom) => (
                                <div
                                    key={symptom.id}
                                    className="symptom-chip clickable"
                                    onClick={() => fetchGuidance(symptom.symptom_type)}
                                >
                                    <span className="symptom-name">{symptom.symptom_type.replace(/_/g, ' ')}</span>
                                    <span className="symptom-severity">{symptom.severity}/10</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Most Common Symptoms */}
            {analysis?.most_common && analysis.most_common.length > 0 && (
                <div className="common-symptoms card">
                    <div className="card-header">
                        <h3>Most Common (Last 30 Days)</h3>
                        <span className="card-subtitle">Tap for do's & don'ts</span>
                    </div>
                    <div className="card-body">
                        <div className="common-list">
                            {analysis.most_common.map((item, index) => (
                                <div
                                    key={item.symptom}
                                    className="common-item clickable"
                                    onClick={() => fetchGuidance(item.symptom)}
                                >
                                    <span className="rank">#{index + 1}</span>
                                    <span className="name">{item.symptom.replace(/_/g, ' ')}</span>
                                    <span className="count">{item.count}x</span>
                                    <div className="severity-bar">
                                        <div
                                            className="severity-fill"
                                            style={{ width: `${item.avg_severity * 10}%` }}
                                        ></div>
                                    </div>
                                    <ChevronRight size={16} className="chevron" />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Recommendations */}
            {analysis?.recommendations && analysis.recommendations.length > 0 && (
                <div className="recommendations card">
                    <div className="card-header">
                        <h3><AlertTriangle size={18} /> AI Recommendations</h3>
                    </div>
                    <div className="card-body">
                        <ul className="rec-list">
                            {analysis.recommendations.map((rec, index) => (
                                <li key={index}>{rec}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* Recent Symptoms */}
            <div className="recent-symptoms card">
                <div className="card-header">
                    <h3>Recent Symptoms</h3>
                </div>
                <div className="card-body">
                    {symptoms.length > 0 ? (
                        <div className="symptoms-list">
                            {symptoms.slice(0, 10).map((symptom) => (
                                <div
                                    key={symptom.id}
                                    className="symptom-item clickable"
                                    onClick={() => fetchGuidance(symptom.symptom_type)}
                                >
                                    <div className="symptom-info">
                                        <span className="symptom-type">{symptom.symptom_type.replace(/_/g, ' ')}</span>
                                        <span className="symptom-date">{format(new Date(symptom.date), 'MMM d, yyyy')}</span>
                                    </div>
                                    <div className="symptom-meta">
                                        <span className={`severity-badge severity-${Math.ceil(symptom.severity / 3)}`}>
                                            {symptom.severity}/10
                                        </span>
                                        <span className="category-badge">{symptom.category}</span>
                                        <ChevronRight size={16} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>No symptoms logged yet</p>
                            <button className="btn btn-secondary" onClick={() => setShowModal(true)}>
                                Log Your First Symptom
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Symptom Guidance Modal */}
            {showGuidanceModal && (
                <div className="modal-overlay" onClick={() => setShowGuidanceModal(false)}>
                    <div className="modal guidance-modal glass animate-slide-up" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>
                                {guidance?.emoji || '📋'} {guidanceSymptom.replace(/_/g, ' ')}
                            </h2>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowGuidanceModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="modal-body guidance-body">
                            {loadingGuidance ? (
                                <div className="loading-guidance">
                                    <div className="spinner"></div>
                                    <p>Loading personalized guidance...</p>
                                </div>
                            ) : guidance ? (
                                <>
                                    <p className="guidance-description">{guidance.description}</p>

                                    {/* User History */}
                                    {guidance.user_history.times_logged > 0 && (
                                        <div className="user-history-badge">
                                            <UserCheck size={16} />
                                            <span>You've logged this {guidance.user_history.times_logged} times
                                                (avg severity: {guidance.user_history.average_severity}/10)</span>
                                        </div>
                                    )}

                                    {/* What TO DO */}
                                    <div className="guidance-section do-section">
                                        <h4><CheckCircle size={18} /> What TO DO</h4>
                                        <ul>
                                            {guidance.do.map((item, i) => (
                                                <li key={i}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* What NOT to do */}
                                    <div className="guidance-section dont-section">
                                        <h4><XCircle size={18} /> What NOT to Do</h4>
                                        <ul>
                                            {guidance.dont.map((item, i) => (
                                                <li key={i}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Home Remedies */}
                                    <div className="guidance-section remedies-section">
                                        <h4><Heart size={18} /> Home Remedies</h4>
                                        <div className="remedies-grid">
                                            {guidance.remedies.map((remedy, i) => (
                                                <div key={i} className="remedy-card">
                                                    <strong>{remedy.name}</strong>
                                                    <p>{remedy.how}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* When to See Doctor */}
                                    <div className="guidance-section doctor-section">
                                        <h4><AlertTriangle size={18} /> See a Doctor If...</h4>
                                        <ul>
                                            {guidance.see_doctor.map((item, i) => (
                                                <li key={i}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </>
                            ) : (
                                <p>No guidance available</p>
                            )}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowGuidanceModal(false)}>
                                Close
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => {
                                    setShowGuidanceModal(false);
                                    setSelectedSymptom(guidanceSymptom);
                                    setShowModal(true);
                                }}
                            >
                                Log This Symptom
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Log Symptom Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal glass animate-slide-up" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Log Symptom</h2>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Date</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={selectedDate}
                                        onChange={(e) => setSelectedDate(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Category</label>
                                    <div className="category-options">
                                        {symptomCategories.map((cat) => (
                                            <button
                                                key={cat.value}
                                                type="button"
                                                className={`category-option ${selectedCategory === cat.value ? 'active' : ''}`}
                                                onClick={() => {
                                                    setSelectedCategory(cat.value);
                                                    setSelectedSymptom('');
                                                }}
                                            >
                                                <span>{cat.emoji}</span>
                                                <span>{cat.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Symptom</label>
                                    <div className="symptom-options">
                                        {commonSymptoms[selectedCategory]?.map((sym) => (
                                            <button
                                                key={sym}
                                                type="button"
                                                className={`symptom-option ${selectedSymptom === sym ? 'active' : ''}`}
                                                onClick={() => {
                                                    setSelectedSymptom(sym);
                                                    setCustomSymptom('');
                                                }}
                                            >
                                                {sym.replace(/_/g, ' ')}
                                            </button>
                                        ))}
                                    </div>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Or type a custom symptom..."
                                        value={customSymptom}
                                        onChange={(e) => {
                                            setCustomSymptom(e.target.value);
                                            setSelectedSymptom('');
                                        }}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Severity: {severity}/10</label>
                                    <input
                                        type="range"
                                        min="1"
                                        max="10"
                                        value={severity}
                                        onChange={(e) => setSeverity(parseInt(e.target.value))}
                                        className="severity-slider"
                                    />
                                    <div className="severity-labels">
                                        <span>Mild</span>
                                        <span>Moderate</span>
                                        <span>Severe</span>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Notes (optional)</label>
                                    <textarea
                                        className="form-input form-textarea"
                                        placeholder="Any additional details..."
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
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
                                    disabled={(!selectedSymptom && !customSymptom) || createMutation.isPending}
                                >
                                    {createMutation.isPending ? 'Saving...' : 'Log Symptom'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

