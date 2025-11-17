# MindVision Camera API - Quick Start Guide

Complete guide to get the camera control system up and running in minutes.

## System Overview

```
┌─────────────────────────────────────────────────┐
│              Web Browser                        │
│    http://localhost:3000 (Frontend)             │
└────────────────┬────────────────────────────────┘
                 │
                 │ HTTP/WebSocket
                 ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend Server                  │
│    http://localhost:8000 (Camera API)           │
└────────────────┬────────────────────────────────┘
                 │
                 │ Python SDK
                 ▼
┌─────────────────────────────────────────────────┐
│       MindVision 47MP GigE Camera               │
│         (Hardware Device)                       │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **MindVision Camera SDK** installed
- **MindVision 47MP Camera** connected via GigE
- **MQTT Broker** (optional, for events)

## Installation

### Step 1: Install Backend Dependencies

```bash
# Navigate to project root
cd mvsdk-api

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### Step 3: Configure Environment

#### Backend Configuration
The backend uses default settings (port 8000). No configuration needed for local development.

#### Frontend Configuration
```bash
cd frontend

# Copy environment template
cp .env.example .env.local

# Edit if needed (default should work)
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the System

### Terminal 1: Start Backend API Server

```bash
# From project root
python camera_api.py
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify backend is running:
```bash
curl http://localhost:8000/health
```

### Terminal 2: Start Frontend Development Server

```bash
# From frontend directory
cd frontend
npm run dev
```

Expected output:
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000
- Ready in 2.3s
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## First Time Usage

### 1. Connect to Camera

1. **Enter API URL** (default: `http://localhost:8000`)
2. Click **"Discover Cameras"** button
3. Select your camera from the dropdown
4. Click **"Connect"** button

You should see:
- ✅ Green "Connected Camera" panel
- Camera details displayed
- Controls enabled

### 2. Start Capturing

1. Click **"Start"** in the Capture Control panel
2. The camera will begin continuous capture mode
3. Status indicator shows "Capturing" with green dot

### 3. Start Video Streaming

1. Click **"Start Stream"** button
2. Live video feed appears in the center panel
3. FPS counter shows in top-right corner
4. Use fullscreen button for expanded view

### 4. Capture a Single Image

1. Click **"Snap Image"** button
2. Image automatically downloads to your Downloads folder
3. Filename format: `snapshot_[timestamp].jpg`

### 5. Adjust Camera Settings

#### Exposure Control
- Toggle **"Auto Exposure"** on/off
- Adjust **Exposure Time** slider (in microseconds)
- Set **Analog Gain** value
- Click **"Apply"** to save changes

#### Monitor Statistics
- **FPS**: Real-time frames per second
- **Captured**: Total frames captured
- **Lost**: Number of lost frames
- **Loss Rate**: Percentage of frame loss

## Common Tasks

### Take High-Quality Photos

```bash
1. Disable auto exposure
2. Set exposure time to 50000 µs (50ms)
3. Set analog gain to 100
4. Click "Apply"
5. Click "Snap Image"
```

### Optimize for Speed

```bash
1. Reduce resolution (via API)
2. Enable auto exposure
3. Monitor FPS in statistics
4. Adjust exposure target if needed
```

### Hardware Trigger Setup

Using the REST API:
```bash
# Set to hardware trigger mode
curl -X PUT http://localhost:8000/cameras/0/trigger \
  -H "Content-Type: application/json" \
  -d '{"trigger_mode": 2, "ext_trig_type": 0}'
```

### Software Trigger

```bash
# In frontend: Click "Software Trigger" button
# Or via API:
curl -X POST http://localhost:8000/cameras/0/trigger/software
```

## Troubleshooting

### Backend Won't Start

**Error**: `No module named 'mvsdk'`
```bash
# Ensure mvsdk.py is in the project directory
ls mvsdk.py

# Check Python path
python -c "import sys; print(sys.path)"
```

**Error**: `libMVSDK.so: cannot open shared object file`
```bash
# Install MindVision SDK
# Add library path to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/path/to/mvsdk:$LD_LIBRARY_PATH
```

### Camera Not Found

```bash
# Check camera IP is reachable
ping <camera_ip>

# Verify camera is on same subnet
ifconfig  # Linux
ipconfig  # Windows

# Check GigE driver installation
# Reinstall MindVision SDK if needed
```

### Frontend Can't Connect to Backend

