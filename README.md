# FemCare AI 🩺💜

A comprehensive women's health intelligence platform with AI-powered cycle tracking, health insights, mood journaling, and family sharing.

![FemCare AI](https://img.shields.io/badge/FemCare-AI-pink?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square)

## 🌟 Features

### 📅 **Cycle Tracking**
- Log and predict menstrual cycles with weighted moving average predictions
- Visual calendar with period days and predictions
- Phase-based insights (Menstrual, Follicular, Ovulation, Luteal)

### 💊 **Symptom Tracking**
- Track 50+ symptoms across 6 categories
- Severity rating (1-10 scale)
- AI-powered pattern detection and PMS prediction
- Personalized symptom guidance with remedies

### 😊 **Mood Journal**
- 12 mood options with emoji support
- Energy level tracking
- Mood-based activity & video suggestions
- Streak tracking and gratitude journaling

### 🏋️ **Activity Tracker**
- Phase-based exercise recommendations
- YouTube video integration
- Workout logging with calories burned
- Exercise streak tracking

### 🍎 **Nutrition Logger**
- Food database with macros
- AI photo analysis (Imagga API)
- Daily calorie & macro summaries
- Custom food creation

### 💧 **Water Tracker**
- Quick add buttons (250ml, 500ml, etc.)
- Phase-adjusted hydration goals
- Daily progress visualization
- 7-day history chart

### 👨‍👩‍👧 **Family Sharing**
- Invite family members to view health data
- Granular permission controls (mood, symptoms, cycle, nutrition, exercise)
- **Enhanced period insights** for family:
  - Real-time period status with days remaining
  - Flow level and phase information
  - Days until next period countdown
  - Phase-specific care suggestions

### 📊 **Health Insights**
- AI-powered risk assessment for:
  - PCOS (Polycystic Ovary Syndrome)
  - Endometriosis
  - Anemia
  - Thyroid conditions
- Real-time health score calculation
- Personalized recommendations based on your data

### 🤖 **AI Assistant**
- Natural language health queries
- Context-aware responses using your data
- Quick action categories (Period, Symptoms, Mood, Tips)
- Intent classification and entity extraction

### 📚 **Learn**
- 8 comprehensive health articles:
  - Menstrual Cycle Phases
  - PCOS Information
  - Endometriosis Signs & Symptoms
  - Nutrition for Hormonal Balance
  - Mental Health & Your Cycle
  - Fertility Awareness Methods
  - Myth Busting: Chocolate & Cramps
  - Myth Busting: Pregnancy on Period

### ⚙️ **Settings**
- Profile customization
- Notification preferences
- Data export
- Account management

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=your-secret-key-here" > .env

# Run the server
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

---

## 📁 Project Structure

```
Femcare-Ai/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── database.py       # SQLite/SQLAlchemy setup
│   │   ├── models.py         # Database models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── config.py         # App configuration
│   │   ├── security.py       # JWT Auth utilities
│   │   └── routers/          # API endpoints
│   │       ├── auth.py       # Authentication
│   │       ├── cycles.py     # Cycle tracking
│   │       ├── symptoms.py   # Symptom logging
│   │       ├── mood.py       # Mood journal
│   │       ├── activity.py   # Exercise tracking
│   │       ├── nutrition.py  # Calorie logging
│   │       ├── hydration.py  # Water tracking
│   │       ├── family.py     # Family sharing
│   │       ├── insights.py   # Health insights
│   │       └── chat.py       # AI assistant
│   ├── agent/                # AI agent core
│   │   ├── core.py
│   │   └── tools/
│   │       └── cycle_analyzer.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── components/       # Reusable components
    │   │   └── Layout/       # Main layout with sidebar
    │   ├── pages/            # Page components
    │   │   ├── Dashboard.tsx
    │   │   ├── CycleTracker.tsx
    │   │   ├── Symptoms.tsx
    │   │   ├── MoodJournal.tsx
    │   │   ├── Activity.tsx
    │   │   ├── CalorieLogger.tsx
    │   │   ├── WaterTracker.tsx
    │   │   ├── FamilySharing.tsx
    │   │   ├── FamilyView.tsx
    │   │   ├── Insights.tsx
    │   │   ├── Chat.tsx
    │   │   ├── Education.tsx
    │   │   └── Settings.tsx
    │   ├── context/          # React context (Auth)
    │   ├── services/         # API services
    │   └── types/            # TypeScript types
    ├── package.json
    └── vite.config.ts
```

---

## 🔌 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get JWT token |
| `/api/auth/me` | GET | Get current user |

### Cycle Tracking
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cycles/` | GET/POST | Cycle CRUD |
| `/api/cycles/current` | GET | Current cycle info |
| `/api/cycles/history` | GET | Cycle history |

### Symptoms
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/symptoms/` | GET/POST | Symptom CRUD |
| `/api/symptoms/today` | GET | Today's symptoms |
| `/api/symptoms/analysis` | GET | Symptom analysis |
| `/api/symptoms/pms-prediction` | GET | PMS prediction |

### Mood Journal
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mood/log` | POST | Log mood entry |
| `/api/mood/today` | GET | Today's moods |
| `/api/mood/insights` | GET | Mood analytics |
| `/api/mood/suggestions/{mood}` | GET | Mood-based suggestions |

### Health Insights
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/insights/risks` | GET | Risk assessments |
| `/api/insights/recommendations` | GET | Personalized recommendations |
| `/api/insights/dashboard` | GET | Dashboard summary with health score |

### Family Sharing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/family/members` | GET | List family members |
| `/api/family/invite` | POST | Invite family member |
| `/api/family/shared/{code}` | GET | Get shared data |

### AI Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/` | POST | Send message to AI |
| `/api/chat/history` | GET | Get chat history |

---

## 🔒 Privacy & Security

- **Local-First**: All data stored in local SQLite database
- **No Cloud Sync**: Your health data never leaves your device
- **Secure Auth**: JWT-based authentication with bcrypt password hashing
- **Family Permissions**: Granular control over what family members can see

---

## 🛠️ Technologies

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Local database
- **Pydantic** - Data validation
- **NumPy** - Numerical computing for health calculations
- **JWT** - Secure authentication

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **TanStack Query** - Data fetching & caching
- **Lucide Icons** - Beautiful icons
- **CSS Variables** - Theming support

---

## 🎨 UI Features

- **Dark/Light Mode** toggle
- **Responsive Design** - Works on mobile and desktop
- **Glass Morphism** - Modern aesthetic
- **Smooth Animations** - Polished user experience
- **Accessibility** - Semantic HTML and ARIA labels

---

## 📝 Environment Variables

### Backend (.env)
```env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///./femcare.db
IMAGGA_API_KEY=optional-for-food-photo-analysis
IMAGGA_API_SECRET=optional-for-food-photo-analysis
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

---

## 💜 Acknowledgments

Built with love for women's health. This app aims to empower women with better health insights and make period tracking more comprehensive and supportive.

---

**Made with 💜 by FemCare AI Team**
