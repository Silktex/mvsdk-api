import { create } from 'zustand';
import type { CameraInfo, CameraStatus, CameraCapability } from '@/types/camera';

interface CameraState {
  // Available cameras
  availableCameras: CameraInfo[];
  setAvailableCameras: (cameras: CameraInfo[]) => void;

  // Current camera
  currentCamera: CameraInfo | null;
  setCurrentCamera: (camera: CameraInfo | null) => void;

  // Camera status
  cameraStatus: CameraStatus | null;
  setCameraStatus: (status: CameraStatus | null) => void;

  // Camera capability
  cameraCapability: CameraCapability | null;
  setCameraCapability: (capability: CameraCapability | null) => void;

  // Connection state
  isConnected: boolean;
  setIsConnected: (connected: boolean) => void;

  // Capture state
  isCapturing: boolean;
  setIsCapturing: (capturing: boolean) => void;

  // Streaming state
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;

  // API URL
  apiURL: string;
  setAPIURL: (url: string) => void;

  // Loading states
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Error state
  error: string | null;
  setError: (error: string | null) => void;

  // FPS counter
  fps: number;
  setFPS: (fps: number) => void;

  // Reset state
  reset: () => void;
}

const useCameraStore = create<CameraState>((set) => ({
  // Initial state
  availableCameras: [],
  currentCamera: null,
  cameraStatus: null,
  cameraCapability: null,
  isConnected: false,
  isCapturing: false,
  isStreaming: false,
  apiURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  isLoading: false,
  error: null,
  fps: 0,

  // Setters
  setAvailableCameras: (cameras) => set({ availableCameras: cameras }),
  setCurrentCamera: (camera) => set({ currentCamera: camera }),
  setCameraStatus: (status) => set({ cameraStatus: status }),
  setCameraCapability: (capability) => set({ cameraCapability: capability }),
  setIsConnected: (connected) => set({ isConnected: connected }),
  setIsCapturing: (capturing) => set({ isCapturing: capturing }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setAPIURL: (url) => set({ apiURL: url }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setFPS: (fps) => set({ fps }),

  // Reset
  reset: () =>
    set({
      currentCamera: null,
      cameraStatus: null,
      cameraCapability: null,
      isConnected: false,
      isCapturing: false,
      isStreaming: false,
      isLoading: false,
      error: null,
      fps: 0,
    }),
}));

export default useCameraStore;
