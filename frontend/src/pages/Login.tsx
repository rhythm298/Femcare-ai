/**
 * Login Page
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Heart, Mail, Lock, AlertCircle } from 'lucide-react';
import './Auth.css';

export default function Login() {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login({ email, password });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-background">
                <div className="auth-gradient-1"></div>
                <div className="auth-gradient-2"></div>
            </div>

            <div className="auth-container">
                <div className="auth-card glass">
                    <div className="auth-header">
                        <div className="auth-logo">
                            <Heart className="logo-icon" />
                            <span className="gradient-text">FemCare AI</span>
                        </div>
                        <h1>Welcome Back</h1>
                        <p>Sign in to continue your health journey</p>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {error && (
                            <div className="auth-error animate-slide-up">
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="form-group">
                            <label className="form-label" htmlFor="email">Email</label>
                            <div className="input-with-icon">
                                <Mail size={18} />
                                <input
                                    id="email"
                                    type="email"
                                    className="form-input"
                                    placeholder="Enter your email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="password">Password</label>
                            <div className="input-with-icon">
                                <Lock size={18} />
                                <input
                                    id="password"
                                    type="password"
                                    className="form-input"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
                            {isLoading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Don't have an account?{' '}
                            <Link to="/register">Create one</Link>
                        </p>
                    </div>
                </div>

                <div className="auth-features">
                    <h2>Your Personal Health Companion</h2>
                    <ul>
                        <li>📅 Smart Cycle Tracking & Predictions</li>
                        <li>🩺 AI-Powered Health Risk Assessment</li>
                        <li>💬 24/7 Health Assistant Chat</li>
                        <li>📊 Personalized Insights & Recommendations</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
