'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Video, VideoOff, Maximize2, Minimize2 } from 'lucide-react';
import useCameraStore from '@/store/camera-store';
import { getAPIClient } from '@/lib/api-client';
import type { StreamFrame } from '@/types/camera';
import { calculateFPS } from '@/lib/utils';

interface VideoStreamProps {
  className?: string;
}

export default function VideoStream({ className = '' }: VideoStreamProps) {
  const { currentCamera, isStreaming, setIsStreaming, setFPS, apiURL } = useCameraStore();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [frameSize, setFrameSize] = useState({ width: 0, height: 0 });
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const wsRef = useRef<WebSocket | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());

  const api = getAPIClient(apiURL);

  const connectWebSocket = useCallback(() => {
    if (!currentCamera || wsRef.current) return;

    const wsURL = api.getStreamURL(currentCamera.camera_id, apiURL);

    try {
      const ws = new WebSocket(wsURL);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsStreaming(true);
        frameCountRef.current = 0;
        lastFpsUpdateRef.current = Date.now();
      };

      ws.onmessage = (event) => {
        try {
          const data: StreamFrame = JSON.parse(event.data);

          if (imgRef.current) {
            imgRef.current.src = `data:image/jpeg;base64,${data.image}`;
          }

          setFrameSize({ width: data.width, height: data.height });
          setLastUpdate(data.timestamp);

          // Update FPS
          frameCountRef.current++;
          const now = Date.now();
          const elapsed = now - lastFpsUpdateRef.current;

          if (elapsed >= 1000) {
            const fps = calculateFPS(frameCountRef.current, elapsed);
            setFPS(Math.round(fps));
            frameCountRef.current = 0;
            lastFpsUpdateRef.current = now;
          }
        } catch (error) {
          console.error('Failed to process frame:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsStreaming(false);
        setFPS(0);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [currentCamera, apiURL, api, setIsStreaming, setFPS]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsStreaming(false);
      setFPS(0);
    }
  }, [setIsStreaming, setFPS]);

  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  const handleToggleStream = () => {
    if (isStreaming) {
      disconnectWebSocket();
    } else {
      connectWebSocket();
    }
  };

  return (
    <div className={`${className}`}>
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-primary-600 to-secondary-600 text-white px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Video className="w-5 h-5" />
            <h2 className="font-semibold">Live Stream</h2>
          </div>
          <div className="flex items-center space-x-4">
            {frameSize.width > 0 && (
              <span className="text-sm">
                {frameSize.width} × {frameSize.height}
              </span>
            )}
            <button
              onClick={toggleFullscreen}
              className="p-1 hover:bg-white/20 rounded transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div
          ref={containerRef}
          className="relative bg-black aspect-video flex items-center justify-center"
        >
          {currentCamera ? (
            <>
              <img
                ref={imgRef}
                alt="Camera stream"
                className="max-w-full max-h-full object-contain"
              />
              {!isStreaming && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/80">
                  <div className="text-center text-white">
                    <VideoOff className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg mb-2">Stream not active</p>
                    <button
                      onClick={handleToggleStream}
                      className="px-6 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                    >
                      Start Streaming
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-gray-400">
              <VideoOff className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No camera connected</p>
            </div>
          )}
        </div>

        <div className="bg-gray-50 px-4 py-3 flex items-center justify-between text-sm">
          <div className="text-gray-600">
            {lastUpdate && <span>Last update: {new Date(lastUpdate).toLocaleTimeString()}</span>}
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleToggleStream}
              disabled={!currentCamera}
              className={`px-4 py-1.5 rounded-lg font-medium transition-colors ${
                isStreaming
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-primary-600 hover:bg-primary-700 text-white disabled:bg-gray-300 disabled:cursor-not-allowed'
              }`}
            >
              {isStreaming ? 'Stop Stream' : 'Start Stream'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
