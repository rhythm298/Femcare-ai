/**
 * Main Layout Component with Sidebar Navigation
 */

import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    LayoutDashboard,
    Calendar,
    Activity,
    LineChart,
    MessageCircle,
    BookOpen,
    Settings,
    LogOut,
    Menu,
    X,
    Heart,
    Moon,
    Sun,
    Dumbbell,
    Apple,
    Users,
    Droplets,
    Target,
    Smile,
} from 'lucide-react';
import './Layout.css';

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/cycles', icon: Calendar, label: 'Cycle Tracker' },
    // { path: '/fertility', icon: Target, label: 'Fertility' }, // Disabled for now
    { path: '/symptoms', icon: Activity, label: 'Symptoms' },
    { path: '/mood', icon: Smile, label: 'Mood Journal' },
    { path: '/activity', icon: Dumbbell, label: 'Activity' },
    { path: '/nutrition', icon: Apple, label: 'Nutrition' },
    { path: '/hydration', icon: Droplets, label: 'Water Tracker' },
    { path: '/family', icon: Users, label: 'Family Sharing' },
    { path: '/insights', icon: LineChart, label: 'Health Insights' },
    { path: '/chat', icon: MessageCircle, label: 'AI Assistant' },
    { path: '/education', icon: BookOpen, label: 'Learn' },
    { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
    const { user, logout } = useAuth();
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [darkMode, setDarkMode] = useState(false);

    const toggleDarkMode = () => {
        setDarkMode(!darkMode);
        document.documentElement.setAttribute('data-theme', darkMode ? 'light' : 'dark');
    };

    const closeSidebar = () => setSidebarOpen(false);

    return (
        <div className="layout">
            {/* Mobile Header */}
            <header className="mobile-header">
                <button className="btn btn-icon" onClick={() => setSidebarOpen(true)}>
                    <Menu size={24} />
                </button>
                <div className="mobile-logo">
                    <Heart className="logo-icon" />
                    <span className="gradient-text">FemCare AI</span>
                </div>
                <button className="btn btn-icon" onClick={toggleDarkMode}>
                    {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                </button>
            </header>

            {/* Sidebar Overlay */}
            {sidebarOpen && <div className="sidebar-overlay" onClick={closeSidebar} />}

            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <div className="logo">
                        <Heart className="logo-icon" />
                        <span className="gradient-text">FemCare AI</span>
                    </div>
                    <button className="btn btn-icon mobile-close" onClick={closeSidebar}>
                        <X size={24} />
                    </button>
                </div>

                <nav className="sidebar-nav">
                    {navItems.map(({ path, icon: Icon, label }) => (
                        <NavLink
                            key={path}
                            to={path}
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                            onClick={closeSidebar}
                            end={path === '/'}
                        >
                            <Icon size={20} />
                            <span>{label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <div className="user-info">
                        <div className="user-avatar">
                            {user?.name?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="user-details">
                            <span className="user-name">{user?.name || 'User'}</span>
                            <span className="user-email">{user?.email}</span>
                        </div>
                    </div>
                    <div className="sidebar-actions">
                        <button className="btn btn-icon" onClick={toggleDarkMode} title="Toggle theme">
                            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
                        </button>
                        <button className="btn btn-icon logout-btn" onClick={logout} title="Logout">
                            <LogOut size={18} />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}