**Error**: `Network Error` or `ERR_CONNECTION_REFUSED`

```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check frontend API URL
cat frontend/.env.local
# Should be: NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. Check CORS settings
# Backend allows all origins by default

# 4. Restart frontend
cd frontend
npm run dev
```

### WebSocket Stream Not Working

```bash
# 1. Ensure camera is connected first
# 2. Start capture before streaming
# 3. Check browser console for errors (F12)
# 4. Verify WebSocket URL in console:
#    ws://localhost:8000/cameras/0/stream

# 5. Test backend WebSocket directly
npm install -g wscat
wscat -c ws://localhost:8000/cameras/0/stream
```

### Low FPS / Laggy Stream

```bash
# 1. Reduce camera resolution
curl -X PUT http://localhost:8000/cameras/0/resolution \
  -H "Content-Type: application/json" \
  -d '{"width": 1920, "height": 1080}'

# 2. Check network bandwidth
# GigE cameras need ~100MB/s for full resolution

# 3. Use production build (faster)
cd frontend
npm run build
npm start

# 4. Monitor statistics for frame loss
```

## Advanced Features

### Using MQTT for Events

```bash
# 1. Start MQTT broker (Mosquitto)
mosquitto

# 2. Connect via API
curl -X POST http://localhost:8000/mqtt/connect \
  -H "Content-Type: application/json" \
  -d '{"broker": "localhost", "port": 1883, "topic_prefix": "camera"}'

# 3. Subscribe to events
mosquitto_sub -t "camera/#" -v
```

### Save/Load Camera Parameters

```bash
# Save current settings to team 1
curl -X POST http://localhost:8000/cameras/0/parameters/save?team=1

# Load settings from team 1
curl -X POST http://localhost:8000/cameras/0/parameters/load?team=1
```

### Access Interactive API Docs

Open in browser:
```
http://localhost:8000/docs
```

Try out all API endpoints interactively!

## Docker Deployment

### Build and Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- **camera-api**: Backend on port 8000
- **mosquitto**: MQTT broker on ports 1883, 9001

### Build Frontend for Production

```bash
cd frontend
npm run build
npm start
```

Or with Docker:
```bash
cd frontend
docker build -t camera-frontend .
docker run -p 3000:3000 camera-frontend
```

## Production Deployment

### Backend (FastAPI)

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn camera_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Frontend (Next.js)

```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start

# Or use PM2 for process management
npm install -g pm2
pm2 start npm --name "camera-frontend" -- start
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/camera-api

server {
    listen 80;
    server_name camera.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## File Structure

```
mvsdk-api/
├── camera_api.py              # FastAPI backend server
├── mvsdk.py                   # MindVision SDK wrapper
├── requirements.txt           # Python dependencies
├── README.md                  # Backend documentation
├── example_client.py          # Python client example
├── web_client_example.html    # Simple HTML client
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Backend Docker image
├── mosquitto/                 # MQTT broker config
│   └── config/
│       └── mosquitto.conf
└── frontend/                  # Next.js frontend
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── README.md              # Frontend documentation
    └── src/
        ├── app/               # Next.js pages
        ├── components/        # React components
        ├── hooks/             # Custom hooks
        ├── lib/               # API client & utils
        ├── store/             # State management
        └── types/             # TypeScript types
```

## Next Steps

### Explore the API

1. Open interactive docs: http://localhost:8000/docs
2. Try different endpoints
3. Test with Python/JavaScript clients

### Customize the Frontend

1. Modify components in `frontend/src/components/`
2. Add new features to API client
3. Create additional configuration panels
4. Customize styling in Tailwind config

### Add More Features

- Implement white balance control
- Add image processing controls (gamma, contrast, etc.)
- Create trigger configuration panel
- Add I/O control interface
- Implement network configuration
- Add parameter preset management
- Create multi-camera support

## Getting Help

- **Backend API Docs**: `README.md` in project root
- **Frontend Docs**: `frontend/README.md`
- **Interactive API**: http://localhost:8000/docs
- **Example Client**: Run `python example_client.py`
- **Issues**: Check browser console (F12) and terminal logs

## Resources

- **MindVision SDK**: Contact manufacturer for documentation
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs

---

**Congratulations!** 🎉 You now have a fully functional camera control system!

For more detailed information, refer to:
- Backend: `/README.md`
- Frontend: `/frontend/README.md`
- API Documentation: http://localhost:8000/docs
