# MindVision 47MP GigE Vision Camera API

A comprehensive REST API with WebSocket streaming and MQTT event support for controlling the MindVision 47MP GigE Vision industrial camera.

## Features

- **REST API**: Complete control over camera settings and operations
- **WebSocket Streaming**: Real-time video streaming with low latency
- **MQTT Events**: Asynchronous event notifications for camera state changes
- **Comprehensive SDK Coverage**: All MindVision SDK functions exposed via API
- **Auto-generated Documentation**: Interactive Swagger/OpenAPI documentation
- **CORS Support**: Ready for web-based applications

## Architecture

```
┌─────────────────┐
│   Web Client    │
└────────┬────────┘
         │
         ├─── REST API ──────┐
         │                   │
         ├─── WebSocket ─────┤
         │                   │
         └─── MQTT ──────────┤
                             │
                    ┌────────┴────────┐
                    │  Camera API     │
                    │  (FastAPI)      │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  MVSDK Wrapper  │
                    │   (mvsdk.py)    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  MindVision SDK │
                    │  (libMVSDK.so)  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Camera Hardware│
                    │  (GigE Vision)  │
                    └─────────────────┘
```

## Installation

### Prerequisites

1. **MindVision SDK**: Install the MindVision camera SDK and drivers
2. **Python 3.8+**: Required for FastAPI and async support
3. **MQTT Broker** (Optional): For event notifications (e.g., Mosquitto)

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Optional: MQTT Broker Setup

```bash
# Install Mosquitto (Ubuntu/Debian)
sudo apt-get install mosquitto mosquitto-clients

# Start Mosquitto
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

## Quick Start

### 1. Start the API Server

```bash
python camera_api.py
```

The server will start on `http://localhost:8000`

### 2. Access Interactive Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Basic Usage Example

```bash
# Discover cameras
curl http://localhost:8000/cameras/discover

# Connect to first camera
curl -X POST http://localhost:8000/cameras/0/connect

# Start capturing
curl -X POST http://localhost:8000/cameras/0/start

# Capture a single image
curl http://localhost:8000/cameras/0/snap --output snapshot.jpg

# Get camera status
curl http://localhost:8000/cameras/0/status
```

## API Endpoints

### System & Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and version |
| GET | `/health` | Health check |
| GET | `/cameras/discover` | Discover all cameras |
| GET | `/cameras/discover/gige` | Discover GigE cameras |

### Camera Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cameras/{camera_index}/connect` | Connect to camera by index |
| POST | `/cameras/{camera_id}/disconnect` | Disconnect from camera |
| POST | `/cameras/{camera_id}/reconnect` | Reconnect to camera |
| GET | `/cameras/{camera_id}/status` | Get camera status |
| GET | `/cameras/{camera_id}/info` | Get camera information |
| GET | `/cameras/{camera_id}/capability` | Get camera capabilities |

### Image Capture & Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cameras/{camera_id}/start` | Start continuous capture |
| POST | `/cameras/{camera_id}/stop` | Stop capture |
| POST | `/cameras/{camera_id}/pause` | Pause capture |
| GET | `/cameras/{camera_id}/snap` | Capture single image (JPEG/PNG) |
| GET | `/cameras/{camera_id}/frame` | Get frame as JSON (base64) |
| WS | `/cameras/{camera_id}/stream` | WebSocket video streaming |

### Camera Configuration

#### Resolution & Format

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/resolution` | Get current resolution |
| PUT | `/cameras/{camera_id}/resolution` | Set resolution and ROI |
| GET | `/cameras/{camera_id}/media-type` | Get media type |
| PUT | `/cameras/{camera_id}/media-type` | Set media type |

#### Exposure Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/exposure` | Get exposure settings |
| PUT | `/cameras/{camera_id}/exposure` | Set exposure (auto/manual) |
| GET | `/cameras/{camera_id}/exposure/range` | Get exposure range |

#### Gain Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/gain` | Get RGB gains |
| PUT | `/cameras/{camera_id}/gain` | Set RGB gains |

#### White Balance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/white-balance` | Get WB settings |
| PUT | `/cameras/{camera_id}/white-balance` | Set WB (auto/manual) |
| POST | `/cameras/{camera_id}/white-balance/once` | One-time WB |

#### Image Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/image-processing` | Get processing params |
| PUT | `/cameras/{camera_id}/image-processing` | Set gamma, contrast, etc. |

### Trigger Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/trigger` | Get trigger config |
| PUT | `/cameras/{camera_id}/trigger` | Set trigger mode/params |
| POST | `/cameras/{camera_id}/trigger/software` | Send software trigger |

### I/O Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/io/{io_index}` | Get I/O state |
| PUT | `/cameras/{camera_id}/io/{io_index}` | Configure I/O pin |

