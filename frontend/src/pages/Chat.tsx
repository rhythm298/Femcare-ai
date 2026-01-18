/**
 * AI Chat Page - Health Assistant
 * Interactive AI-powered health companion
 */

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../services/api';
import { format } from 'date-fns';
import { MessageCircle, Send, Trash2, Bot, User, Heart, Calendar, Activity, Droplets, Apple, Moon, Sparkles } from 'lucide-react';
import './Chat.css';

// Quick action categories
const quickActions = [
    {
        icon: '📅',
        label: 'Period',
        questions: [
            "When is my next period?",
            "How long is my average cycle?",
            "Am I fertile right now?"
        ]
    },
    {
        icon: '💊',
        label: 'Symptoms',
        questions: [
            "What do my symptoms mean?",
            "How can I relieve cramps?",
            "Is this symptom normal?"
        ]
    },
    {
        icon: '🏃‍♀️',
        label: 'Exercise',
        questions: [
            "What exercises are best for me today?",
            "Can I work out during my period?",
            "What's my exercise streak?"
        ]
    },
    {
        icon: '🍎',
        label: 'Nutrition',
        questions: [
            "What should I eat this phase?",
            "Foods to avoid during period?",
            "How are my calories today?"
        ]
    },
    {
        icon: '⚠️',
        label: 'Health Risk',
        questions: [
            "What's my PCOS risk?",
            "Should I see a doctor?",
            "What are endometriosis symptoms?"
        ]
    },
    {
        icon: '💡',
        label: 'Tips',
        questions: [
            "Give me self-care tips",
            "How to sleep better?",
            "Stress management advice"
        ]
    }
];

export default function Chat() {
    const queryClient = useQueryClient();
    const [message, setMessage] = useState('');
    const [activeCategory, setActiveCategory] = useState<number | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const { data: messages = [], isLoading } = useQuery({
        queryKey: ['chatHistory'],
        queryFn: () => chatApi.getHistory(),
    });

    const sendMutation = useMutation({
        mutationFn: (content: string) => chatApi.sendMessage(content),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['chatHistory'] });
            setMessage('');
            setActiveCategory(null);
        },
    });

    const clearMutation = useMutation({
        mutationFn: chatApi.clearHistory,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['chatHistory'] });
        },
    });

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim() || sendMutation.isPending) return;
        sendMutation.mutate(message.trim());
    };

    const handleQuickQuestion = (question: string) => {
        sendMutation.mutate(question);
    };

    return (
        <div className="chat-page animate-fade-in">
            <div className="chat-container">
                {/* Header */}
                <div className="chat-header">
                    <div className="chat-title">
                        <div className="ai-avatar">
                            <Bot size={24} />
                            <span className="online-dot"></span>
                        </div>
                        <div>
                            <h1>FemCare AI</h1>
                            <p className="status-text">
                                <Sparkles size={12} /> Always here to help
                            </p>
                        </div>
                    </div>
                    {messages.length > 0 && (
                        <button
                            className="btn btn-ghost"
                            onClick={() => clearMutation.mutate()}
                            disabled={clearMutation.isPending}
                        >
                            <Trash2 size={18} />
                        </button>
                    )}
                </div>

                {/* Messages */}
                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="chat-welcome">
                            <div className="welcome-header">
                                <div className="welcome-avatar">
                                    <Bot size={48} />
                                </div>
                                <h2>Hi there! 👋</h2>
                                <p className="welcome-subtitle">
                                    I'm your personal health companion. How can I help you today?
                                </p>
                            </div>

                            {/* Quick Action Cards */}
                            <div className="quick-actions-grid">
                                {quickActions.map((action, idx) => (
                                    <button
                                        key={idx}
                                        className={`quick-action-card ${activeCategory === idx ? 'active' : ''}`}
                                        onClick={() => setActiveCategory(activeCategory === idx ? null : idx)}
                                    >
                                        <span className="action-icon">{action.icon}</span>
                                        <span className="action-label">{action.label}</span>
                                    </button>
                                ))}
                            </div>

                            {/* Expanded Questions */}
                            {activeCategory !== null && (
                                <div className="expanded-questions animate-fade-in">
                                    <h3>Ask about {quickActions[activeCategory].label}:</h3>
                                    <div className="question-buttons">
                                        {quickActions[activeCategory].questions.map((q, i) => (
                                            <button
                                                key={i}
                                                className="question-btn"
                                                onClick={() => handleQuickQuestion(q)}
                                                disabled={sendMutation.isPending}
                                            >
                                                {q}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Smart Suggestions based on time */}
                            <div className="smart-suggestions">
                                <h3>💡 Suggested for you:</h3>
                                <div className="suggestion-chips">
                                    <button
                                        className="suggestion-chip"
                                        onClick={() => handleQuickQuestion("How am I doing today?")}
                                        disabled={sendMutation.isPending}
                                    >
                                        <Moon size={14} /> Daily check-in
                                    </button>
                                    <button
                                        className="suggestion-chip"
                                        onClick={() => handleQuickQuestion("Give me personalized recommendations")}
                                        disabled={sendMutation.isPending}
                                    >
                                        <Heart size={14} /> Get recommendations
                                    </button>
                                    <button
                                        className="suggestion-chip"
                                        onClick={() => handleQuickQuestion("Explain my current cycle phase")}
                                        disabled={sendMutation.isPending}
                                    >
                                        <Calendar size={14} /> Cycle insights
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`message ${msg.role === 'user' ? 'user' : 'assistant'}`}
                                >
                                    <div className="message-avatar">
                                        {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                                    </div>
                                    <div className="message-content">
                                        <div className="message-text">
                                            {msg.content.split('\n').map((line, i) => (
                                                <p key={i}>{line}</p>
                                            ))}
                                        </div>
                                        <span className="message-time">
                                            {format(new Date(msg.created_at), 'h:mm a')}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {sendMutation.isPending && (
                                <div className="message assistant">
                                    <div className="message-avatar">
                                        <Bot size={20} />
                                    </div>
                                    <div className="message-content">
                                        <div className="typing-indicator">
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />

                            {/* Show quick actions below messages too */}
                            <div className="inline-quick-actions">
                                <button
                                    className="inline-action"
                                    onClick={() => handleQuickQuestion("Tell me more")}
                                    disabled={sendMutation.isPending}
                                >
                                    Tell me more
                                </button>
                                <button
                                    className="inline-action"
                                    onClick={() => handleQuickQuestion("What else should I know?")}
                                    disabled={sendMutation.isPending}
                                >
                                    What else?
                                </button>
                                <button
                                    className="inline-action"
                                    onClick={() => handleQuickQuestion("Give me an action plan")}
                                    disabled={sendMutation.isPending}
                                >
                                    Action plan
                                </button>
                            </div>
                        </>
                    )}
                </div>

                {/* Input */}
                <form className="chat-input-form" onSubmit={handleSubmit}>
                    <input
                        type="text"
                        className="chat-input"
                        placeholder="Ask me anything about your health..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        disabled={sendMutation.isPending}
                    />
                    <button
                        type="submit"
                        className="btn btn-primary send-btn"
                        disabled={!message.trim() || sendMutation.isPending}
                    >
                        <Send size={20} />
                    </button>
                </form>
            </div>
        </div>
    );
}
