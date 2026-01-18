# FemCare AI - Deployment Guide

## Overview
This guide covers deploying FemCare AI for development (localhost), staging, and production (Netlify + Render).

---

## Local Development Setup

### Backend (FastAPI)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example if available)
# Required variables:
# DATABASE_URL=sqlite:///./femcare.db (for local SQLite)
# SECRET_KEY=your-secret-key-here

# Run development server
python -m uvicorn app.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend (Vite + React)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Make sure .env has correct API URL
# VITE_API_URL=http://localhost:8000/api

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## Production Deployment

### Backend on Render

1. **Create a Render account** at [render.com](https://render.com)

2. **Connect your GitHub repository**

3. **Create a new Web Service** with these settings:
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

4. **Add Environment Variables** in Render Dashboard:
   ```
   DATABASE_URL=<your-postgresql-url>
   SECRET_KEY=<your-production-secret-key>
   USE_LOCAL_LLM=false
   DEBUG=false
   ```

   > **Note**: Render provides free PostgreSQL databases. Create one and link it.

5. **Deploy** - Render will automatically deploy on git push

### Frontend on Netlify

1. **Create a Netlify account** at [netlify.com](https://netlify.com)

2. **Connect your GitHub repository**

3. **Configure build settings**:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

4. **Add Environment Variables** in Netlify Dashboard:
   ```
   VITE_API_URL=https://your-render-backend.onrender.com/api
   VITE_APP_NAME=FemCare AI
   VITE_ENV=production
   ```

5. **Deploy** - Netlify will automatically deploy on git push

---

## netlify.toml Configuration

The frontend already includes `netlify.toml`:

```toml
[build]
  base = "frontend"
  publish = "dist"
  command = "npm run build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## After Deployment Checklist

### Backend (Render)
- [ ] Verify health check: `https://your-app.onrender.com/`
- [ ] Check API docs: `https://your-app.onrender.com/docs`
- [ ] Verify CORS allows your Netlify domain
- [ ] Test user registration and login

### Frontend (Netlify)
- [ ] Verify site loads correctly
- [ ] Test login/registration flow
- [ ] Verify API calls work (check browser console)
- [ ] Test all new features (Activity, Nutrition, Water, Family)

---

## Environment Variables Reference

### Backend (.env)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host/db` |
| `SECRET_KEY` | JWT signing key | `your-super-secret-key` |
| `DEBUG` | Enable debug mode | `false` |
| `USE_LOCAL_LLM` | Use Ollama for AI | `false` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llava` |

### Frontend (.env)
| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.example.com/api` |
| `VITE_APP_NAME` | Application name | `FemCare AI` |
| `VITE_ENV` | Environment name | `production` |

---

## Updating CORS for Production

In `backend/app/main.py`, update the CORS origins to include your Netlify domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://your-netlify-site.netlify.app",
        "https://your-custom-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Troubleshooting

### API calls failing
1. Check browser console for CORS errors
2. Verify `VITE_API_URL` is correctly set
3. Ensure backend is running and accessible

### 404 on page refresh (Netlify)
- Ensure `netlify.toml` has the redirect rule for SPA routing

### Database connection issues
- Verify `DATABASE_URL` is correctly formatted
- Check if database server is accessible from Render

### Slow initial load on Render
- Free tier instances sleep after inactivity
- First request may take 30-60 seconds to wake up
