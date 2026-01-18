/**
 * Authentication Context for FemCare AI
 * Provides auth state and methods throughout the app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { authApi } from '../services/api';
import type { User, LoginCredentials, RegisterData } from '../types';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (credentials: LoginCredentials) => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    logout: () => void;
    updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const queryClient = useQueryClient();

    // Check for existing token on mount
    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('femcare_token');
            if (token) {
                try {
                    const userData = await authApi.getProfile();
                    setUser(userData);
                } catch {
                    localStorage.removeItem('femcare_token');
                }
            }
            setIsLoading(false);
        };
        checkAuth();
    }, []);

    const login = async (credentials: LoginCredentials) => {
        // Clear any cached data from previous user
        queryClient.clear();

        const { access_token } = await authApi.login(credentials);
        localStorage.setItem('femcare_token', access_token);
        const userData = await authApi.getProfile();
        setUser(userData);
    };

    const register = async (data: RegisterData) => {
        await authApi.register(data);
        // Auto-login after registration
        await login({ email: data.email, password: data.password });
    };

    const logout = () => {
        // Clear all cached data to prevent data leakage between users
        queryClient.clear();
        localStorage.removeItem('femcare_token');
        setUser(null);
    };

    const updateUser = (updatedUser: User) => {
        setUser(updatedUser);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                register,
                logout,
                updateUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