### Network Configuration (GigE)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/network` | Get network config |
| PUT | `/cameras/{camera_id}/network` | Set IP/subnet/gateway |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras/{camera_id}/statistics` | Get frame statistics |

### Parameter Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cameras/{camera_id}/parameters/save` | Save parameters |
| POST | `/cameras/{camera_id}/parameters/load` | Load parameters |

### MQTT Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mqtt/connect` | Connect to MQTT broker |
| GET | `/mqtt/status` | Get MQTT status |

## Usage Examples

### Python Client

```python
import requests
import json
import base64
from PIL import Image
from io import BytesIO

# Base URL
BASE_URL = "http://localhost:8000"

# Discover cameras
response = requests.get(f"{BASE_URL}/cameras/discover")
cameras = response.json()
print(f"Found {len(cameras)} camera(s)")

# Connect to first camera
camera_index = 0
response = requests.post(f"{BASE_URL}/cameras/{camera_index}/connect")
camera_info = response.json()
camera_id = camera_info["camera_id"]
print(f"Connected to camera {camera_id}")

# Configure exposure
exposure_config = {
    "auto_exposure": False,
    "exposure_time": 30000,  # 30ms
    "analog_gain": 100
}
response = requests.put(
    f"{BASE_URL}/cameras/{camera_id}/exposure",
    json=exposure_config
)

# Start capturing
requests.post(f"{BASE_URL}/cameras/{camera_id}/start")

# Capture single image
response = requests.get(f"{BASE_URL}/cameras/{camera_id}/snap?format=jpeg")
image = Image.open(BytesIO(response.content))
image.save("captured_image.jpg")

# Get frame as base64
response = requests.get(f"{BASE_URL}/cameras/{camera_id}/frame?encoding=base64")
frame_data = response.json()
image_data = base64.b64decode(frame_data["image"])
image = Image.open(BytesIO(image_data))

# Get statistics
response = requests.get(f"{BASE_URL}/cameras/{camera_id}/statistics")
stats = response.json()
print(f"Captured: {stats['captured_frames']}, Lost: {stats['lost_frames']}")

# Stop and disconnect
requests.post(f"{BASE_URL}/cameras/{camera_id}/stop")
requests.post(f"{BASE_URL}/cameras/{camera_id}/disconnect")
```

### JavaScript/TypeScript Client

```javascript
// Discover cameras
const response = await fetch('http://localhost:8000/cameras/discover');
const cameras = await response.json();
console.log(`Found ${cameras.length} camera(s)`);

// Connect to camera
const connectResponse = await fetch(
  'http://localhost:8000/cameras/0/connect',
  { method: 'POST' }
);
const cameraInfo = await connectResponse.json();
const cameraId = cameraInfo.camera_id;

// Configure camera
await fetch(`http://localhost:8000/cameras/${cameraId}/exposure`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    auto_exposure: false,
    exposure_time: 30000,
    analog_gain: 100
  })
});

// Start capturing
await fetch(`http://localhost:8000/cameras/${cameraId}/start`, {
  method: 'POST'
});

