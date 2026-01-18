/**
 * FemCare AI - Main App Component
 * Routing and layout configuration
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import CycleTracker from './pages/CycleTracker';
import Symptoms from './pages/Symptoms';
import Insights from './pages/Insights';
import Chat from './pages/Chat';
import Education from './pages/Education';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
import Activity from './pages/Activity';
import CalorieLogger from './pages/CalorieLogger';
import FamilySharing from './pages/FamilySharing';
import FamilyView from './pages/FamilyView';
import WaterTracker from './pages/WaterTracker';
import Fertility from './pages/Fertility';
import MoodJournal from './pages/MoodJournal';

// Loading spinner component
function LoadingScreen() {
    return (
        <div className="loading-screen">
            <div className="loading-content">
                <div className="loading-logo animate-pulse">🩺</div>
                <h2 className="gradient-text">FemCare AI</h2>
                <p>Loading your health dashboard...</p>
            </div>
            <style>{`
        .loading-screen {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          background: var(--bg-primary);
        }
        .loading-content {
          text-align: center;
        }
        .loading-logo {
          font-size: 4rem;
          margin-bottom: 1rem;
        }
        .loading-content h2 {
          font-size: 1.5rem;
          margin-bottom: 0.5rem;
        }
        .loading-content p {
          color: var(--text-muted);
        }
      `}</style>
        </div>
    );
}

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return <LoadingScreen />;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}

// Public route wrapper (redirects if already authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return <LoadingScreen />;
    }

    if (isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    return <>{children}</>;
}

function App() {
    return (
        <Routes>
            {/* Public Routes */}
            <Route
                path="/login"
                element={
                    <PublicRoute>
                        <Login />
                    </PublicRoute>
                }
            />
            <Route
                path="/register"
                element={
                    <PublicRoute>
                        <Register />
                    </PublicRoute>
                }
            />

            {/* Protected Routes */}
            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <Layout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<Dashboard />} />
                <Route path="cycles" element={<CycleTracker />} />
                <Route path="symptoms" element={<Symptoms />} />
                <Route path="insights" element={<Insights />} />
                <Route path="chat" element={<Chat />} />
                <Route path="education" element={<Education />} />
                <Route path="settings" element={<Settings />} />
                <Route path="activity" element={<Activity />} />
                <Route path="nutrition" element={<CalorieLogger />} />
                <Route path="hydration" element={<WaterTracker />} />
                <Route path="family" element={<FamilySharing />} />
                <Route path="fertility" element={<Fertility />} />
                <Route path="mood" element={<MoodJournal />} />
            </Route>

            {/* Public Family View Route */}
            <Route path="/family-view/:inviteCode" element={<FamilyView />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}

export default App;
