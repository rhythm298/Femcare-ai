/**
 * Health Insights Page - Risk scores and recommendations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { insightsApi } from '../services/api';
import {
    LineChart,
    AlertTriangle,
    CheckCircle2,
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronRight,
} from 'lucide-react';
import './Insights.css';

const conditionInfo: Record<string, { name: string; description: string }> = {
    pcos: {
        name: 'PCOS',
        description: 'Polycystic Ovary Syndrome',
    },
    endometriosis: {
        name: 'Endometriosis',
        description: 'Tissue growth outside the uterus',
    },
    anemia: {
        name: 'Anemia',
        description: 'Iron deficiency condition',
    },
    thyroid: {
        name: 'Thyroid',
        description: 'Thyroid hormone imbalance',
    },
};

export default function Insights() {
    const queryClient = useQueryClient();

    const { data: risks, isLoading: risksLoading } = useQuery({
        queryKey: ['risks'],
        queryFn: insightsApi.getRisks,
    });

    const { data: recommendations = [] } = useQuery({
        queryKey: ['recommendations'],
        queryFn: insightsApi.getRecommendations,
    });

    const completeMutation = useMutation({
        mutationFn: insightsApi.completeRecommendation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['recommendations'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
    });

    const getRiskLevel = (score: number) => {
        if (score < 0.3) return { level: 'Low', class: 'low', color: 'var(--color-success)' };
        if (score < 0.6) return { level: 'Medium', class: 'medium', color: 'var(--color-warning)' };
        return { level: 'High', class: 'high', color: 'var(--color-error)' };
    };

    const getTrendIcon = (trend?: string) => {
        if (!trend) return null;
        switch (trend) {
            case 'improving': return <TrendingDown className="trend improving" />;
            case 'worsening': return <TrendingUp className="trend worsening" />;
            default: return <Minus className="trend stable" />;
        }
    };

    if (risksLoading) {
        return (
            <div className="insights-page">
                <div className="page-header">
                    <h1><LineChart size={28} /> Health Insights</h1>
                </div>
                <div className="skeleton-grid">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="skeleton" style={{ height: 200 }}></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="insights-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1><LineChart size={28} /> Health Insights</h1>
                    <p>AI-powered health risk assessment and recommendations</p>
                </div>
                <div className="health-score-display">
                    <span className="score-value">{risks?.overall_health_score?.toFixed(0) || '--'}</span>
                    <span className="score-label">Health Score</span>
                </div>
            </div>

            {/* Priority Concerns */}
            {risks?.priority_concerns && risks.priority_concerns.length > 0 && (
                <div className="concerns-banner">
                    <AlertTriangle size={20} />
                    <div>
                        <strong>Areas to Monitor:</strong>
                        <span>{risks.priority_concerns.join(' • ')}</span>
                    </div>
                </div>
            )}

            {/* Risk Cards */}
            <div className="risk-cards">
                {Object.entries(conditionInfo).map(([key, info]) => {
                    const riskData = risks?.[key as keyof typeof risks];
                    if (!riskData || typeof riskData !== 'object') return null;

                    const score = (riskData as any).score || 0;
                    const confidence = (riskData as any).confidence || 0;
                    const factors = (riskData as any).factors || [];
                    const risk = getRiskLevel(score);

                    return (
                        <div key={key} className={`risk-card ${risk.class}`}>
                            <div className="risk-card-header">
                                <div>
                                    <h3>{info.name}</h3>
                                    <p>{info.description}</p>
                                </div>
                                <div className={`risk-level-badge ${risk.class}`}>
                                    {risk.level}
                                </div>
                            </div>

                            <div className="risk-gauge-large">
                                <div className="gauge-track">
                                    <div
                                        className={`gauge-fill ${risk.class}`}
                                        style={{ width: `${score * 100}%` }}
                                    ></div>
                                </div>
                                <div className="gauge-labels">
                                    <span>0%</span>
                                    <span className="gauge-value">{(score * 100).toFixed(0)}%</span>
                                    <span>100%</span>
                                </div>
                            </div>

                            <div className="risk-meta">
                                <span className="confidence">
                                    Confidence: {(confidence * 100).toFixed(0)}%
                                </span>
                            </div>

                            {factors.length > 0 && (
                                <div className="risk-factors">
                                    <h4>Contributing Factors:</h4>
                                    <ul>
                                        {factors.slice(0, 3).map((factor: any, i: number) => (
                                            <li key={i}>
                                                <span className={`impact ${factor.impact}`}>●</span>
                                                {factor.factor}
                                                {factor.value && <span className="factor-value">{factor.value}</span>}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Recommendations */}
            {recommendations.length > 0 && (
                <div className="recommendations-section card">
                    <div className="card-header">
                        <h3><CheckCircle2 size={20} /> Recommendations</h3>
                    </div>
                    <div className="card-body">
                        <div className="recommendations-list">
                            {recommendations.map((rec) => (
                                <div key={rec.id} className={`recommendation-item priority-${Math.ceil(rec.priority / 3)}`}>
                                    <div className="rec-content">
                                        <div className="rec-header">
                                            <h4>{rec.title}</h4>
                                            <span className="rec-category">{rec.category}</span>
                                        </div>
                                        <p>{rec.description}</p>
                                        {rec.action_steps && rec.action_steps.length > 0 && (
                                            <ul className="action-steps">
                                                {rec.action_steps.map((step, i) => (
                                                    <li key={i}>{step}</li>
                                                ))}
                                            </ul>
                                        )}
                                        {rec.reason && (
                                            <p className="rec-reason">💡 {rec.reason}</p>
                                        )}
                                    </div>
                                    <button
                                        className="btn btn-ghost complete-btn"
                                        onClick={() => completeMutation.mutate(rec.id)}
                                        disabled={completeMutation.isPending}
                                    >
                                        <CheckCircle2 size={18} />
                                        Done
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
