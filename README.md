# FemCare AI

A comprehensive women's health intelligence platform with AI-powered risk assessment, cycle tracking, and personalized recommendations.

## 🌟 Features

- **Cycle Tracking** - Log and predict menstrual cycles with weighted moving average predictions
- **Symptom Analysis** - Track symptoms with severity, get AI-powered correlations and insights
- **Risk Assessment** - AI-powered screening for PCOS, Endometriosis, Anemia, and Thyroid conditions
- **Health Chat** - AI health assistant for personalized guidance
- **Privacy-First** - All data stored locally using SQLite

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

## 📁 Project Structure

```
Femcare-Ai/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI entry point
│   │   ├── database.py     # SQLite/SQLAlchemy setup
│   │   ├── models.py       # Database models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── config.py       # App configuration
│   │   ├── security.py     # Auth utilities
│   │   └── routers/        # API endpoints
│   │       ├── auth.py
│   │       ├── cycles.py
│   │       ├── symptoms.py
│   │       ├── insights.py
│   │       └── chat.py
│   ├── agent/              # AI agent core
│   │   ├── core.py
│   │   └── tools/
│   │       └── cycle_analyzer.py
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/     # React components
    │   ├── pages/          # Page components
    │   ├── context/        # React context
    │   ├── services/       # API services
    │   └── types/          # TypeScript types
    ├── package.json
    └── vite.config.ts
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get token |
| `/api/cycles/` | GET/POST | Cycle CRUD |
| `/api/cycles/current` | GET | Current cycle info |
| `/api/cycles/prediction` | GET | Cycle predictions |
| `/api/symptoms/` | GET/POST | Symptom CRUD |
| `/api/symptoms/analysis` | GET | Symptom analysis |
| `/api/insights/risks` | GET | Risk assessments |
| `/api/insights/recommendations` | GET | Recommendations |
| `/api/insights/dashboard` | GET | Dashboard summary |
| `/api/chat/` | POST | AI chat |

## 🔒 Privacy

- **Local-First**: All data is stored in a local SQLite database
- **No Cloud**: Your health data never leaves your device
- **Secure Auth**: JWT-based authentication with bcrypt password hashing

## 🛠️ Technologies

### Backend
- FastAPI
- SQLAlchemy + SQLite
- Pydantic
- NumPy/Pandas

### Frontend
- React 18
- TypeScript
- TanStack Query
- Recharts
- Lucide Icons

## 📄 License

MIT License
