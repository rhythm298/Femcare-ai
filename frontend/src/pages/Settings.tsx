/**
 * Settings Page - User profile and preferences
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { UserUpdate } from '../types';
import {
    Settings as SettingsIcon,
    User,
    Bell,
    Shield,
    Download,
    Trash2,
    Save,
    CheckCircle,
} from 'lucide-react';
import './Settings.css';

export default function Settings() {
    const { user, updateUser, logout } = useAuth();
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState('profile');
    const [successMessage, setSuccessMessage] = useState('');

    // Profile form state
    const [name, setName] = useState(user?.name || '');
    const [dateOfBirth, setDateOfBirth] = useState(user?.date_of_birth || '');
    const [weight, setWeight] = useState(user?.weight?.toString() || '');
    const [height, setHeight] = useState(user?.height?.toString() || '');

    // Health context
    const [hasGivenBirth, setHasGivenBirth] = useState(user?.has_given_birth || false);
    const [isPregnant, setIsPregnant] = useState(user?.is_pregnant || false);
    const [isTryingToConceive, setIsTryingToConceive] = useState(user?.is_trying_to_conceive || false);
    const [isOnBirthControl, setIsOnBirthControl] = useState(user?.is_on_birth_control || false);

    // Notifications
    const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(user?.notification_enabled ?? true);
    const [partnerSharing, setPartnerSharing] = useState(user?.partner_sharing_enabled || false);

    const updateMutation = useMutation({
        mutationFn: (data: UserUpdate) => authApi.updateProfile(data),
        onSuccess: (updatedUser) => {
            updateUser(updatedUser);
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
            setSuccessMessage('Settings saved successfully!');
            setTimeout(() => setSuccessMessage(''), 3000);
        },
    });

    const handleSaveProfile = () => {
        updateMutation.mutate({
            name,
            date_of_birth: dateOfBirth || undefined,
            weight: weight ? parseFloat(weight) : undefined,
            height: height ? parseFloat(height) : undefined,
            has_given_birth: hasGivenBirth,
            is_pregnant: isPregnant,
            is_trying_to_conceive: isTryingToConceive,
            is_on_birth_control: isOnBirthControl,
            notification_enabled: notificationsEnabled,
            partner_sharing_enabled: partnerSharing,
        });
    };

    const handleExportData = () => {
        // In a real app, this would call an export endpoint
        alert('Data export feature coming soon!');
    };

    const handleDeleteAccount = () => {
        if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            authApi.deleteAccount().then(() => {
                logout();
            });
        }
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'privacy', label: 'Privacy & Data', icon: Shield },
    ];

    return (
        <div className="settings-page animate-fade-in">
            <div className="page-header">
                <h1><SettingsIcon size={28} /> Settings</h1>
            </div>

            {successMessage && (
                <div className="success-message animate-slide-up">
                    <CheckCircle size={18} />
                    {successMessage}
                </div>
            )}

            <div className="settings-layout">
                {/* Tabs */}
                <div className="settings-tabs">
                    {tabs.map(({ id, label, icon: Icon }) => (
                        <button
                            key={id}
                            className={`tab-btn ${activeTab === id ? 'active' : ''}`}
                            onClick={() => setActiveTab(id)}
                        >
                            <Icon size={18} />
                            {label}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="settings-content card">
                    {activeTab === 'profile' && (
                        <div className="settings-section">
                            <h2>Profile Information</h2>
                            <p className="section-desc">Manage your personal details</p>

                            <div className="form-grid">
                                <div className="form-group">
                                    <label className="form-label">Full Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Email</label>
                                    <input
                                        type="email"
                                        className="form-input"
                                        value={user?.email || ''}
                                        disabled
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Date of Birth</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={dateOfBirth}
                                        onChange={(e) => setDateOfBirth(e.target.value)}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Weight (kg)</label>
                                    <input
                                        type="number"
                                        className="form-input"
                                        value={weight}
                                        onChange={(e) => setWeight(e.target.value)}
                                        placeholder="e.g., 60"
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Height (cm)</label>
                                    <input
                                        type="number"
                                        className="form-input"
                                        value={height}
                                        onChange={(e) => setHeight(e.target.value)}
                                        placeholder="e.g., 165"
                                    />
                                </div>
                            </div>

                            <h3>Health Context</h3>
                            <p className="section-desc">Help us personalize your experience</p>

                            <div className="toggle-group">
                                <label className="toggle-item">
                                    <input
                                        type="checkbox"
                                        checked={hasGivenBirth}
                                        onChange={(e) => setHasGivenBirth(e.target.checked)}
                                    />
                                    <span className="toggle-label">I have given birth before</span>
                                </label>

                                <label className="toggle-item">
                                    <input
                                        type="checkbox"
                                        checked={isPregnant}
                                        onChange={(e) => setIsPregnant(e.target.checked)}
                                    />
                                    <span className="toggle-label">I am currently pregnant</span>
                                </label>

                                <label className="toggle-item">
                                    <input
                                        type="checkbox"
                                        checked={isTryingToConceive}
                                        onChange={(e) => setIsTryingToConceive(e.target.checked)}
                                    />
                                    <span className="toggle-label">I am trying to conceive</span>
                                </label>

                                <label className="toggle-item">
                                    <input
                                        type="checkbox"
                                        checked={isOnBirthControl}
                                        onChange={(e) => setIsOnBirthControl(e.target.checked)}
                                    />
                                    <span className="toggle-label">I am on birth control</span>
                                </label>
                            </div>

                            <button
                                className="btn btn-primary save-btn"
                                onClick={handleSaveProfile}
                                disabled={updateMutation.isPending}
                            >
                                <Save size={18} />
                                {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    )}

                    {activeTab === 'notifications' && (
                        <div className="settings-section">
                            <h2>Notification Preferences</h2>
                            <p className="section-desc">Control how we communicate with you</p>

                            <div className="toggle-group">
                                <label className="toggle-item">
                                    <input
                                        type="checkbox"
                                        checked={notificationsEnabled}
                                        onChange={(e) => setNotificationsEnabled(e.target.checked)}
                                    />
                                    <span className="toggle-label">Enable notifications</span>
                                    <span className="toggle-desc">Get reminders for period tracking and health insights</span>
                                </label>
                            </div>

                            <button
                                className="btn btn-primary save-btn"
                                onClick={handleSaveProfile}
                                disabled={updateMutation.isPending}
                            >
                                <Save size={18} />
                                Save Changes
                            </button>
                        </div>
                    )}

                    {activeTab === 'privacy' && (
                        <div className="settings-section">
                            <h2>Privacy & Data</h2>
                            <p className="section-desc">Manage your data and privacy settings</p>

                            <div className="data-actions">
                                <button className="btn btn-secondary" onClick={handleExportData}>
                                    <Download size={18} />
                                    Export My Data
                                </button>

                                <button className="btn btn-ghost danger-btn" onClick={handleDeleteAccount}>
                                    <Trash2 size={18} />
                                    Delete Account
                                </button>
                            </div>

                            <div className="privacy-note">
                                <p>
                                    <strong>🔒 Your Privacy Matters</strong><br />
                                    All your data is stored locally on your device. We never share your
                                    personal health information with third parties.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
