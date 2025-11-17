# MindVision Camera Frontend

A modern, professional Next.js frontend for controlling the MindVision 47MP GigE Vision industrial camera. Built with React, TypeScript, and Tailwind CSS.

## Features

- 🎥 **Real-time Video Streaming**: WebSocket-based live video feed with FPS counter
- 🎛️ **Camera Control**: Connect, disconnect, and manage camera settings
- 📸 **Image Capture**: Start/stop/pause capture and snap single images
- ⚙️ **Configuration**: Adjust exposure, gain, white balance, and more
- 📊 **Live Statistics**: Real-time frame statistics and performance monitoring
- 🎨 **Modern UI**: Responsive design with Tailwind CSS
- 🔄 **State Management**: Zustand for efficient state management
- 🎯 **Type-Safe**: Full TypeScript support
- 🚀 **Optimized**: Server-side rendering and performance optimizations

## Screenshots

### Main Interface
![Main Interface](https://via.placeholder.com/800x500?text=Camera+Control+Interface)

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Notifications**: React Hot Toast
- **Real-time**: WebSocket

## Prerequisites

- Node.js 18+ and npm 9+
- Camera API Backend running (see parent directory)
- Modern web browser with WebSocket support

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type checking
npm run type-check
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                  # Next.js app directory
│   │   ├── layout.tsx        # Root layout
│   │   ├── page.tsx          # Main page
│   │   └── globals.css       # Global styles
│   ├── components/           # React components
│   │   ├── VideoStream.tsx   # WebSocket video streaming
│   │   ├── CameraControl.tsx # Camera connection panel
│   │   ├── CaptureControl.tsx# Capture controls
│   │   ├── ExposureControl.tsx # Exposure settings
│   │   └── StatsDashboard.tsx # Statistics display
│   ├── hooks/                # Custom React hooks
│   │   └── use-camera.ts     # Camera operations hook
│   ├── lib/                  # Utility functions
│   │   ├── api-client.ts     # API client wrapper
│   │   └── utils.ts          # Helper functions
│   ├── store/                # State management
│   │   └── camera-store.ts   # Zustand camera store
│   └── types/                # TypeScript types
│       └── camera.ts         # Camera-related types
├── public/                   # Static assets
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript config
├── tailwind.config.ts        # Tailwind CSS config
├── next.config.js            # Next.js config
└── README.md                 # This file
```

## Usage Guide

### 1. Connect to Camera

1. Ensure the Camera API backend is running
2. Click "Discover Cameras" to find available cameras
3. Select a camera from the dropdown
4. Click "Connect" to establish connection

### 2. Start Live Streaming

1. After connecting, navigate to the video stream section
2. Click "Start Stream" to begin WebSocket streaming
3. Monitor FPS in the top-right corner
4. Click "Stop Stream" to end streaming

### 3. Capture Images

1. Click "Start" in the Capture Control panel to begin continuous capture
2. Click "Snap Image" to save a single image
3. Use "Pause" or "Stop" to control capture

### 4. Adjust Settings

#### Exposure Control
- Toggle "Auto Exposure" for automatic exposure
- Adjust "Exposure Time" slider for manual control
- Set "Analog Gain" to control sensor sensitivity
- Use "AE Target" to set auto-exposure brightness goal

#### Image Processing
- Adjust gamma, contrast, saturation
- Enable/disable noise filtering
- Configure sharpness levels

#### Trigger Control
- Select trigger mode (Continuous/Software/Hardware)
- Set trigger delay and count
- Use "Software Trigger" button for manual triggers

### 5. Monitor Statistics

The Statistics Dashboard displays real-time information:
- **FPS**: Current frames per second
- **Captured**: Total frames captured successfully
- **Lost**: Number of lost frames
- **Loss Rate**: Percentage of frames lost

## API Integration

The frontend communicates with the backend API through the `CameraAPIClient` class in `src/lib/api-client.ts`.

### Example Usage

```typescript
import { getAPIClient } from '@/lib/api-client';

const api = getAPIClient('http://localhost:8000');

// Discover cameras
const cameras = await api.discoverCameras();

// Connect to camera
const camera = await api.connectCamera(0);

// Start capture
await api.startCapture(camera.camera_id);

// Get frame
const frame = await api.getFrame(camera.camera_id);

// Update exposure
await api.setExposure(camera.camera_id, {
  auto_exposure: false,
  exposure_time: 30000,
  analog_gain: 100
});
```

### WebSocket Streaming

```typescript
const wsURL = api.getStreamURL(cameraId);
const ws = new WebSocket(wsURL);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.image contains base64 JPEG
  // data.width, data.height, data.timestamp
};
```

## State Management

The application uses Zustand for state management. Access the camera store:

```typescript
import useCameraStore from '@/store/camera-store';