// Capture image
const imageResponse = await fetch(
  `http://localhost:8000/cameras/${cameraId}/snap?format=jpeg`
);
const imageBlob = await imageResponse.blob();
const imageUrl = URL.createObjectURL(imageBlob);
document.getElementById('image').src = imageUrl;
```

### WebSocket Streaming

```javascript
// WebSocket video streaming
const ws = new WebSocket(`ws://localhost:8000/cameras/${cameraId}/stream`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const img = document.getElementById('video-stream');
  img.src = `data:image/jpeg;base64,${data.image}`;
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

### Python WebSocket Client

```python
import asyncio
import websockets
import json
import base64
from PIL import Image
from io import BytesIO

async def stream_camera():
    uri = "ws://localhost:8000/cameras/0/stream"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            # Decode base64 image
            image_data = base64.b64decode(data["image"])
            image = Image.open(BytesIO(image_data))

            # Process image
            print(f"Received frame: {data['width']}x{data['height']}")

            # Save or display
            image.save(f"frame_{data['timestamp']}.jpg")

asyncio.run(stream_camera())
```

### MQTT Event Subscription

```python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    # Subscribe to all camera events
    client.subscribe("camera/#")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    print(f"Payload: {msg.payload.decode()}")

# Connect to MQTT broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()
```

### Configure MQTT via API

```python
import requests

# Connect to MQTT broker
mqtt_config = {
    "broker": "localhost",
    "port": 1883,
    "topic_prefix": "camera"
}
response = requests.post(
    "http://localhost:8000/mqtt/connect",
    json=mqtt_config
)
print(response.json())
```

## MQTT Event Topics

When MQTT is configured, the API publishes events to the following topics:

- `camera/{camera_id}/connected` - Camera connected
- `camera/{camera_id}/disconnected` - Camera disconnected
- `camera/{camera_id}/reconnected` - Camera reconnected
- `camera/{camera_id}/capture_started` - Capture started
- `camera/{camera_id}/capture_stopped` - Capture stopped
- `camera/{camera_id}/capture_paused` - Capture paused
- `camera/{camera_id}/image_snapped` - Single image captured
- `camera/{camera_id}/exposure_changed` - Exposure settings changed
- `camera/{camera_id}/gain_changed` - Gain settings changed
- `camera/{camera_id}/white_balance_changed` - White balance changed
- `camera/{camera_id}/resolution_changed` - Resolution changed
- `camera/{camera_id}/trigger_config_changed` - Trigger configuration changed
- `camera/{camera_id}/software_trigger` - Software trigger sent

### Event Payload Example

```json
{
  "timestamp": "2025-01-17T10:30:45.123456",
  "camera_id": 12345,
  "event": "exposure_changed",
  "data": {
    "auto_exposure": false,
    "exposure_time": 30000,
    "analog_gain": 100
  }
}
```

## Configuration Examples

### Set Resolution and ROI

```python
resolution_config = {
    "width": 1920,
    "height": 1080,
    "offset_x": 100,
    "offset_y": 100
}
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/resolution",
    json=resolution_config
)
```

### Configure Hardware Trigger

```python
trigger_config = {
    "trigger_mode": 2,  # Hardware trigger
    "trigger_delay": 1000,  # 1ms delay
    "trigger_count": 1,
    "ext_trig_type": 0  # Rising edge
}
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/trigger",
    json=trigger_config
)
```

### Configure I/O Pin as Output

```python
io_config = {
    "io_index": 0,
    "mode": 3,  # GPIO output
    "state": 1  # High
}
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/io/0",
    json=io_config
)
```

### Set White Balance

```python
wb_config = {
    "auto_wb": False,
    "r_gain": 120,
    "g_gain": 100,
    "b_gain": 110
}
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/white-balance",
    json=wb_config
)
```

### Configure Image Processing

```python
processing_config = {
    "gamma": 100,
    "contrast": 100,
    "saturation": 100,
    "sharpness": 3,
    "noise_filter": True,
    "monochrome": False,
    "inverse": False
}
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/image-processing",
    json=processing_config
)
```

### Set GigE Network Configuration

```python
network_config = {
    "ip_address": "192.168.1.100",
    "subnet_mask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "persistent": True
}
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/network",
    json=network_config
)
```

## Advanced Features

### Parameter Teams

Save and load different camera configurations:

```python
# Save current settings to team 1
requests.post(f"{BASE_URL}/cameras/{camera_id}/parameters/save?team=1")

# Load settings from team 1
requests.post(f"{BASE_URL}/cameras/{camera_id}/parameters/load?team=1")
```

### Frame Statistics

Monitor camera performance:

```python
response = requests.get(f"{BASE_URL}/cameras/{camera_id}/statistics")
stats = response.json()
print(f"Loss rate: {stats['loss_rate']*100:.2f}%")
```

### Software Trigger

Trigger frame capture programmatically:

```python
# Set to software trigger mode
requests.put(
    f"{BASE_URL}/cameras/{camera_id}/trigger",
    json={"trigger_mode": 1}
)

# Send trigger
requests.post(f"{BASE_URL}/cameras/{camera_id}/trigger/software")
```

## Production Deployment

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY requirements.txt .
COPY camera_api.py .
COPY mvsdk.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "camera_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t camera-api .
docker run -p 8000:8000 --network host camera-api
```

### Using systemd Service

Create `/etc/systemd/system/camera-api.service`:

```ini
[Unit]
Description=MindVision Camera API
After=network.target

[Service]
Type=simple
User=camera
WorkingDirectory=/opt/camera-api
Environment="PATH=/opt/camera-api/venv/bin"
ExecStart=/opt/camera-api/venv/bin/uvicorn camera_api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable camera-api
sudo systemctl start camera-api
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name camera-api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Camera Not Found

```bash
# Check if camera is on network
ping <camera_ip>

# Check GigE filter driver (Windows)
# Reinstall MindVision SDK drivers

# Check permissions (Linux)
sudo chmod 666 /dev/bus/usb/...
```

### Connection Timeout

```python
# Increase timeout
response = requests.get(
    f"{BASE_URL}/cameras/{camera_id}/snap?timeout=5000"
)
```

### Frame Drops

```python
# Check statistics
stats = requests.get(f"{BASE_URL}/cameras/{camera_id}/statistics").json()
if stats['loss_rate'] > 0.01:  # More than 1% loss
    # Reduce resolution or frame rate
    # Check network bandwidth
    # Adjust packet size for GigE
```

## License

This API wrapper is provided as-is. The MindVision SDK is proprietary and requires appropriate licensing.

## Support

For issues related to:
- **API**: Check the interactive docs at `/docs`
- **SDK**: Consult MindVision SDK documentation
- **Hardware**: Contact MindVision support

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All endpoints are documented
- Tests are included for new features
