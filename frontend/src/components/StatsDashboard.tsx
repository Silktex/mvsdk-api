'use client';

import { useEffect, useState } from 'react';
import { Activity, Camera, AlertCircle, Zap } from 'lucide-react';
import useCameraStore from '@/store/camera-store';
import { getAPIClient } from '@/lib/api-client';
import { formatPercentage } from '@/lib/utils';

export default function StatsDashboard() {
  const { currentCamera, isConnected, fps, apiURL } = useCameraStore();
  const api = getAPIClient(apiURL);

  const [stats, setStats] = useState({
    total_frames: 0,
    captured_frames: 0,
    lost_frames: 0,
    loss_rate: 0,
  });

  useEffect(() => {
    if (!currentCamera) return;

    const interval = setInterval(async () => {
      try {
        const newStats = await api.getStatistics(currentCamera.camera_id);
        setStats(newStats);
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [currentCamera, api]);

  if (!isConnected || !currentCamera) {
    return null;
  }

  const statItems = [
    {
      label: 'FPS',
      value: fps,
      icon: Zap,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Captured',
      value: stats.captured_frames.toLocaleString(),
      icon: Camera,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Lost',
      value: stats.lost_frames.toLocaleString(),
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    {
      label: 'Loss Rate',
      value: formatPercentage(stats.loss_rate),
      icon: Activity,
      color: stats.loss_rate > 0.01 ? 'text-red-600' : 'text-green-600',
      bgColor: stats.loss_rate > 0.01 ? 'bg-red-50' : 'bg-green-50',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>

      <div className="grid grid-cols-2 gap-4">
        {statItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <div
              key={index}
              className={`${item.bgColor} rounded-lg p-4 border border-gray-200`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">{item.label}</span>
                <Icon className={`w-5 h-5 ${item.color}`} />
              </div>
              <div className={`text-2xl font-bold ${item.color}`}>{item.value}</div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Total Frames:</span>
          <span className="font-semibold text-gray-900">
            {stats.total_frames.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}
