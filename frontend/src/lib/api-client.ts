import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  CameraInfo,
  CameraStatus,
  CameraCapability,
  ResolutionConfig,
  Resolution,
  ExposureConfig,
  ExposureInfo,
  ExposureRange,
  GainConfig,
  WhiteBalanceConfig,
  WhiteBalanceInfo,
  TriggerConfig,
  TriggerInfo,
  IOConfig,
  IOState,
  ImageProcessingConfig,
  ImageProcessingInfo,
  NetworkConfig,
  NetworkInfo,
  CameraStatistics,
  FrameData,
  APIInfo,
  HealthStatus,
  MQTTConfig,
  MQTTStatus,
  ErrorResponse,
} from '@/types/camera';

export class CameraAPIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        const message = error.response?.data?.detail || error.message;
        throw new Error(message);
      }
    );
  }

  // System & Discovery
  async getInfo(): Promise<APIInfo> {
    const { data } = await this.client.get<APIInfo>('/');
    return data;
  }

  async getHealth(): Promise<HealthStatus> {
    const { data } = await this.client.get<HealthStatus>('/health');
    return data;
  }

  async discoverCameras(): Promise<CameraInfo[]> {
    const { data } = await this.client.get<CameraInfo[]>('/cameras/discover');
    return data;
  }

  async discoverGigECameras(ipList?: string[]): Promise<CameraInfo[]> {
    const params = ipList ? { ip_list: ipList } : {};
    const { data } = await this.client.get<CameraInfo[]>('/cameras/discover/gige', { params });
    return data;
  }

  // Camera Management
  async connectCamera(cameraIndex: number): Promise<CameraInfo> {
    const { data } = await this.client.post<CameraInfo>(`/cameras/${cameraIndex}/connect`);
    return data;
  }

  async disconnectCamera(cameraId: number): Promise<{ status: string; camera_id: number }> {
    const { data } = await this.client.post(`/cameras/${cameraId}/disconnect`);
    return data;
  }

  async reconnectCamera(cameraId: number): Promise<{ status: string; camera_id: number }> {
    const { data } = await this.client.post(`/cameras/${cameraId}/reconnect`);
    return data;
  }

  async getCameraStatus(cameraId: number): Promise<CameraStatus> {
    const { data } = await this.client.get<CameraStatus>(`/cameras/${cameraId}/status`);
    return data;
  }

  async getCameraInfo(cameraId: number): Promise<any> {
    const { data } = await this.client.get(`/cameras/${cameraId}/info`);
    return data;
  }

  async getCameraCapability(cameraId: number): Promise<CameraCapability> {
    const { data } = await this.client.get<CameraCapability>(`/cameras/${cameraId}/capability`);
    return data;
  }

  // Image Capture & Streaming
  async startCapture(cameraId: number): Promise<{ status: string; camera_id: number }> {
    const { data } = await this.client.post(`/cameras/${cameraId}/start`);
    return data;
  }

  async stopCapture(cameraId: number): Promise<{ status: string; camera_id: number }> {
    const { data } = await this.client.post(`/cameras/${cameraId}/stop`);
    return data;
  }

  async pauseCapture(cameraId: number): Promise<{ status: string; camera_id: number }> {
    const { data } = await this.client.post(`/cameras/${cameraId}/pause`);
    return data;
  }

  async snapImage(cameraId: number, format: string = 'jpeg', timeout: number = 1000): Promise<Blob> {
    const { data } = await this.client.get(`/cameras/${cameraId}/snap`, {
      params: { format, timeout },
      responseType: 'blob',
    });
    return data;
  }

  async getFrame(cameraId: number, timeout: number = 1000, encoding: string = 'base64'): Promise<FrameData> {
    const { data } = await this.client.get<FrameData>(`/cameras/${cameraId}/frame`, {
      params: { timeout, encoding },
    });
    return data;
  }

  getStreamURL(cameraId: number, baseURL?: string): string {
    const wsURL = (baseURL || this.client.defaults.baseURL || '').replace(/^http/, 'ws');
    return `${wsURL}/cameras/${cameraId}/stream`;
  }

  // Resolution & Format
  async getResolution(cameraId: number): Promise<Resolution> {
    const { data } = await this.client.get<Resolution>(`/cameras/${cameraId}/resolution`);
    return data;
  }

  async setResolution(cameraId: number, config: ResolutionConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/resolution`, config);
    return data;
  }

  async getMediaType(cameraId: number): Promise<{ media_type: number }> {
    const { data } = await this.client.get(`/cameras/${cameraId}/media-type`);
    return data;
  }

  async setMediaType(cameraId: number, mediaType: number): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/media-type`, null, {
      params: { media_type: mediaType },
    });
    return data;
  }

  // Exposure Control
  async getExposure(cameraId: number): Promise<ExposureInfo> {
    const { data } = await this.client.get<ExposureInfo>(`/cameras/${cameraId}/exposure`);
    return data;
  }

  async setExposure(cameraId: number, config: ExposureConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/exposure`, config);
    return data;
  }

  async getExposureRange(cameraId: number): Promise<ExposureRange> {
    const { data } = await this.client.get<ExposureRange>(`/cameras/${cameraId}/exposure/range`);
    return data;
  }

  // Gain Control
  async getGain(cameraId: number): Promise<GainConfig> {
    const { data } = await this.client.get<GainConfig>(`/cameras/${cameraId}/gain`);
    return data;
  }

  async setGain(cameraId: number, config: GainConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/gain`, config);
    return data;
  }

  // White Balance
  async getWhiteBalance(cameraId: number): Promise<WhiteBalanceInfo> {
    const { data } = await this.client.get<WhiteBalanceInfo>(`/cameras/${cameraId}/white-balance`);
    return data;
  }

  async setWhiteBalance(cameraId: number, config: WhiteBalanceConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/white-balance`, config);
    return data;
  }

  async setOnceWhiteBalance(cameraId: number): Promise<any> {
    const { data } = await this.client.post(`/cameras/${cameraId}/white-balance/once`);
    return data;
  }

  // Image Processing
  async getImageProcessing(cameraId: number): Promise<ImageProcessingInfo> {
    const { data } = await this.client.get<ImageProcessingInfo>(`/cameras/${cameraId}/image-processing`);
    return data;
  }

  async setImageProcessing(cameraId: number, config: ImageProcessingConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/image-processing`, config);
    return data;
  }

  // Trigger Control
  async getTrigger(cameraId: number): Promise<TriggerInfo> {
    const { data } = await this.client.get<TriggerInfo>(`/cameras/${cameraId}/trigger`);
    return data;
  }

  async setTrigger(cameraId: number, config: TriggerConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/trigger`, config);
    return data;
  }

  async softwareTrigger(cameraId: number): Promise<any> {
    const { data } = await this.client.post(`/cameras/${cameraId}/trigger/software`);
    return data;
  }

  // I/O Control
  async getIOState(cameraId: number, ioIndex: number): Promise<IOState> {
    const { data } = await this.client.get<IOState>(`/cameras/${cameraId}/io/${ioIndex}`);
    return data;
  }

  async setIOConfig(cameraId: number, ioIndex: number, config: IOConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/io/${ioIndex}`, config);
    return data;
  }

  // Network Configuration
  async getNetworkConfig(cameraId: number): Promise<NetworkInfo> {
    const { data } = await this.client.get<NetworkInfo>(`/cameras/${cameraId}/network`);
    return data;
  }

  async setNetworkConfig(cameraId: number, config: NetworkConfig): Promise<any> {
    const { data } = await this.client.put(`/cameras/${cameraId}/network`, config);
    return data;
  }

  // Statistics
  async getStatistics(cameraId: number): Promise<CameraStatistics> {
    const { data } = await this.client.get<CameraStatistics>(`/cameras/${cameraId}/statistics`);
    return data;
  }

  // Parameters
  async saveParameters(cameraId: number, team: number = 0): Promise<any> {
    const { data } = await this.client.post(`/cameras/${cameraId}/parameters/save`, null, {
      params: { team },
    });
    return data;
  }

  async loadParameters(cameraId: number, team: number = 0): Promise<any> {
    const { data } = await this.client.post(`/cameras/${cameraId}/parameters/load`, null, {
      params: { team },
    });
    return data;
  }

  // MQTT
  async connectMQTT(config: MQTTConfig): Promise<any> {
    const { data } = await this.client.post('/mqtt/connect', config);
    return data;
  }

  async getMQTTStatus(): Promise<MQTTStatus> {
    const { data } = await this.client.get<MQTTStatus>('/mqtt/status');
    return data;
  }
}

// Singleton instance
let apiClientInstance: CameraAPIClient | null = null;

export function getAPIClient(baseURL?: string): CameraAPIClient {
  if (!apiClientInstance || baseURL) {
    apiClientInstance = new CameraAPIClient(
      baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    );
  }
  return apiClientInstance;
}

export default getAPIClient;
