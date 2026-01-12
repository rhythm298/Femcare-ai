/**
 * Register Page
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Heart, Mail, Lock, User, AlertCircle } from 'lucide-react';
import './Auth.css';

export default function Register() {
    const { register } = useAuth();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setIsLoading(true);

        try {
            await register({ name, email, password });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
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
                        <h1>Create Account</h1>
                        <p>Start your personalized health journey</p>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {error && (
                            <div className="auth-error animate-slide-up">
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="form-group">
                            <label className="form-label" htmlFor="name">Full Name</label>
                            <div className="input-with-icon">
                                <User size={18} />
                                <input
                                    id="name"
                                    type="text"
                                    className="form-input"
                                    placeholder="Enter your name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

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
                                    placeholder="Create a password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
                            <div className="input-with-icon">
                                <Lock size={18} />
                                <input
                                    id="confirmPassword"
                                    type="password"
                                    className="form-input"
                                    placeholder="Confirm your password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
                            {isLoading ? 'Creating Account...' : 'Create Account'}
                        </button>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Already have an account?{' '}
                            <Link to="/login">Sign in</Link>
                        </p>
                    </div>
                </div>

                <div className="auth-features">
                    <h2>Why Join FemCare AI?</h2>
                    <ul>
                        <li>🔒 100% Private - All data stored locally</li>
                        <li>🤖 AI-Powered Health Insights</li>
                        <li>📱 Track cycles, symptoms & more</li>
                        <li>💡 Personalized recommendations</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
