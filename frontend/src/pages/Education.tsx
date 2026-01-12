/**
 * Education Page - Health articles and learning resources
 */

import { useState } from 'react';
import { BookOpen, Search, GraduationCap, Sparkles, Heart, Baby, Brain, Apple } from 'lucide-react';
import './Education.css';

interface Article {
    id: number;
    title: string;
    summary: string;
    category: string;
    icon: typeof Heart;
    readTime: number;
    isMythBusting?: boolean;
}

const articles: Article[] = [
    {
        id: 1,
        title: 'Understanding Your Menstrual Cycle',
        summary: 'Learn about the four phases of your cycle and what to expect during each one.',
        category: 'Menstrual Health',
        icon: Heart,
        readTime: 5,
    },
    {
        id: 2,
        title: 'What is PCOS?',
        summary: 'Polycystic Ovary Syndrome explained: symptoms, causes, and management strategies.',
        category: 'Conditions',
        icon: Sparkles,
        readTime: 8,
    },
    {
        id: 3,
        title: 'Endometriosis: Signs and Symptoms',
        summary: 'How to recognize endometriosis and when to seek medical help.',
        category: 'Conditions',
        icon: Sparkles,
        readTime: 7,
    },
    {
        id: 4,
        title: 'Nutrition for Hormonal Balance',
        summary: 'Foods that support hormonal health and those to limit.',
        category: 'Nutrition',
        icon: Apple,
        readTime: 6,
    },
    {
        id: 5,
        title: 'Mental Health and Your Cycle',
        summary: 'Understanding the connection between hormones and mood.',
        category: 'Mental Health',
        icon: Brain,
        readTime: 5,
    },
    {
        id: 6,
        title: 'Fertility Awareness Methods',
        summary: 'Understanding your fertile window and tracking ovulation.',
        category: 'Fertility',
        icon: Baby,
        readTime: 10,
    },
    {
        id: 7,
        title: 'Myth: Chocolate Makes Cramps Worse',
        summary: 'What research actually says about chocolate and menstrual pain.',
        category: 'Myth Busting',
        icon: GraduationCap,
        readTime: 3,
        isMythBusting: true,
    },
    {
        id: 8,
        title: 'Myth: You Can\'t Get Pregnant on Your Period',
        summary: 'The truth about fertility during menstruation.',
        category: 'Myth Busting',
        icon: GraduationCap,
        readTime: 4,
        isMythBusting: true,
    },
];

const categories = ['All', 'Menstrual Health', 'Conditions', 'Nutrition', 'Mental Health', 'Fertility', 'Myth Busting'];

export default function Education() {
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

    const filteredArticles = articles.filter((article) => {
        const matchesCategory = selectedCategory === 'All' || article.category === selectedCategory;
        const matchesSearch =
            article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            article.summary.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    return (
        <div className="education-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1><BookOpen size={28} /> Learn</h1>
                    <p>Evidence-based health education</p>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="education-filters">
                <div className="search-bar">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder="Search articles..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="category-filters">
                    {categories.map((category) => (
                        <button
                            key={category}
                            className={`filter-btn ${selectedCategory === category ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(category)}
                        >
                            {category}
                        </button>
                    ))}
                </div>
            </div>

            {/* Articles Grid */}
            <div className="articles-grid">
                {filteredArticles.map((article) => {
                    const Icon = article.icon;
                    return (
                        <div
                            key={article.id}
                            className={`article-card card ${article.isMythBusting ? 'myth-busting' : ''}`}
                            onClick={() => setSelectedArticle(article)}
                        >
                            <div className="article-icon">
                                <Icon size={24} />
                            </div>
                            <div className="article-content">
                                <span className="article-category">{article.category}</span>
                                <h3>{article.title}</h3>
                                <p>{article.summary}</p>
                                <span className="read-time">{article.readTime} min read</span>
                            </div>
                            {article.isMythBusting && (
                                <span className="myth-badge">Myth Busting</span>
                            )}
                        </div>
                    );
                })}
            </div>

            {filteredArticles.length === 0 && (
                <div className="no-results">
                    <p>No articles found matching your search.</p>
                </div>
            )}

            {/* Article Modal */}
            {selectedArticle && (
                <div className="modal-overlay" onClick={() => setSelectedArticle(null)}>
                    <div className="modal article-modal glass animate-slide-up" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <span className="article-category">{selectedArticle.category}</span>
                                <h2>{selectedArticle.title}</h2>
                            </div>
                            <button className="btn btn-ghost" onClick={() => setSelectedArticle(null)}>
                                ✕
                            </button>
                        </div>
                        <div className="modal-body article-body">
                            <p className="article-intro">{selectedArticle.summary}</p>

                            {selectedArticle.id === 1 && (
                                <div className="article-full">
                                    <h3>The Four Phases of Your Cycle</h3>
                                    <ol>
                                        <li>
                                            <strong>Menstrual Phase (Days 1-5)</strong>
                                            <p>This is when you have your period. The uterine lining sheds, and hormone levels are low.</p>
                                        </li>
                                        <li>
                                            <strong>Follicular Phase (Days 1-13)</strong>
                                            <p>Overlapping with menstruation, this phase sees rising estrogen levels as follicles develop in the ovaries.</p>
                                        </li>
                                        <li>
                                            <strong>Ovulation Phase (Day 14)</strong>
                                            <p>A mature egg is released. This is your most fertile time.</p>
                                        </li>
                                        <li>
                                            <strong>Luteal Phase (Days 15-28)</strong>
                                            <p>Progesterone rises to prepare for potential pregnancy. PMS symptoms may occur.</p>
                                        </li>
                                    </ol>
                                </div>
                            )}

                            {selectedArticle.id === 2 && (
                                <div className="article-full">
                                    <h3>What is PCOS?</h3>
                                    <p>Polycystic Ovary Syndrome affects about 1 in 10 women of reproductive age. It's a hormonal disorder that can cause:</p>
                                    <ul>
                                        <li>Irregular or missed periods</li>
                                        <li>Excess androgen (acne, facial hair)</li>
                                        <li>Polycystic ovaries on ultrasound</li>
                                        <li>Weight gain or difficulty losing weight</li>
                                    </ul>
                                    <h3>Management</h3>
                                    <p>PCOS can be managed through lifestyle changes, medication, and working with your healthcare provider.</p>
                                </div>
                            )}

                            {selectedArticle.id !== 1 && selectedArticle.id !== 2 && (
                                <div className="article-full">
                                    <p className="coming-soon">Full article content coming soon! This is a preview.</p>
                                </div>
                            )}
                        </div>
                        <div className="modal-footer">
                            <span className="read-time-footer">📖 {selectedArticle.readTime} min read</span>
                            <button className="btn btn-primary" onClick={() => setSelectedArticle(null)}>
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
