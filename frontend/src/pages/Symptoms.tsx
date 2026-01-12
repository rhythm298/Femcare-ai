/**
 * Symptoms Page - Log and track symptoms
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
} from 'lucide-react';
import './Symptoms.css';

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
    const [selectedCategory, setSelectedCategory] = useState<SymptomCategory>('physical');
    const [selectedSymptom, setSelectedSymptom] = useState('');
    const [customSymptom, setCustomSymptom] = useState('');
    const [severity, setSeverity] = useState(5);
    const [description, setDescription] = useState('');
    const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));

    const { data: symptoms = [], isLoading } = useQuery({
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

            {/* Today's Symptoms */}
            {todaySymptoms.length > 0 && (
                <div className="today-symptoms card">
                    <div className="card-header">
                        <h3>Today's Symptoms</h3>
                    </div>
                    <div className="card-body">
                        <div className="symptom-chips">
                            {todaySymptoms.map((symptom) => (
                                <div key={symptom.id} className="symptom-chip">
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
                    </div>
                    <div className="card-body">
                        <div className="common-list">
                            {analysis.most_common.map((item, index) => (
                                <div key={item.symptom} className="common-item">
                                    <span className="rank">#{index + 1}</span>
                                    <span className="name">{item.symptom.replace(/_/g, ' ')}</span>
                                    <span className="count">{item.count}x</span>
                                    <div className="severity-bar">
                                        <div
                                            className="severity-fill"
                                            style={{ width: `${item.avg_severity * 10}%` }}
                                        ></div>
                                    </div>
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
                                <div key={symptom.id} className="symptom-item">
                                    <div className="symptom-info">
                                        <span className="symptom-type">{symptom.symptom_type.replace(/_/g, ' ')}</span>
                                        <span className="symptom-date">{format(new Date(symptom.date), 'MMM d, yyyy')}</span>
                                    </div>
                                    <div className="symptom-meta">
                                        <span className={`severity-badge severity-${Math.ceil(symptom.severity / 3)}`}>
                                            {symptom.severity}/10
                                        </span>
                                        <span className="category-badge">{symptom.category}</span>
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
