/**
 * API service for FemCare AI backend communication
 */

import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
    User,
    UserUpdate,
    LoginCredentials,
    RegisterData,
    AuthToken,
    CycleEntry,
    CycleCreate,
    CyclePrediction,
    CyclePatterns,
    CurrentCycle,
    Symptom,
    SymptomCreate,
    SymptomAnalysis,
    SymptomTypes,
    RiskAssessment,
    Recommendation,
    HealthTimeline,
    ChatMessage,
    DashboardSummary,
} from '../types';

// API base URL - uses environment variable in production, /api proxy for local dev
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('femcare_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('femcare_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// ============== Auth API ==============

export const authApi = {
    register: async (data: RegisterData): Promise<User> => {
        const response = await api.post('/auth/register', data);
        return response.data;
    },

    login: async (credentials: LoginCredentials): Promise<AuthToken> => {
        const response = await api.post('/auth/login', credentials);
        return response.data;
    },

    getProfile: async (): Promise<User> => {
        const response = await api.get('/auth/profile');
        return response.data;
    },

    updateProfile: async (data: UserUpdate): Promise<User> => {
        const response = await api.put('/auth/profile', data);
        return response.data;
    },

    deleteAccount: async (): Promise<void> => {
        await api.delete('/auth/account');
    },
};

// ============== Cycles API ==============

export const cyclesApi = {
    create: async (data: CycleCreate): Promise<CycleEntry> => {
        const response = await api.post('/cycles/', data);
        return response.data;
    },

    getAll: async (skip = 0, limit = 50): Promise<CycleEntry[]> => {
        const response = await api.get('/cycles/', { params: { skip, limit } });
        return response.data;
    },

    getCurrent: async (): Promise<CurrentCycle> => {
        const response = await api.get('/cycles/current');
        return response.data;
    },

    getPrediction: async (): Promise<CyclePrediction> => {
        const response = await api.get('/cycles/prediction');
        return response.data;
    },

    getPatterns: async (): Promise<CyclePatterns> => {
        const response = await api.get('/cycles/patterns');
        return response.data;
    },

    update: async (id: number, data: Partial<CycleCreate>): Promise<CycleEntry> => {
        const response = await api.put(`/cycles/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await api.delete(`/cycles/${id}`);
    },
};

// ============== Symptoms API ==============

export const symptomsApi = {
    create: async (data: SymptomCreate): Promise<Symptom> => {
        const response = await api.post('/symptoms/', data);
        return response.data;
    },

    getAll: async (params?: {
        start_date?: string;
        end_date?: string;
        category?: string;
        skip?: number;
        limit?: number;
    }): Promise<Symptom[]> => {
        const response = await api.get('/symptoms/', { params });
        return response.data;
    },

    getToday: async (): Promise<Symptom[]> => {
        const response = await api.get('/symptoms/today');
        return response.data;
    },

    getAnalysis: async (days = 30): Promise<SymptomAnalysis> => {
        const response = await api.get('/symptoms/analysis', { params: { days } });
        return response.data;
    },

    getTypes: async (): Promise<SymptomTypes> => {
        const response = await api.get('/symptoms/types');
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await api.delete(`/symptoms/${id}`);
    },
};

// ============== Insights API ==============

export const insightsApi = {
    getRisks: async (): Promise<RiskAssessment> => {
        const response = await api.get('/insights/risks');
        return response.data;
    },

    getRecommendations: async (): Promise<Recommendation[]> => {
        const response = await api.get('/insights/recommendations');
        return response.data;
    },

    completeRecommendation: async (id: number): Promise<{ message: string }> => {
        const response = await api.post(`/insights/recommendations/${id}/complete`);
        return response.data;
    },

    getTimeline: async (days = 90): Promise<HealthTimeline> => {
        const response = await api.get('/insights/timeline', { params: { days } });
        return response.data;
    },

    getDashboard: async (): Promise<DashboardSummary> => {
        const response = await api.get('/insights/dashboard');
        return response.data;
    },
};

// ============== Chat API ==============

export const chatApi = {
    sendMessage: async (content: string): Promise<ChatMessage> => {
        const response = await api.post('/chat/', { content });
        return response.data;
    },

    getHistory: async (limit = 50): Promise<ChatMessage[]> => {
        const response = await api.get('/chat/history', { params: { limit } });
        return response.data;
    },

    clearHistory: async (): Promise<void> => {
        await api.delete('/chat/history');
    },
};

export default api;
