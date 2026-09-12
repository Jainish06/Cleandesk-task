# 100% Free Cloud Deployment Guide

This guide walks you through deploying both the **FastAPI Backend** and the **Next.js Frontend** to the cloud for free with live WebSockets, MongoDB Atlas, and Upstash Redis.

---

## Architecture in Production

```
┌──────────────────────────────────────────┐
│      Next.js Frontend on Vercel          │  (100% Free)
│       https://your-app.vercel.app        │
└────────────────────┬─────────────────────┘
                     │ HTTPS & WSS (WebSockets)
                     ▼
┌──────────────────────────────────────────┐
│       FastAPI Backend on Render          │  (100% Free)
│     https://your-backend.onrender.com    │
└──────────────┬───────────────────┬───────┘
               │                   │
               ▼                   ▼
      ┌─────────────────┐ ┌─────────────────┐
      │  MongoDB Atlas  │ │  Upstash Redis  │
      │   (Free M0 DB)  │ │   (Free 10K/day)│
      └─────────────────┘ └─────────────────┘
```

---

## Step 1: Push Project to GitHub

Make sure your project is committed and pushed to a GitHub repository (e.g. `cleandesk-pipeline`):

```bash
# In the root directory (/Users/jainishpathak/Desktop/Cleandesk-task):
git init
git add .
git commit -m "CleanDesk Event-Driven Messaging Pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

*(Note: `.env` is ignored by `.gitignore` so your secret credentials won't be exposed).*

---

## Step 2: Deploy Backend to Render (Free Web Service)

**Render** gives you free web services with full native WebSocket (`wss://`) support.

1. Go to **[Render.com](https://render.com)** and sign up / log in with your GitHub account.
2. Click **New +** ➔ **Web Service**.
3. Select your GitHub repository.
4. Configure the service settings:
   - **Name**: `cleandesk-backend` (or any unique name)
   - **Region**: Nearest to your users (e.g., Oregon, Frankfurt, Singapore)
   - **Root Directory**: `backend` *(Important!)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Select **Free** ($0/month)
5. Under **Environment Variables**, add the following:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `MONGODB_URI` | `mongodb+srv://...` | Your MongoDB Atlas connection string |
   | `MONGODB_DB_NAME` | `cleandesk` | Your database name |
   | `REDIS_URL` | `https://fit-thrush-109841.upstash.io` | Your Upstash Redis URL |
   | `REDIS_TOKEN` | `gQAAAAAAAa...` | Your Upstash Redis Token |
   | `REDIS_QUEUE_NAME`| `cleandesk:interactions:queue` | Queue key |
   | `GEMINI_API_KEY`| *(optional)* | Your Google Gemini key (or leave empty for fallback) |
   | `HOST` | `0.0.0.0` | Server bind host |
   | `DEBUG` | `False` | Production mode |
6. Click **Create Web Service**.
7. Once deployment finishes (usually 1-2 minutes), Render gives you a public URL, for example:
   👉 **`https://cleandesk-backend.onrender.com`**
   *(Your WebSocket endpoint will automatically be available at `wss://cleandesk-backend.onrender.com/ws/inbox`)*.

---

## Step 3: Deploy Frontend to Vercel (100% Free)

**Vercel** is the official creator of Next.js and hosts Next.js apps with global CDN edge routing for free.

1. Go to **[Vercel.com](https://vercel.com)** and log in with GitHub.
2. Click **Add New...** ➔ **Project**.
3. Select your GitHub repository and click **Import**.
4. Configure the build settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click *Edit* and select **`frontend`** *(Important!)*
5. Under **Environment Variables**, add:
   | Key | Value |
   | :--- | :--- |
   | `NEXT_PUBLIC_API_URL` | `https://cleandesk-backend.onrender.com` *(Your Render URL from Step 2)* |
   | `NEXT_PUBLIC_WS_URL` | `wss://cleandesk-backend.onrender.com/ws/inbox` *(Notice `wss://` for secure WebSockets)* |
6. Click **Deploy**.
7. In ~60 seconds, Vercel gives you your production website URL, for example:
   👉 **`https://cleandesk-pipeline.vercel.app`**

---

## Step 4: Verify Your Live Production Deployment

1. Open your Vercel URL in your browser: `https://cleandesk-pipeline.vercel.app`.
2. Check the top header: the status pill will show **"🟢 Live WebSocket"**.
3. Go to the **Webhook Simulator** tab.
4. Click **"Simulate Webhook Event"** on any scenario.
5. Return to the **Universal Inbox**: your live production backend and Upstash Redis queue will process the event, ground it with RAG, and stream the result to your screen in real time!
