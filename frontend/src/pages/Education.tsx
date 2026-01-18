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

                            {selectedArticle.id === 3 && (
                                <div className="article-full">
                                    <h3>What is Endometriosis?</h3>
                                    <p>Endometriosis is a condition where tissue similar to the uterine lining grows outside the uterus. It affects approximately 1 in 10 women and can cause significant pain and fertility issues.</p>

                                    <h3>Common Signs and Symptoms</h3>
                                    <ul>
                                        <li><strong>Severe menstrual cramps</strong> - Pain that doesn't respond to regular painkillers</li>
                                        <li><strong>Chronic pelvic pain</strong> - Pain between periods, not just during menstruation</li>
                                        <li><strong>Pain during intercourse</strong> - Deep pain during or after sex</li>
                                        <li><strong>Heavy periods</strong> - Excessive bleeding or bleeding between periods</li>
                                        <li><strong>Painful bowel movements</strong> - Especially during menstruation</li>
                                        <li><strong>Fatigue</strong> - Chronic tiredness, especially around your period</li>
                                        <li><strong>Infertility</strong> - Difficulty getting pregnant</li>
                                    </ul>

                                    <h3>When to Seek Medical Help</h3>
                                    <p>See a doctor if you experience:</p>
                                    <ul>
                                        <li>Period pain that disrupts daily activities</li>
                                        <li>Pain that progressively worsens over time</li>
                                        <li>Difficulty conceiving after 12 months of trying</li>
                                        <li>Any of the symptoms above that concern you</li>
                                    </ul>

                                    <h3>Important Note</h3>
                                    <p>On average, it takes 7-10 years to diagnose endometriosis. Tracking your symptoms in FemCare AI can help you identify patterns and provide valuable information to your healthcare provider.</p>
                                </div>
                            )}

                            {selectedArticle.id === 4 && (
                                <div className="article-full">
                                    <h3>Foods That Support Hormonal Balance</h3>
                                    <p>What you eat significantly impacts your hormonal health. Here's what to include:</p>

                                    <h4>🥬 Include More:</h4>
                                    <ul>
                                        <li><strong>Leafy greens</strong> - Spinach, kale, broccoli (rich in magnesium)</li>
                                        <li><strong>Fatty fish</strong> - Salmon, sardines (omega-3 fatty acids)</li>
                                        <li><strong>Whole grains</strong> - Oats, quinoa, brown rice (fiber and B vitamins)</li>
                                        <li><strong>Legumes</strong> - Lentils, chickpeas (plant protein and iron)</li>
                                        <li><strong>Berries</strong> - Blueberries, strawberries (antioxidants)</li>
                                        <li><strong>Nuts and seeds</strong> - Flaxseeds, walnuts (healthy fats)</li>
                                    </ul>

                                    <h4>⚠️ Limit These:</h4>
                                    <ul>
                                        <li><strong>Processed foods</strong> - High in inflammatory ingredients</li>
                                        <li><strong>Excessive sugar</strong> - Can disrupt insulin and hormones</li>
                                        <li><strong>Alcohol</strong> - Affects estrogen metabolism</li>
                                        <li><strong>Excess caffeine</strong> - Can worsen PMS symptoms</li>
                                    </ul>

                                    <h4>Phase-Based Eating Tips:</h4>
                                    <ul>
                                        <li><strong>Menstrual:</strong> Iron-rich foods (leafy greens, red meat)</li>
                                        <li><strong>Follicular:</strong> Fresh vegetables and lean proteins</li>
                                        <li><strong>Ovulation:</strong> Fiber-rich foods and antioxidants</li>
                                        <li><strong>Luteal:</strong> Complex carbs and magnesium-rich foods</li>
                                    </ul>
                                </div>
                            )}

                            {selectedArticle.id === 5 && (
                                <div className="article-full">
                                    <h3>The Hormone-Mood Connection</h3>
                                    <p>Your menstrual cycle significantly affects your mental health due to fluctuating hormone levels.</p>

                                    <h4>How Hormones Affect Mood:</h4>
                                    <ul>
                                        <li><strong>Estrogen</strong> - Boosts serotonin ("feel-good" hormone). Higher levels = better mood</li>
                                        <li><strong>Progesterone</strong> - Has calming effects but can cause fatigue and low mood when dropping</li>
                                        <li><strong>Testosterone</strong> - Peaks at ovulation, boosting energy and libido</li>
                                    </ul>

                                    <h4>Mood by Cycle Phase:</h4>
                                    <ul>
                                        <li><strong>Menstrual (Days 1-5):</strong> Low hormones may cause fatigue and introspection. Practice self-care.</li>
                                        <li><strong>Follicular (Days 6-14):</strong> Rising estrogen improves mood and creativity. Great time for new projects!</li>
                                        <li><strong>Ovulation (Day 14):</strong> Peak energy, confidence, and social mood.</li>
                                        <li><strong>Luteal (Days 15-28):</strong> PMS symptoms may include anxiety, irritability, and mood swings.</li>
                                    </ul>

                                    <h4>Tips for Managing Cycle-Related Mood Changes:</h4>
                                    <ul>
                                        <li>Track your mood to identify patterns</li>
                                        <li>Exercise regularly (even gentle movement helps)</li>
                                        <li>Prioritize sleep, especially in the luteal phase</li>
                                        <li>Practice stress-reduction techniques</li>
                                        <li>Talk to a doctor if symptoms are severe (PMDD)</li>
                                    </ul>
                                </div>
                            )}

                            {selectedArticle.id === 6 && (
                                <div className="article-full">
                                    <h3>Understanding Your Fertile Window</h3>
                                    <p>Fertility awareness methods help you understand when you're most likely to conceive.</p>

                                    <h4>The Fertile Window:</h4>
                                    <p>You can only conceive during a small window each cycle:</p>
                                    <ul>
                                        <li>An egg lives for 12-24 hours after ovulation</li>
                                        <li>Sperm can survive 3-5 days in the reproductive tract</li>
                                        <li>Your fertile window is approximately 6 days: 5 days before ovulation + ovulation day</li>
                                    </ul>

                                    <h4>Signs of Ovulation:</h4>
                                    <ul>
                                        <li><strong>Cervical mucus changes</strong> - Becomes clear, stretchy, egg-white consistency</li>
                                        <li><strong>Basal body temperature rise</strong> - Slight increase after ovulation</li>
                                        <li><strong>Mild pelvic pain</strong> - Called "mittelschmerz" (middle pain)</li>
                                        <li><strong>Increased libido</strong> - Natural biological drive</li>
                                        <li><strong>Breast tenderness</strong> - Due to hormonal shifts</li>
                                    </ul>

                                    <h4>Tracking Methods:</h4>
                                    <ul>
                                        <li><strong>Calendar/App:</strong> FemCare AI predicts based on your cycle history</li>
                                        <li><strong>Basal Body Temperature:</strong> Take your temp every morning before getting up</li>
                                        <li><strong>Cervical Mucus:</strong> Check daily and log consistency</li>
                                        <li><strong>Ovulation Predictor Kits:</strong> Detect LH surge 24-36 hours before ovulation</li>
                                    </ul>

                                    <h4>Important:</h4>
                                    <p>Fertility awareness requires consistent tracking and is most effective when combining multiple methods. Consult a healthcare provider for personalized guidance.</p>
                                </div>
                            )}

                            {selectedArticle.id === 7 && (
                                <div className="article-full">
                                    <h3>🍫 The Myth: Chocolate Makes Cramps Worse</h3>
                                    <p className="myth-verdict">❌ BUSTED!</p>

                                    <h4>What Research Actually Says:</h4>
                                    <p>Dark chocolate may actually HELP with cramps! Here's why:</p>
                                    <ul>
                                        <li><strong>Magnesium content:</strong> Dark chocolate is rich in magnesium, which helps relax muscles and may reduce cramping</li>
                                        <li><strong>Mood boost:</strong> Chocolate triggers endorphin release, which can help with pain perception</li>
                                        <li><strong>Antioxidants:</strong> Dark chocolate contains flavonoids that may reduce inflammation</li>
                                    </ul>

                                    <h4>The Caveat:</h4>
                                    <ul>
                                        <li>Choose dark chocolate (70%+ cacao) for benefits</li>
                                        <li>Milk chocolate has less magnesium and more sugar</li>
                                        <li>Moderation is key - a few squares, not a whole bar!</li>
                                    </ul>

                                    <h4>Bottom Line:</h4>
                                    <p>Go ahead and have some dark chocolate during your period! It's not only okay - it might actually help. Just choose quality over quantity. 🍫✨</p>
                                </div>
                            )}

                            {selectedArticle.id === 8 && (
                                <div className="article-full">
                                    <h3>🤰 The Myth: You Can't Get Pregnant on Your Period</h3>
                                    <p className="myth-verdict">❌ BUSTED!</p>

                                    <h4>The Truth:</h4>
                                    <p>While unlikely, it IS possible to get pregnant during your period. Here's why:</p>

                                    <h4>How It Can Happen:</h4>
                                    <ul>
                                        <li><strong>Short cycles:</strong> If your cycle is 21-24 days, you may ovulate just a few days after your period ends</li>
                                        <li><strong>Sperm survival:</strong> Sperm can live up to 5 days in the reproductive tract</li>
                                        <li><strong>Early ovulation:</strong> Some women ovulate earlier than "typical" day 14</li>
                                        <li><strong>Breakthrough bleeding:</strong> What seems like a period might be ovulation spotting</li>
                                    </ul>

                                    <h4>Example Scenario:</h4>
                                    <p>If you have a 24-day cycle and a 6-day period, and you have sex on day 6, the sperm could still be alive when you ovulate on day 10!</p>

                                    <h4>Bottom Line:</h4>
                                    <p>If you're trying to avoid pregnancy, never assume any day is "safe." Use protection throughout your cycle. If you're trying to conceive, your period days are unlikely but not impossible. Track your cycle to understand your unique patterns!</p>
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
