// Camera API Types

export interface CameraInfo {
  camera_id: number;
  product_series: string;
  product_name: string;
  friendly_name: string;
  sensor_type: string;
  port_type: string;
  serial_number: string;
  instance: number;
}

export interface CameraStatus {
  camera_id: number;
  connected: boolean;
  reconnect_count: number;
  is_capturing: boolean;
  state: string;
}

export interface CameraCapability {
  mono_sensor: boolean;
  auto_exposure: boolean;
  auto_wb: boolean;
  hardware_isp: boolean;
  output_io_count: number;
  input_io_count: number;
  resolution_range: {
    width_min: number;
    width_max: number;
    height_min: number;
    height_max: number;
  };
}

export interface ResolutionConfig {
  width: number;
  height: number;
  offset_x?: number;
  offset_y?: number;
}

export interface Resolution {
  index: number;
  description: string;
  width: number;
  height: number;
  offset_x: number;
  offset_y: number;
  fov_width: number;
  fov_height: number;
}

export interface ExposureConfig {
  auto_exposure: boolean;
  exposure_time?: number;
  analog_gain?: number;
  ae_target?: number;
}

export interface ExposureInfo {
  auto_exposure: boolean;
  exposure_time: number;
  analog_gain: number;
}

export interface ExposureRange {
  min_exposure_time: number;
  max_exposure_time: number;
}

export interface GainConfig {
  r_gain: number;
  g_gain: number;
  b_gain: number;
}

export interface WhiteBalanceConfig {
  auto_wb: boolean;
  r_gain?: number;
  g_gain?: number;
  b_gain?: number;
  color_temp_preset?: number;
}

export interface WhiteBalanceInfo {
  auto_wb: boolean;
  r_gain: number;
  g_gain: number;
  b_gain: number;
}

export interface TriggerConfig {
  trigger_mode: number;
  trigger_delay?: number;
  trigger_count?: number;
  ext_trig_type?: number;
}

export interface TriggerInfo {
  trigger_mode: number;
  trigger_delay: number;
  trigger_count: number;
}

export interface IOConfig {
  io_index: number;
  mode: number;
  state?: number;
}

export interface IOState {
  io_index: number;
  state: number;
}

export interface ImageProcessingConfig {
  gamma?: number;
  contrast?: number;
  saturation?: number;
  sharpness?: number;
  monochrome?: boolean;
  inverse?: boolean;
  noise_filter?: boolean;
}

export interface ImageProcessingInfo {
  gamma: number;
  contrast: number;
  saturation: number;
  sharpness: number;
  monochrome: boolean;
  inverse: boolean;
  noise_filter: boolean;
}

export interface NetworkConfig {
  ip_address: string;
  subnet_mask: string;
  gateway: string;
  persistent?: boolean;
}

export interface NetworkInfo {
  ip_address: string;
  subnet_mask: string;
  gateway: string;
  mac_address: string;
}

export interface CameraStatistics {
  total_frames: number;
  captured_frames: number;
  lost_frames: number;
  loss_rate: number;
}

export interface FrameData {
  camera_id: number;
  timestamp: string;
  width: number;
  height: number;
  media_type: number;
  is_mono: boolean;
  image?: string; // base64 encoded
}

export interface StreamFrame {
  timestamp: string;
  width: number;
  height: number;
  image: string; // base64 encoded JPEG
}

export interface APIInfo {
  name: string;
  version: string;
  sdk_version: string;
  mqtt_available: boolean;
  mqtt_connected: boolean;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  active_cameras: number;
}

export interface MQTTConfig {
  broker: string;
  port: number;
  topic_prefix: string;
}

export interface MQTTStatus {
  available: boolean;
  connected: boolean;
  config: {
    broker: string;
    port: number;
    topic_prefix: string;
  };
}

// Trigger modes
export enum TriggerMode {
  Continuous = 0,
  Software = 1,
  Hardware = 2,
}

// IO modes
export enum IOMode {
  TrigInput = 0,
  StrobeOutput = 1,
  GPInput = 2,
  GPOutput = 3,
  PWMOutput = 4,
}

// Image formats
export enum ImageFormat {
  JPEG = 'jpeg',
  PNG = 'png',
}

// Response types
export interface APIResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
}

export interface ErrorResponse {
  detail: string;
}
