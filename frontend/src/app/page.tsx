'use client';

import { Camera } from 'lucide-react';
import CameraControl from '@/components/CameraControl';
import CaptureControl from '@/components/CaptureControl';
import VideoStream from '@/components/VideoStream';
import ExposureControl from '@/components/ExposureControl';
import StatsDashboard from '@/components/StatsDashboard';
import useCameraStore from '@/store/camera-store';

export default function Home() {
  const { fps } = useCameraStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-primary-600 via-primary-700 to-secondary-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
                <Camera className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">MindVision Camera Control</h1>
                <p className="text-primary-100 text-sm">Professional GigE Vision Interface</p>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              {fps > 0 && (
                <div className="flex items-center space-x-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-lg">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="font-mono font-semibold">{fps} FPS</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Controls */}
          <div className="lg:col-span-3 space-y-6">
            <CameraControl />
            <CaptureControl />
            <ExposureControl />
          </div>

          {/* Center - Video Stream */}
          <div className="lg:col-span-6">
            <VideoStream />
          </div>

          {/* Right Sidebar - Statistics */}
          <div className="lg:col-span-3 space-y-6">
            <StatsDashboard />

            {/* Quick Info Card */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Quick Info</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• Connect to camera first</p>
                <p>• Start capture for live view</p>
                <p>• Use snap to save images</p>
                <p>• Adjust exposure & gain</p>
                <p>• Monitor real-time stats</p>
              </div>
            </div>

            {/* System Info Card */}
            <div className="bg-gradient-to-br from-primary-50 to-secondary-50 rounded-lg shadow-lg p-6 border border-primary-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">System</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">API:</span>
                  <span className="font-medium text-gray-900">
                    {useCameraStore.getState().apiURL.replace('http://', '')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-medium ${useCameraStore.getState().isConnected ? 'text-green-600' : 'text-gray-500'}`}>
                    {useCameraStore.getState().isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200 bg-white/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600">
          <p>MindVision 47MP GigE Vision Camera Control System</p>
          <p className="mt-1">Built with Next.js, React & FastAPI</p>
        </div>
      </footer>
    </div>
  );
}
