'use client';

import { useEffect, useState } from 'react';
import { Sun, Save } from 'lucide-react';
import useCameraStore from '@/store/camera-store';
import { useCamera } from '@/hooks/use-camera';
import { getAPIClient } from '@/lib/api-client';

export default function ExposureControl() {
  const { currentCamera, isConnected, apiURL } = useCameraStore();
  const { updateExposure } = useCamera();
  const api = getAPIClient(apiURL);

  const [autoExposure, setAutoExposure] = useState(true);
  const [exposureTime, setExposureTime] = useState(30000);
  const [analogGain, setAnalogGain] = useState(100);
  const [aeTarget, setAeTarget] = useState(128);
  const [exposureRange, setExposureRange] = useState({ min: 0, max: 1000000 });

  useEffect(() => {
    if (currentCamera) {
      loadSettings();
    }
  }, [currentCamera]);

  const loadSettings = async () => {
    if (!currentCamera) return;

    try {
      const exposure = await api.getExposure(currentCamera.camera_id);
      setAutoExposure(exposure.auto_exposure);
      setExposureTime(exposure.exposure_time);
      setAnalogGain(exposure.analog_gain);

      const range = await api.getExposureRange(currentCamera.camera_id);
      setExposureRange({ min: range.min_exposure_time, max: range.max_exposure_time });
    } catch (error) {
      console.error('Failed to load exposure settings:', error);
    }
  };

  const handleApply = async () => {
    await updateExposure({
      auto_exposure: autoExposure,
      exposure_time: autoExposure ? undefined : exposureTime,
      analog_gain: autoExposure ? undefined : analogGain,
      ae_target: autoExposure ? aeTarget : undefined,
    });
  };

  if (!isConnected || !currentCamera) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Sun className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold text-gray-900">Exposure Control</h2>
      </div>

      <div className="space-y-4">
        {/* Auto Exposure Toggle */}
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">Auto Exposure</label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={autoExposure}
              onChange={(e) => setAutoExposure(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
          </label>
        </div>

        {autoExposure ? (
          /* Auto Exposure Target */
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AE Target Brightness (0-255)
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="range"
                min="0"
                max="255"
                value={aeTarget}
                onChange={(e) => setAeTarget(Number(e.target.value))}
                className="flex-1"
              />
              <input
                type="number"
                value={aeTarget}
                onChange={(e) => setAeTarget(Number(e.target.value))}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-center"
                min="0"
                max="255"
              />
            </div>
          </div>
        ) : (
          <>
            {/* Manual Exposure Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Exposure Time (µs)
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min={exposureRange.min}
                  max={exposureRange.max}
                  step="100"
                  value={exposureTime}
                  onChange={(e) => setExposureTime(Number(e.target.value))}
                  className="flex-1"
                />
                <input
                  type="number"
                  value={exposureTime}
                  onChange={(e) => setExposureTime(Number(e.target.value))}
                  className="w-24 px-2 py-1 border border-gray-300 rounded text-right"
                  min={exposureRange.min}
                  max={exposureRange.max}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Range: {exposureRange.min} - {exposureRange.max} µs
              </p>
            </div>

            {/* Analog Gain */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analog Gain
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="16"
                  max="512"
                  value={analogGain}
                  onChange={(e) => setAnalogGain(Number(e.target.value))}
                  className="flex-1"
                />
                <input
                  type="number"
                  value={analogGain}
                  onChange={(e) => setAnalogGain(Number(e.target.value))}
                  className="w-20 px-2 py-1 border border-gray-300 rounded text-center"
                  min="16"
                  max="512"
                />
              </div>
            </div>
          </>
        )}

        <button
          onClick={handleApply}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
        >
          <Save className="w-4 h-4" />
          <span>Apply</span>
        </button>
      </div>
    </div>
  );
}
