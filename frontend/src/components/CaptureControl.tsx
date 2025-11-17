'use client';

import { Play, Pause, Square, Camera } from 'lucide-react';
import useCameraStore from '@/store/camera-store';
import { useCamera } from '@/hooks/use-camera';

export default function CaptureControl() {
  const { currentCamera, isCapturing, isConnected } = useCameraStore();
  const { startCapture, stopCapture, pauseCapture, snapImage } = useCamera();

  if (!isConnected || !currentCamera) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Capture Control</h2>
        <p className="text-gray-500 text-center py-8">Connect a camera to enable controls</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Capture Control</h2>

      <div className="grid grid-cols-2 gap-3">
        {!isCapturing ? (
          <button
            onClick={startCapture}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
          >
            <Play className="w-5 h-5" />
            <span>Start</span>
          </button>
        ) : (
          <>
            <button
              onClick={pauseCapture}
              className="flex items-center justify-center space-x-2 px-4 py-3 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors"
            >
              <Pause className="w-5 h-5" />
              <span>Pause</span>
            </button>
            <button
              onClick={stopCapture}
              className="flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
            >
              <Square className="w-5 h-5" />
              <span>Stop</span>
            </button>
          </>
        )}
      </div>

      <button
        onClick={snapImage}
        className="w-full mt-3 flex items-center justify-center space-x-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
      >
        <Camera className="w-5 h-5" />
        <span>Snap Image</span>
      </button>

      {isCapturing && (
        <div className="mt-4 flex items-center justify-center space-x-2 text-green-600">
          <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">Capturing</span>
        </div>
      )}
    </div>
  );
}