function Component() {
  const {
    currentCamera,
    isConnected,
    isCapturing,
    fps,
    setIsCapturing,
  } = useCameraStore();

  // Use state...
}
```

## Custom Hooks

### `useCamera()`

Provides camera operations:

```typescript
const {
  discoverCameras,
  connectCamera,
  disconnectCamera,
  startCapture,
  stopCapture,
  snapImage,
  updateExposure,
  updateGain,
  softwareTrigger,
} = useCamera();
```

## Styling

The project uses Tailwind CSS for styling. Custom theme colors are defined in `tailwind.config.ts`:

- **Primary**: Purple/Blue gradient (#667eea)
- **Secondary**: Purple gradient (#764ba2)

### Custom Components

Create styled components using Tailwind:

```tsx
<button className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
  Click Me
</button>
```

### Utility Classes

Use the `cn()` utility for conditional classes:

```typescript
import { cn } from '@/lib/utils';

<div className={cn(
  'base-classes',
  condition && 'conditional-classes'
)} />
```

## Production Deployment

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Rebuild source code
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

Update `next.config.js`:

```javascript
const nextConfig = {
  output: 'standalone',
  // ... other config
}
```

Build and run:

```bash
docker build -t camera-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 camera-frontend
```

### Environment Variables for Production

Set these environment variables in production:

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NODE_ENV=production
```

## Troubleshooting

### Cannot Connect to API

**Problem**: "Failed to discover cameras" error

**Solution**:
1. Verify API backend is running: `http://localhost:8000/health`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Verify CORS settings in backend allow frontend origin
4. Check browser console for detailed errors

### WebSocket Connection Failed

**Problem**: "WebSocket error" in console

**Solution**:
1. Ensure camera is connected via API first
2. Verify WebSocket URL is correct (ws:// not http://)
3. Check firewall settings allow WebSocket connections
4. Verify backend WebSocket endpoint is working

### Slow Performance

**Problem**: Low FPS or laggy interface

**Solution**:
1. Reduce camera resolution in backend
2. Adjust JPEG quality in backend streaming
3. Check network bandwidth
4. Close unused browser tabs
5. Use production build (`npm run build && npm start`)

### Type Errors

**Problem**: TypeScript errors during development

**Solution**:
```bash
# Clear .next directory
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Run type checking
npm run type-check
```

## Development Tips

### Hot Reload

Next.js supports hot module replacement. Changes to components will automatically reload without losing state.

### Debugging

1. Use React DevTools browser extension
2. Check browser console for errors
3. Use `console.log()` or debugger statements
4. Monitor network tab for API requests

### Adding New Features

1. Create new component in `src/components/`
2. Add API methods to `src/lib/api-client.ts`
3. Update types in `src/types/camera.ts`
4. Create custom hook in `src/hooks/` if needed
5. Update store in `src/store/` for state management

### Code Style

- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Keep components small and focused
- Use async/await for promises
- Handle errors gracefully

## Performance Optimization

### Image Optimization

- Backend sends JPEG with adjustable quality
- Use base64 encoding for WebSocket streaming
- Consider reducing resolution for better FPS

### Bundle Size

```bash
# Analyze bundle size
npm run build

# Check .next/static directory size
du -sh .next/static
```

### Caching

- API responses cached where appropriate
- Static assets cached by Next.js
- Use React.memo() for expensive components

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is part of the MindVision Camera API system.

## Support

For issues or questions:

- Backend API: See `../README.md`
- Frontend: Check browser console and Network tab
- GitHub Issues: Report bugs and feature requests

## Roadmap

- [ ] Add more camera configuration options
- [ ] Implement parameter presets
- [ ] Add image annotation tools
- [ ] Support multiple camera views
- [ ] Add recording functionality
- [ ] Implement MQTT event display
- [ ] Add user authentication
- [ ] Create mobile-responsive version

## Acknowledgments

- Next.js team for the amazing framework
- Tailwind CSS for the utility-first CSS framework
- Lucide for beautiful icons
- Zustand for simple state management
