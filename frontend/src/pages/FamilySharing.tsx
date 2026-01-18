/**
 * Family Sharing Page - Manage family access to health data
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Users,
    UserPlus,
    Share2,
    Settings,
    Trash2,
    Copy,
    Check,
    X,
    Eye,
    EyeOff,
    Heart,
    Activity,
    Moon,
    Apple,
    Calendar
} from 'lucide-react';
import './FamilySharing.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('femcare_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const familyApi = {
    getMembers: async () => {
        const response = await fetch(`${API_BASE_URL}/family/members`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch members');
        return response.json();
    },
    inviteMember: async (data: {
        member_email: string;
        member_name: string;
        relationship: string;
        can_view_mood?: boolean;
        can_view_symptoms?: boolean;
        can_view_exercise?: boolean;
        can_view_cycle?: boolean;
        can_view_nutrition?: boolean;
    }) => {
        const params = new URLSearchParams();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined) {
                // Map 'relationship' to 'relation_type' for backend
                const paramKey = key === 'relationship' ? 'relation_type' : key;
                params.set(paramKey, String(value));
            }
        });
        const response = await fetch(`${API_BASE_URL}/family/invite?${params}`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to invite member');
        return response.json();
    },
    updatePermissions: async (memberId: number, permissions: Record<string, boolean>) => {
        const params = new URLSearchParams();
        Object.entries(permissions).forEach(([key, value]) => {
            params.set(key, String(value));
        });
        const response = await fetch(`${API_BASE_URL}/family/permissions/${memberId}?${params}`, {
            method: 'PUT',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to update permissions');
        return response.json();
    },
    removeMember: async (memberId: number) => {
        const response = await fetch(`${API_BASE_URL}/family/members/${memberId}`, {
            method: 'DELETE',
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to remove member');
        return response.json();
    }
};

interface FamilyMember {
    id: number;
    member_name: string;
    member_email: string;
    relationship: string;
    invite_code: string;
    invite_status: 'pending' | 'accepted' | 'declined';
    permissions: {
        can_view_mood?: boolean;
        can_view_symptoms?: boolean;
        can_view_exercise?: boolean;
        can_view_cycle?: boolean;
        can_view_nutrition?: boolean;
    };
    created_at: string;
    accepted_at: string | null;
}

const relationships = [
    { id: 'mother', label: 'Mother', emoji: '👩' },
    { id: 'father', label: 'Father', emoji: '👨' },
    { id: 'sister', label: 'Sister', emoji: '👧' },
    { id: 'brother', label: 'Brother', emoji: '👦' },
    { id: 'partner', label: 'Partner', emoji: '💕' },
    { id: 'husband', label: 'Husband', emoji: '👫' },
    { id: 'wife', label: 'Wife', emoji: '👫' },
    { id: 'friend', label: 'Friend', emoji: '🤝' },
    { id: 'other', label: 'Other', emoji: '👤' }
];

const permissionItems = [
    { key: 'can_view_mood', label: 'Mood', icon: Moon, description: 'Your daily mood and energy levels' },
    { key: 'can_view_symptoms', label: 'Symptoms', icon: Activity, description: 'Logged symptoms and severity' },
    { key: 'can_view_exercise', label: 'Exercise', icon: Activity, description: 'Workout logs and streaks' },
    { key: 'can_view_cycle', label: 'Cycle', icon: Calendar, description: 'Current cycle day and phase' },
    { key: 'can_view_nutrition', label: 'Nutrition', icon: Apple, description: 'Food and calorie logs' }
];

export default function FamilySharing() {
    const queryClient = useQueryClient();
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [showPermissionsModal, setShowPermissionsModal] = useState(false);
    const [selectedMember, setSelectedMember] = useState<FamilyMember | null>(null);
    const [copiedCode, setCopiedCode] = useState<string | null>(null);

    // Invite form state
    const [inviteForm, setInviteForm] = useState({
        member_name: '',
        member_email: '',
        relationship: 'mother',
        can_view_mood: true,
        can_view_symptoms: true,
        can_view_exercise: true,
        can_view_cycle: true,
        can_view_nutrition: false
    });

    const { data: membersData, isLoading } = useQuery({
        queryKey: ['familyMembers'],
        queryFn: familyApi.getMembers
    });

    const inviteMutation = useMutation({
        mutationFn: familyApi.inviteMember,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['familyMembers'] });
            setShowInviteModal(false);
            setInviteForm({
                member_name: '',
                member_email: '',
                relationship: 'mother',
                can_view_mood: true,
                can_view_symptoms: true,
                can_view_exercise: true,
                can_view_cycle: true,
                can_view_nutrition: false
            });
        }
    });

    const updatePermissionsMutation = useMutation({
        mutationFn: ({ memberId, permissions }: { memberId: number; permissions: Record<string, boolean> }) =>
            familyApi.updatePermissions(memberId, permissions),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['familyMembers'] });
        }
    });

    const removeMutation = useMutation({
        mutationFn: familyApi.removeMember,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['familyMembers'] });
        }
    });

    const handleCopyLink = (inviteCode: string) => {
        const link = `${window.location.origin}/family-view/${inviteCode}`;
        navigator.clipboard.writeText(link);
        setCopiedCode(inviteCode);
        setTimeout(() => setCopiedCode(null), 2000);
    };

    const handleTogglePermission = (memberId: number, permissionKey: string, currentValue: boolean) => {
        updatePermissionsMutation.mutate({
            memberId,
            permissions: { [permissionKey]: !currentValue }
        });
    };

    const handleEditPermissions = (member: FamilyMember) => {
        setSelectedMember(member);
        setShowPermissionsModal(true);
    };

    const members = membersData?.members || [];

    return (
        <div className="family-page animate-fade-in">
            {/* Header */}
            <div className="family-header">
                <div>
                    <h1><Users size={28} /> Family Sharing</h1>
                    <p>Share your health journey with trusted family members</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowInviteModal(true)}>
                    <UserPlus size={18} /> Invite Family
                </button>
            </div>

            {/* Info Card */}
            <div className="info-card">
                <Share2 size={24} />
                <div>
                    <h3>Keep Your Family in the Loop</h3>
                    <p>
                        When you share access with family members, they can see your selected health data
                        and receive personalized care suggestions based on your cycle phase.
                        Real-time updates help them understand and support you better.
                    </p>
                </div>
            </div>

            {/* Members List */}
            <section className="members-section">
                <h2>Family Members ({members.length})</h2>

                {isLoading ? (
                    <div className="loading-state">Loading...</div>
                ) : members.length === 0 ? (
                    <div className="empty-state">
                        <Users size={48} />
                        <h3>No family members yet</h3>
                        <p>Invite your first family member to start sharing your health journey.</p>
                        <button className="btn btn-primary" onClick={() => setShowInviteModal(true)}>
                            <UserPlus size={18} /> Invite Someone
                        </button>
                    </div>
                ) : (
                    <div className="members-grid">
                        {members.map((member: FamilyMember) => (
                            <div key={member.id} className="member-card">
                                <div className="member-header">
                                    <div className="member-avatar">
                                        {relationships.find(r => r.id === member.relationship)?.emoji || '👤'}
                                    </div>
                                    <div className="member-info">
                                        <h3>{member.member_name}</h3>
                                        <span className="relationship">{member.relationship}</span>
                                        <span className={`status-badge ${member.invite_status}`}>
                                            {member.invite_status}
                                        </span>
                                    </div>
                                </div>

                                <div className="member-permissions">
                                    <h4>Sharing Access</h4>
                                    <div className="permission-toggles">
                                        {permissionItems.map(perm => (
                                            <button
                                                key={perm.key}
                                                className={`permission-toggle ${member.permissions[perm.key as keyof typeof member.permissions] ? 'active' : ''}`}
                                                onClick={() => handleTogglePermission(
                                                    member.id,
                                                    perm.key,
                                                    member.permissions[perm.key as keyof typeof member.permissions] || false
                                                )}
                                                title={perm.description}
                                            >
                                                {member.permissions[perm.key as keyof typeof member.permissions] ? (
                                                    <Eye size={14} />
                                                ) : (
                                                    <EyeOff size={14} />
                                                )}
                                                {perm.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="member-actions">
                                    <button
                                        className="action-btn copy"
                                        onClick={() => handleCopyLink(member.invite_code)}
                                    >
                                        {copiedCode === member.invite_code ? (
                                            <><Check size={16} /> Copied!</>
                                        ) : (
                                            <><Copy size={16} /> Copy Link</>
                                        )}
                                    </button>
                                    <button
                                        className="action-btn whatsapp"
                                        onClick={() => {
                                            const link = `${window.location.origin}/family-view/${member.invite_code}`;
                                            const message = `Hi! I'd like to share my health journey with you through FemCare AI. Click here to see my updates: ${link}`;
                                            window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
                                        }}
                                        title="Share via WhatsApp"
                                    >
                                        📱 WhatsApp
                                    </button>
                                    <button
                                        className="action-btn settings"
                                        onClick={() => handleEditPermissions(member)}
                                    >
                                        <Settings size={16} />
                                    </button>
                                    <button
                                        className="action-btn delete"
                                        onClick={() => removeMutation.mutate(member.id)}
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* Privacy Note */}
            <div className="privacy-note">
                <Heart size={20} />
                <p>
                    <strong>Your privacy matters.</strong> You have full control over what each family member
                    can see. They only receive care suggestions based on your current phase, never raw
                    medical data. You can revoke access anytime.
                </p>
            </div>

            {/* Invite Modal */}
            {showInviteModal && (
                <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
                    <div className="modal invite-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Invite Family Member</h3>
                            <button className="close-btn" onClick={() => setShowInviteModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Name *</label>
                                <input
                                    type="text"
                                    value={inviteForm.member_name}
                                    onChange={e => setInviteForm({ ...inviteForm, member_name: e.target.value })}
                                    placeholder="Their name"
                                />
                            </div>
                            <div className="form-group">
                                <label>Email</label>
                                <input
                                    type="email"
                                    value={inviteForm.member_email}
                                    onChange={e => setInviteForm({ ...inviteForm, member_email: e.target.value })}
                                    placeholder="their@email.com"
                                />
                            </div>
                            <div className="form-group">
                                <label>Relationship</label>
                                <div className="relationship-options">
                                    {relationships.map(rel => (
                                        <button
                                            key={rel.id}
                                            className={`relationship-option ${inviteForm.relationship === rel.id ? 'active' : ''}`}
                                            onClick={() => setInviteForm({ ...inviteForm, relationship: rel.id })}
                                        >
                                            <span className="emoji">{rel.emoji}</span>
                                            <span className="label">{rel.label}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="form-group">
                                <label>What can they see?</label>
                                <div className="permission-checkboxes">
                                    {permissionItems.map(perm => (
                                        <label key={perm.key} className="permission-checkbox">
                                            <input
                                                type="checkbox"
                                                checked={inviteForm[perm.key as keyof typeof inviteForm] as boolean}
                                                onChange={e => setInviteForm({
                                                    ...inviteForm,
                                                    [perm.key]: e.target.checked
                                                })}
                                            />
                                            <span className="checkmark"></span>
                                            <span className="perm-label">{perm.label}</span>
                                            <span className="perm-desc">{perm.description}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowInviteModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => inviteMutation.mutate(inviteForm)}
                                disabled={!inviteForm.member_name || inviteMutation.isPending}
                            >
                                {inviteMutation.isPending ? 'Sending...' : 'Send Invite'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Permissions Modal */}
            {showPermissionsModal && selectedMember && (
                <div className="modal-overlay" onClick={() => setShowPermissionsModal(false)}>
                    <div className="modal permissions-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Manage Permissions for {selectedMember.member_name}</h3>
                            <button className="close-btn" onClick={() => setShowPermissionsModal(false)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <p className="modal-description">
                                Control exactly what {selectedMember.member_name} can see about your health journey.
                            </p>
                            <div className="permission-list">
                                {permissionItems.map(perm => {
                                    const Icon = perm.icon;
                                    const isEnabled = selectedMember.permissions[perm.key as keyof typeof selectedMember.permissions];
                                    return (
                                        <div key={perm.key} className="permission-row">
                                            <div className="permission-info">
                                                <Icon size={20} />
                                                <div>
                                                    <span className="perm-name">{perm.label}</span>
                                                    <span className="perm-desc">{perm.description}</span>
                                                </div>
                                            </div>
                                            <button
                                                className={`toggle-switch ${isEnabled ? 'on' : 'off'}`}
                                                onClick={() => handleTogglePermission(
                                                    selectedMember.id,
                                                    perm.key,
                                                    isEnabled || false
                                                )}
                                            >
                                                <span className="toggle-knob"></span>
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-primary" onClick={() => setShowPermissionsModal(false)}>
                                Done
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
