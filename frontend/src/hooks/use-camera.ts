import { useCallback } from 'react';
import { toast } from 'react-hot-toast';
import useCameraStore from '@/store/camera-store';
import { getAPIClient } from '@/lib/api-client';
import type { ExposureConfig, GainConfig, WhiteBalanceConfig, TriggerConfig, ImageProcessingConfig } from '@/types/camera';

export function useCamera() {
  const store = useCameraStore();
  const api = getAPIClient(store.apiURL);

  const discoverCameras = useCallback(async () => {
    store.setIsLoading(true);
    store.setError(null);

    try {
      const cameras = await api.discoverCameras();
      store.setAvailableCameras(cameras);
      toast.success(`Found ${cameras.length} camera(s)`);
      return cameras;
    } catch (error: any) {
      const message = error.message || 'Failed to discover cameras';
      store.setError(message);
      toast.error(message);
      throw error;
    } finally {
      store.setIsLoading(false);
    }
  }, [api, store]);

  const connectCamera = useCallback(
    async (cameraIndex: number) => {
      store.setIsLoading(true);
      store.setError(null);

      try {
        const camera = await api.connectCamera(cameraIndex);
        store.setCurrentCamera(camera);
        store.setIsConnected(true);

        // Fetch capability
        const capability = await api.getCameraCapability(camera.camera_id);
        store.setCameraCapability(capability);

        // Fetch status
        const status = await api.getCameraStatus(camera.camera_id);
        store.setCameraStatus(status);

        toast.success(`Connected to ${camera.friendly_name}`);
        return camera;
      } catch (error: any) {
        const message = error.message || 'Failed to connect camera';
        store.setError(message);
        toast.error(message);
        throw error;
      } finally {
        store.setIsLoading(false);
      }
    },
    [api, store]
  );

  const disconnectCamera = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    store.setIsLoading(true);
    store.setError(null);

    try {
      await api.disconnectCamera(cameraId);
      store.reset();
      toast.success('Camera disconnected');
    } catch (error: any) {
      const message = error.message || 'Failed to disconnect camera';
      store.setError(message);
      toast.error(message);
      throw error;
    } finally {
      store.setIsLoading(false);
    }
  }, [api, store]);

  const startCapture = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      await api.startCapture(cameraId);
      store.setIsCapturing(true);
      toast.success('Capture started');
    } catch (error: any) {
      toast.error(error.message || 'Failed to start capture');
      throw error;
    }
  }, [api, store]);

  const stopCapture = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      await api.stopCapture(cameraId);
      store.setIsCapturing(false);
      toast.success('Capture stopped');
    } catch (error: any) {
      toast.error(error.message || 'Failed to stop capture');
      throw error;
    }
  }, [api, store]);

  const pauseCapture = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      await api.pauseCapture(cameraId);
      toast.success('Capture paused');
    } catch (error: any) {
      toast.error(error.message || 'Failed to pause capture');
      throw error;
    }
  }, [api, store]);

  const snapImage = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      const blob = await api.snapImage(cameraId, 'jpeg');
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `snapshot_${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success('Image captured');
    } catch (error: any) {
      toast.error(error.message || 'Failed to capture image');
      throw error;
    }
  }, [api, store]);

  const updateExposure = useCallback(
    async (config: ExposureConfig) => {
      const cameraId = store.currentCamera?.camera_id;
      if (!cameraId) return;

      try {
        await api.setExposure(cameraId, config);
        toast.success('Exposure updated');
      } catch (error: any) {
        toast.error(error.message || 'Failed to update exposure');
        throw error;
      }
    },
    [api, store]
  );

  const updateGain = useCallback(
    async (config: GainConfig) => {
      const cameraId = store.currentCamera?.camera_id;
      if (!cameraId) return;

      try {
        await api.setGain(cameraId, config);
        toast.success('Gain updated');
      } catch (error: any) {
        toast.error(error.message || 'Failed to update gain');
        throw error;
      }
    },
    [api, store]
  );

  const updateWhiteBalance = useCallback(
    async (config: WhiteBalanceConfig) => {
      const cameraId = store.currentCamera?.camera_id;
      if (!cameraId) return;

      try {
        await api.setWhiteBalance(cameraId, config);
        toast.success('White balance updated');
      } catch (error: any) {
        toast.error(error.message || 'Failed to update white balance');
        throw error;
      }
    },
    [api, store]
  );

  const setOnceWhiteBalance = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      await api.setOnceWhiteBalance(cameraId);
      toast.success('One-time white balance set');
    } catch (error: any) {
      toast.error(error.message || 'Failed to set white balance');
      throw error;
    }
  }, [api, store]);

  const updateImageProcessing = useCallback(
    async (config: ImageProcessingConfig) => {
      const cameraId = store.currentCamera?.camera_id;
      if (!cameraId) return;

      try {
        await api.setImageProcessing(cameraId, config);
        toast.success('Image processing updated');
      } catch (error: any) {
        toast.error(error.message || 'Failed to update image processing');
        throw error;
      }
    },
    [api, store]
  );

  const updateTrigger = useCallback(
    async (config: TriggerConfig) => {
      const cameraId = store.currentCamera?.camera_id;
      if (!cameraId) return;

      try {
        await api.setTrigger(cameraId, config);
        toast.success('Trigger updated');
      } catch (error: any) {
        toast.error(error.message || 'Failed to update trigger');
        throw error;
      }
    },
    [api, store]
  );

  const softwareTrigger = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      await api.softwareTrigger(cameraId);
      toast.success('Software trigger sent');
    } catch (error: any) {
      toast.error(error.message || 'Failed to send trigger');
      throw error;
    }
  }, [api, store]);

  const refreshStatus = useCallback(async () => {
    const cameraId = store.currentCamera?.camera_id;
    if (!cameraId) return;

    try {
      const status = await api.getCameraStatus(cameraId);
      store.setCameraStatus(status);
      store.setIsConnected(status.connected);
      store.setIsCapturing(status.is_capturing);
    } catch (error: any) {
      // Silent fail for background updates
      console.error('Failed to refresh status:', error);
    }
  }, [api, store]);

  return {
    discoverCameras,
    connectCamera,
    disconnectCamera,
    startCapture,
    stopCapture,
    pauseCapture,
    snapImage,
    updateExposure,
    updateGain,
    updateWhiteBalance,
    setOnceWhiteBalance,
    updateImageProcessing,
    updateTrigger,
    softwareTrigger,
    refreshStatus,
  };
}
