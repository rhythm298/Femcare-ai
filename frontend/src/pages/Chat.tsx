/**
 * AI Chat Page - Health Assistant
 */

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../services/api';
import { format } from 'date-fns';
import { MessageCircle, Send, Trash2, Bot, User } from 'lucide-react';
import './Chat.css';

const quickQuestions = [
    "When is my next period?",
    "What's my PCOS risk?",
    "Tell me about my recent symptoms",
    "What recommendations do you have?",
    "What is endometriosis?",
];

export default function Chat() {
    const queryClient = useQueryClient();
    const [message, setMessage] = useState('');
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
                        <MessageCircle size={24} />
                        <div>
                            <h1>AI Health Assistant</h1>
                            <p>Ask me anything about your health</p>
                        </div>
                    </div>
                    {messages.length > 0 && (
                        <button
                            className="btn btn-ghost"
                            onClick={() => clearMutation.mutate()}
                            disabled={clearMutation.isPending}
                        >
                            <Trash2 size={18} />
                            Clear
                        </button>
                    )}
                </div>

                {/* Messages */}
                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="chat-welcome">
                            <div className="welcome-avatar">
                                <Bot size={40} />
                            </div>
                            <h2>Hello! 👋</h2>
                            <p>
                                I'm your personal health assistant. I can help you understand your
                                cycle, symptoms, health risks, and provide personalized recommendations.
                            </p>
                            <div className="quick-questions">
                                <p className="quick-title">Try asking:</p>
                                <div className="quick-buttons">
                                    {quickQuestions.map((q) => (
                                        <button
                                            key={q}
                                            className="quick-btn"
                                            onClick={() => handleQuickQuestion(q)}
                                            disabled={sendMutation.isPending}
                                        >
                                            {q}
                                        </button>
                                    ))}
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
                        </>
                    )}
                </div>

                {/* Input */}
                <form className="chat-input-form" onSubmit={handleSubmit}>
                    <input
                        type="text"
                        className="chat-input"
                        placeholder="Type your message..."
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
