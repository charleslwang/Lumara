# Lumara AI Deployment Guide

## Current Setup
- **Frontend**: Hosted on GoDaddy (lumaraai.xyz) via GitHub integration
- **Backend**: Needs to be deployed separately (Render.com recommended)

## Files Updated for Deployment ✅
- ✅ `config.js` - Backend URL configuration
- ✅ `script.js` - Updated to use external backend
- ✅ `index.html` - Added config.js script
- ✅ `api.py` - Added health endpoint & stateless design
- ✅ `core/pipeline.py` - User-provided API keys only
- ✅ `wsgi.py` - Production WSGI entry point
- ✅ `gunicorn.conf.py` - Production server config
- ✅ `requirements.txt` - All dependencies included

## Deployment Steps

### 1. Deploy Backend to Render.com (FREE)

1. **Go to [render.com](https://render.com)**
2. **Sign up with GitHub**
3. **Click "New +" → "Web Service"**
4. **Connect your Lumara GitHub repository**
5. **Configure:**
   - **Name:** `lumara-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --config gunicorn.conf.py wsgi:app`
   - **Auto-Deploy:** Yes

6. **Deploy!** You'll get a URL like: `https://lumara-backend-abc123.onrender.com`

### 2. Update Frontend Configuration

1. **Edit `config.js`:**
   ```javascript
   const LUMARA_CONFIG = {
       BACKEND_URL: 'https://your-actual-render-url.onrender.com',
       // ... rest stays the same
   };
   ```

2. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Update backend URL for production"
   git push
   ```

3. **GoDaddy will auto-update your site!**

### 3. Test Your Deployment

1. **Frontend:** https://lumaraai.xyz
2. **Backend Health:** https://your-render-url.onrender.com/api/health
3. **Try the refinement engine with a test API key**

## Important Notes

- ✅ **No API keys stored on server** - Users provide their own
- ✅ **Completely free hosting** with Render.com
- ✅ **Auto-deploys** from GitHub
- ⚠️ **Backend sleeps after 15 min** (wakes up in ~30 seconds)
- ✅ **CORS enabled** for cross-origin requests

## Troubleshooting

### Backend Issues:
- Check logs in Render dashboard
- Verify health endpoint: `/api/health`
- Check build logs for dependency errors

### Frontend Issues:
- Check browser console for errors
- Verify config.js has correct backend URL
- Test backend URL directly in browser

### API Issues:
- Users need valid Google Gemini API key
- Check API key format and permissions
- Verify quota limits not exceeded

## File Structure
```
Lumara/
├── config.js          # Backend URL configuration
├── index.html         # Main frontend page
├── script.js          # Frontend JavaScript
├── api.py            # Flask backend
├── wsgi.py           # Production entry point
├── gunicorn.conf.py  # Server configuration
├── requirements.txt  # Python dependencies
├── core/
│   └── pipeline.py   # Refinement logic
└── Refinery/         # Core refinement engine
```

## Success! 🎉
Your Lumara AI is now deployed and ready for users!
