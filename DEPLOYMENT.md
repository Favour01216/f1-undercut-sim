# F1 Undercut Simulator - Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended)

1. Push code to GitHub
2. Go to https://railway.app
3. Connect your GitHub repo
4. Railway auto-detects Docker and deploys
5. Get public URL: `https://f1-undercut-sim.railway.app`

### Option 2: Vercel + Railway Split

**Frontend (Vercel):**

- Deploy to https://vercel.com
- Auto-detects Next.js
- Free custom domains

**Backend (Railway):**

- Deploy FastAPI to Railway
- Get API endpoint

### Option 3: DigitalOcean App Platform

1. Create DO account
2. Use App Platform
3. Connect GitHub repo
4. Deploy with docker-compose.prod.yml

## 🔧 Production Environment Variables

Create a `.env.prod` file:

```bash
# Backend
ENV=production
CORS_ORIGINS=https://your-frontend.vercel.app
SENTRY_DSN=your-sentry-dsn

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_ENABLE_SENTRY=true
```

## 🐳 Docker Production Commands

```bash
# Local production test
docker-compose -f docker-compose.prod.yml up --build

# Deploy to cloud
git push origin main  # Auto-deploys on most platforms
```

## 🌍 Custom Domain Setup

Most platforms support custom domains:

- `f1-undercut-simulator.com`
- `undercut-analyzer.racing`
- `pit-strategy.f1`

## 📊 Monitoring

All platforms provide:

- ✅ Automatic SSL certificates
- ✅ Health checks
- ✅ Scaling
- ✅ Logs and metrics
- ✅ Zero-downtime deployments

## 🏁 Ready to Deploy!

Your F1 Undercut Simulator is production-ready with:

- ✅ Docker containers
- ✅ F1 racing theme
- ✅ All 30 F1 circuits
- ✅ Environment configs
- ✅ Health checks
- ✅ Error monitoring ready
