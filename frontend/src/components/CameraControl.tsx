'use client';

import { useEffect, useState } from 'react';
import { Camera, RefreshCw, Power, PowerOff } from 'lucide-react';
import useCameraStore from '@/store/camera-store';
import { useCamera } from '@/hooks/use-camera';
import type { CameraInfo } from '@/types/camera';

export default function CameraControl() {
  const {
    availableCameras,
    currentCamera,
    isConnected,
    isLoading,
  } = useCameraStore();

  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  const {
    discoverCameras,
    connectCamera,
    disconnectCamera,
  } = useCamera();

  useEffect(() => {
    // Auto-discover cameras on mount
    discoverCameras();
  }, []);

  const handleConnect = async () => {
    if (selectedIndex !== null) {
      await connectCamera(selectedIndex);
    }
  };

  const handleDisconnect = async () => {
    await disconnectCamera();
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Camera className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold text-gray-900">Camera Connection</h2>
      </div>

      <div className="space-y-4">
        {/* API URL Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API URL
          </label>
          <input
            type="text"
            value={useCameraStore.getState().apiURL}
            onChange={(e) => useCameraStore.getState().setAPIURL(e.target.value)}
            disabled={isConnected}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="http://localhost:8000"
          />
        </div>

        {/* Discover Button */}
        <button
          onClick={discoverCameras}
          disabled={isLoading || isConnected}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-primary-100 hover:bg-primary-200 text-primary-700 rounded-lg transition-colors disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Discover Cameras</span>
        </button>

        {/* Camera Selection */}
        {availableCameras.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Camera
            </label>
            <select
              value={selectedIndex}
              onChange={(e) => setSelectedIndex(Number(e.target.value))}
              disabled={isConnected}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              {availableCameras.map((camera, index) => (
                <option key={camera.serial_number} value={index}>
                  {camera.friendly_name} ({camera.serial_number})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Connection Buttons */}
        {!isConnected ? (
          <button
            onClick={handleConnect}
            disabled={isLoading || availableCameras.length === 0}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Power className="w-5 h-5" />
            <span>Connect</span>
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            disabled={isLoading}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <PowerOff className="w-5 h-5" />
            <span>Disconnect</span>
          </button>
        )}

        {/* Current Camera Info */}
        {currentCamera && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-sm font-semibold text-green-900 mb-2">Connected Camera</h3>
            <dl className="space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-600">Name:</dt>
                <dd className="text-gray-900 font-medium">{currentCamera.friendly_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Type:</dt>
                <dd className="text-gray-900">{currentCamera.sensor_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Port:</dt>
                <dd className="text-gray-900">{currentCamera.port_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">ID:</dt>
                <dd className="text-gray-900 font-mono">{currentCamera.camera_id}</dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
