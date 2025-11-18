#!/usr/bin/env python3
# coding=utf-8
"""
MindVision 47MP GigE Vision Camera REST API
Comprehensive API supporting REST, WebSocket streaming, and MQTT events
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
import mvsdk
import numpy as np
import cv2
import base64
import json
import asyncio
import threading
import time
from datetime import datetime
from contextlib import asynccontextmanager
import logging

# MQTT support
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("paho-mqtt not installed. MQTT features will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Global state management
# =============================================================================

class CameraManager:
    """Manages camera instances and their state"""
    def __init__(self):
        self.cameras: Dict[int, dict] = {}  # camera_id -> {handle, info, state}
        self.lock = threading.Lock()
        self.frame_callbacks: Dict[int, list] = {}  # camera_id -> [callbacks]
        self.mqtt_client: Optional[mqtt.Client] = None
        self.mqtt_config = {
            "broker": "localhost",
            "port": 1883,
            "topic_prefix": "camera"
        }

    def init_mqtt(self, broker: str, port: int, topic_prefix: str = "camera"):
        """Initialize MQTT client"""
        if not MQTT_AVAILABLE:
            raise Exception("MQTT not available. Install paho-mqtt.")

        self.mqtt_config = {
            "broker": broker,
            "port": port,
            "topic_prefix": topic_prefix
        }

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

        try:
            self.mqtt_client.connect(broker, port, 60)
            self.mqtt_client.loop_start()
            logger.info(f"MQTT connected to {broker}:{port}")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            self.mqtt_client = None
            raise

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        logger.info(f"MQTT connected with result code {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT disconnected with result code {rc}")

    def publish_event(self, camera_id: int, event_type: str, data: dict):
        """Publish event to MQTT"""
        if self.mqtt_client and self.mqtt_client.is_connected():
            topic = f"{self.mqtt_config['topic_prefix']}/{camera_id}/{event_type}"
            payload = json.dumps({
                "timestamp": datetime.now().isoformat(),
                "camera_id": camera_id,
                "event": event_type,
                "data": data
            })
            self.mqtt_client.publish(topic, payload)

    def add_camera(self, handle: int, dev_info: mvsdk.tSdkCameraDevInfo) -> int:
        """Add a camera to the manager"""
        with self.lock:
            camera_id = handle
            self.cameras[camera_id] = {
                "handle": handle,
                "info": dev_info,
                "state": "initialized",
                "is_capturing": False,
                "frame_buffer": None,
                "capability": None
            }
            self.frame_callbacks[camera_id] = []
            return camera_id

    def get_camera(self, camera_id: int) -> dict:
        """Get camera by ID"""
        if camera_id not in self.cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        return self.cameras[camera_id]

    def remove_camera(self, camera_id: int):
        """Remove camera from manager"""
        with self.lock:
            if camera_id in self.cameras:
                del self.cameras[camera_id]
            if camera_id in self.frame_callbacks:
                del self.frame_callbacks[camera_id]

camera_manager = CameraManager()

# =============================================================================
# Pydantic Models for API
# =============================================================================

class CameraInfo(BaseModel):
    camera_id: int
    product_series: str
    product_name: str
    friendly_name: str
    sensor_type: str
    port_type: str
    serial_number: str
    instance: int

class ResolutionConfig(BaseModel):
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    offset_x: int = Field(default=0, ge=0)
    offset_y: int = Field(default=0, ge=0)

class ExposureConfig(BaseModel):
    auto_exposure: bool
    exposure_time: Optional[float] = Field(None, ge=0, description="Exposure time in microseconds")
    analog_gain: Optional[int] = Field(None, ge=0)
    ae_target: Optional[int] = Field(None, ge=0, le=255)

class GainConfig(BaseModel):
    r_gain: int = Field(..., ge=0)
    g_gain: int = Field(..., ge=0)
    b_gain: int = Field(..., ge=0)

class WhiteBalanceConfig(BaseModel):
    auto_wb: bool
    r_gain: Optional[int] = None
    g_gain: Optional[int] = None
    b_gain: Optional[int] = None
    color_temp_preset: Optional[int] = None

class TriggerConfig(BaseModel):
    trigger_mode: int = Field(..., ge=0, description="0=continuous, 1=software, 2=hardware")
    trigger_delay: Optional[int] = Field(None, ge=0, description="Delay in microseconds")
    trigger_count: Optional[int] = Field(None, ge=1)
    ext_trig_type: Optional[int] = Field(None, ge=0, le=4, description="External trigger signal type")

class IOConfig(BaseModel):
    io_index: int = Field(..., ge=0)
    mode: int = Field(..., description="IO mode: 0=trig_input, 1=strobe_output, 2=gp_input, 3=gp_output, 4=pwm_output")
    state: Optional[int] = Field(None, description="Output state for GPIO")

class ImageProcessingConfig(BaseModel):
    gamma: Optional[int] = None
    contrast: Optional[int] = None
    saturation: Optional[int] = None
    sharpness: Optional[int] = None
    monochrome: Optional[bool] = None
    inverse: Optional[bool] = None
    noise_filter: Optional[bool] = None

class NetworkConfig(BaseModel):
    ip_address: str
    subnet_mask: str
    gateway: str
    persistent: bool = True

class MQTTConfig(BaseModel):
    broker: str = "localhost"
    port: int = 1883
    topic_prefix: str = "camera"

# =============================================================================
# Lifespan events
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Camera API starting up...")
    # Initialize SDK
    try:
        mvsdk.CameraSdkInit(1)  # 1 for English
        logger.info("Camera SDK initialized")
    except Exception as e:
        logger.warning(f"SDK init warning: {e}")

    yield

    # Cleanup
    logger.info("Camera API shutting down...")
    for camera_id in list(camera_manager.cameras.keys()):
        try:
            handle = camera_manager.cameras[camera_id]["handle"]
            mvsdk.CameraUnInit(handle)
            logger.info(f"Camera {camera_id} uninitialized")
        except Exception as e:
            logger.error(f"Error uninitializing camera {camera_id}: {e}")

    if camera_manager.mqtt_client:
        camera_manager.mqtt_client.loop_stop()
        camera_manager.mqtt_client.disconnect()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="MindVision 47MP Camera API",
    description="Comprehensive REST API for MindVision GigE Vision camera control",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# System and Discovery Endpoints
# =============================================================================

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "MindVision 47MP Camera API",
        "version": "1.0.0",
        "sdk_version": mvsdk.CameraSdkGetVersionString(),
        "mqtt_available": MQTT_AVAILABLE,
        "mqtt_connected": camera_manager.mqtt_client.is_connected() if camera_manager.mqtt_client else False
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_cameras": len(camera_manager.cameras)
    }

@app.get("/cameras/discover", response_model=List[CameraInfo])
async def discover_cameras():
    """Discover available cameras on the network"""
    try:
        devices = mvsdk.CameraEnumerateDevice()
        camera_list = []
        for dev in devices:
            camera_list.append(CameraInfo(
                camera_id=dev.uInstance,
                product_series=dev.GetProductSeries(),
                product_name=dev.GetProductName(),
                friendly_name=dev.GetFriendlyName(),
                sensor_type=dev.GetSensorType(),
                port_type=dev.GetPortType(),
                serial_number=dev.GetSn(),
                instance=dev.uInstance
            ))
        return camera_list
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {e.message}")

@app.get("/cameras/discover/gige")
async def discover_gige_cameras(ip_list: Optional[List[str]] = Query(None)):
    """Discover GigE Vision cameras on network"""
    try:
        devices = mvsdk.CameraGigeEnumerateDevice(ip_list if ip_list else None)
        camera_list = []
        for dev in devices:
            camera_list.append(CameraInfo(
                camera_id=dev.uInstance,
                product_series=dev.GetProductSeries(),
                product_name=dev.GetProductName(),
                friendly_name=dev.GetFriendlyName(),
                sensor_type=dev.GetSensorType(),
                port_type=dev.GetPortType(),
                serial_number=dev.GetSn(),
                instance=dev.uInstance
            ))
        return camera_list
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"GigE discovery failed: {e.message}")

# =============================================================================
# Camera Connection Management
# =============================================================================

@app.post("/cameras/{camera_index}/connect", response_model=CameraInfo)
async def connect_camera(camera_index: int):
    """Connect to a camera by index"""
    try:
        devices = mvsdk.CameraEnumerateDevice()
        if camera_index >= len(devices):
            raise HTTPException(status_code=404, detail=f"Camera index {camera_index} not found")

        dev_info = devices[camera_index]
        handle = mvsdk.CameraInit(dev_info, -1, -1)

        camera_id = camera_manager.add_camera(handle, dev_info)

        # Get capability
        cap = mvsdk.CameraGetCapability(handle)
        camera_manager.cameras[camera_id]["capability"] = cap

        # Allocate frame buffer
        mono = cap.sIspCapacity.bMonoSensor != 0
        buffer_size = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if mono else 3)
        frame_buffer = mvsdk.CameraAlignMalloc(buffer_size, 16)
        camera_manager.cameras[camera_id]["frame_buffer"] = frame_buffer
        camera_manager.cameras[camera_id]["mono"] = mono

        # Set default output format
        if mono:
            mvsdk.CameraSetIspOutFormat(handle, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(handle, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

        camera_manager.publish_event(camera_id, "connected", {"device": dev_info.GetFriendlyName()})

        return CameraInfo(
            camera_id=camera_id,
            product_series=dev_info.GetProductSeries(),
            product_name=dev_info.GetProductName(),
            friendly_name=dev_info.GetFriendlyName(),
            sensor_type=dev_info.GetSensorType(),
            port_type=dev_info.GetPortType(),
            serial_number=dev_info.GetSn(),
            instance=dev_info.uInstance
        )
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Camera connection failed: {e.message}")

@app.post("/cameras/{camera_id}/disconnect")
async def disconnect_camera(camera_id: int):
    """Disconnect from camera"""
    camera = camera_manager.get_camera(camera_id)
    try:
        # Stop capture if running
        if camera["is_capturing"]:
            mvsdk.CameraStop(camera["handle"])

        # Free frame buffer
        if camera["frame_buffer"]:
            mvsdk.CameraAlignFree(camera["frame_buffer"])

        # Uninitialize camera
        mvsdk.CameraUnInit(camera["handle"])

        camera_manager.remove_camera(camera_id)
        camera_manager.publish_event(camera_id, "disconnected", {})

        return {"status": "disconnected", "camera_id": camera_id}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {e.message}")

@app.post("/cameras/{camera_id}/reconnect")
async def reconnect_camera(camera_id: int):
    """Reconnect to camera"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraReConnect(camera["handle"])
        camera_manager.publish_event(camera_id, "reconnected", {})
        return {"status": "reconnected", "camera_id": camera_id}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Reconnect failed: {e.message}")

@app.get("/cameras/{camera_id}/status")
async def get_camera_status(camera_id: int):
    """Get camera connection status"""
    camera = camera_manager.get_camera(camera_id)
    try:
        test_result = mvsdk.CameraConnectTest(camera["handle"])
        reconnect_count = mvsdk.CameraGetReConnectCounts(camera["handle"])

        return {
            "camera_id": camera_id,
            "connected": test_result == mvsdk.CAMERA_STATUS_SUCCESS,
            "reconnect_count": reconnect_count,
            "is_capturing": camera["is_capturing"],
            "state": camera["state"]
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {e.message}")

# =============================================================================
# Image Capture and Streaming
# =============================================================================

@app.post("/cameras/{camera_id}/start")
async def start_capture(camera_id: int):
    """Start continuous image capture"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraPlay(camera["handle"])
        camera["is_capturing"] = True
        camera["state"] = "capturing"
        camera_manager.publish_event(camera_id, "capture_started", {})
        return {"status": "capturing", "camera_id": camera_id}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Start capture failed: {e.message}")

@app.post("/cameras/{camera_id}/stop")
async def stop_capture(camera_id: int):
    """Stop image capture"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraStop(camera["handle"])
        camera["is_capturing"] = False
        camera["state"] = "stopped"
        camera_manager.publish_event(camera_id, "capture_stopped", {})
        return {"status": "stopped", "camera_id": camera_id}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Stop capture failed: {e.message}")

@app.post("/cameras/{camera_id}/pause")
async def pause_capture(camera_id: int):
    """Pause image capture"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraPause(camera["handle"])
        camera["state"] = "paused"
        camera_manager.publish_event(camera_id, "capture_paused", {})
        return {"status": "paused", "camera_id": camera_id}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Pause failed: {e.message}")

@app.get("/cameras/{camera_id}/snap")
async def snap_image(camera_id: int, timeout: int = 1000, format: str = "jpeg"):
    """Capture a single image"""
    camera = camera_manager.get_camera(camera_id)
    try:
        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(camera["handle"], timeout)
        mvsdk.CameraImageProcess(camera["handle"], pRawData, camera["frame_buffer"], FrameHead)
        mvsdk.CameraReleaseImageBuffer(camera["handle"], pRawData)

        # Convert to numpy array
        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(camera["frame_buffer"])
        frame = np.frombuffer(frame_data, dtype=np.uint8)

        is_mono = FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8
        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if is_mono else 3))

        # Encode image
        if format.lower() == "jpeg":
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            media_type = "image/jpeg"
        elif format.lower() == "png":
            ret, buffer = cv2.imencode('.png', frame)
            media_type = "image/png"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        if not ret:
            raise HTTPException(status_code=500, detail="Image encoding failed")

        camera_manager.publish_event(camera_id, "image_snapped", {"format": format})

        return StreamingResponse(iter([buffer.tobytes()]), media_type=media_type)
    except mvsdk.CameraException as e:
        if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
            raise HTTPException(status_code=408, detail="Capture timeout")
        raise HTTPException(status_code=500, detail=f"Snap failed: {e.message}")

@app.get("/cameras/{camera_id}/frame")
async def get_frame(camera_id: int, timeout: int = 1000, encoding: str = "base64"):
    """Get current frame as JSON (base64 or raw metadata)"""
    camera = camera_manager.get_camera(camera_id)
    try:
        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(camera["handle"], timeout)
        mvsdk.CameraImageProcess(camera["handle"], pRawData, camera["frame_buffer"], FrameHead)
        mvsdk.CameraReleaseImageBuffer(camera["handle"], pRawData)

        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(camera["frame_buffer"])
        frame = np.frombuffer(frame_data, dtype=np.uint8)

        is_mono = FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8
        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if is_mono else 3))

        response = {
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "width": FrameHead.iWidth,
            "height": FrameHead.iHeight,
            "media_type": FrameHead.uiMediaType,
            "is_mono": is_mono
        }

        if encoding == "base64":
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                response["image"] = base64.b64encode(buffer).decode('utf-8')
                response["encoding"] = "base64"

        return response
    except mvsdk.CameraException as e:
        if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
            raise HTTPException(status_code=408, detail="Frame timeout")
        raise HTTPException(status_code=500, detail=f"Get frame failed: {e.message}")

@app.websocket("/cameras/{camera_id}/stream")
async def stream_video(websocket: WebSocket, camera_id: int):
    """WebSocket endpoint for real-time video streaming"""
    await websocket.accept()

    camera = camera_manager.get_camera(camera_id)

    try:
        logger.info(f"WebSocket streaming started for camera {camera_id}")

        while True:
            try:
                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(camera["handle"], 200)
                mvsdk.CameraImageProcess(camera["handle"], pRawData, camera["frame_buffer"], FrameHead)
                mvsdk.CameraReleaseImageBuffer(camera["handle"], pRawData)

                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(camera["frame_buffer"])
                frame = np.frombuffer(frame_data, dtype=np.uint8)

                is_mono = FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if is_mono else 3))

                # Encode as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    # Send as base64
                    await websocket.send_json({
                        "timestamp": datetime.now().isoformat(),
                        "width": FrameHead.iWidth,
                        "height": FrameHead.iHeight,
                        "image": base64.b64encode(buffer).decode('utf-8')
                    })

                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming

            except mvsdk.CameraException as e:
                if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                    continue
                logger.error(f"Streaming error: {e.message}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# =============================================================================
# Camera Configuration - Resolution and Format
# =============================================================================

@app.get("/cameras/{camera_id}/resolution")
async def get_resolution(camera_id: int):
    """Get current image resolution"""
    camera = camera_manager.get_camera(camera_id)
    try:
        res = mvsdk.CameraGetImageResolution(camera["handle"])
        return {
            "index": res.iIndex,
            "description": res.GetDescription(),
            "width": res.iWidth,
            "height": res.iHeight,
            "offset_x": res.iHOffsetFOV,
            "offset_y": res.iVOffsetFOV,
            "fov_width": res.iWidthFOV,
            "fov_height": res.iHeightFOV
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get resolution failed: {e.message}")

@app.put("/cameras/{camera_id}/resolution")
async def set_resolution(camera_id: int, config: ResolutionConfig):
    """Set image resolution"""
    camera = camera_manager.get_camera(camera_id)
    try:
        # Get current resolution to modify
        res = mvsdk.CameraGetImageResolution(camera["handle"])
        res.iWidth = config.width
        res.iHeight = config.height
        res.iHOffsetFOV = config.offset_x
        res.iVOffsetFOV = config.offset_y
        res.iIndex = 0xFF  # Custom resolution

        mvsdk.CameraSetImageResolution(camera["handle"], res)
        camera_manager.publish_event(camera_id, "resolution_changed", {
            "width": config.width,
            "height": config.height
        })
        return {"status": "success", "resolution": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set resolution failed: {e.message}")

@app.get("/cameras/{camera_id}/media-type")
async def get_media_type(camera_id: int):
    """Get current media type"""
    camera = camera_manager.get_camera(camera_id)
    try:
        media_type = mvsdk.CameraGetMediaType(camera["handle"])
        return {"media_type": media_type}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get media type failed: {e.message}")

@app.put("/cameras/{camera_id}/media-type")
async def set_media_type(camera_id: int, media_type: int):
    """Set media type"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetMediaType(camera["handle"], media_type)
        camera_manager.publish_event(camera_id, "media_type_changed", {"media_type": media_type})
        return {"status": "success", "media_type": media_type}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set media type failed: {e.message}")

# =============================================================================
# Camera Configuration - Exposure Control
# =============================================================================

@app.get("/cameras/{camera_id}/exposure")
async def get_exposure(camera_id: int):
    """Get exposure settings"""
    camera = camera_manager.get_camera(camera_id)
    try:
        ae_state = mvsdk.CameraGetAeState(camera["handle"])
        exposure_time = mvsdk.CameraGetExposureTime(camera["handle"])
        analog_gain = mvsdk.CameraGetAnalogGain(camera["handle"])

        return {
            "auto_exposure": ae_state == 1,
            "exposure_time": exposure_time,
            "analog_gain": analog_gain
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get exposure failed: {e.message}")

@app.put("/cameras/{camera_id}/exposure")
async def set_exposure(camera_id: int, config: ExposureConfig):
    """Set exposure settings"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetAeState(camera["handle"], 1 if config.auto_exposure else 0)

        if not config.auto_exposure:
            if config.exposure_time is not None:
                mvsdk.CameraSetExposureTime(camera["handle"], config.exposure_time)
            if config.analog_gain is not None:
                mvsdk.CameraSetAnalogGain(camera["handle"], config.analog_gain)

        if config.ae_target is not None:
            mvsdk.CameraSetAeTarget(camera["handle"], config.ae_target)

        camera_manager.publish_event(camera_id, "exposure_changed", config.dict())
        return {"status": "success", "config": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set exposure failed: {e.message}")

@app.get("/cameras/{camera_id}/exposure/range")
async def get_exposure_range(camera_id: int):
    """Get exposure time range"""
    camera = camera_manager.get_camera(camera_id)
    try:
        min_time, max_time = mvsdk.CameraGetExposureTimeRange(camera["handle"])
        return {
            "min_exposure_time": min_time,
            "max_exposure_time": max_time
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get exposure range failed: {e.message}")

# =============================================================================
# Camera Configuration - Gain Control
# =============================================================================

@app.get("/cameras/{camera_id}/gain")
async def get_gain(camera_id: int):
    """Get RGB gain values"""
    camera = camera_manager.get_camera(camera_id)
    try:
        r, g, b = mvsdk.CameraGetGain(camera["handle"])
        return {"r_gain": r, "g_gain": g, "b_gain": b}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get gain failed: {e.message}")

@app.put("/cameras/{camera_id}/gain")
async def set_gain(camera_id: int, config: GainConfig):
    """Set RGB gain values"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetGain(camera["handle"], config.r_gain, config.g_gain, config.b_gain)
        camera_manager.publish_event(camera_id, "gain_changed", config.dict())
        return {"status": "success", "gain": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set gain failed: {e.message}")

# =============================================================================
# Camera Configuration - White Balance
# =============================================================================

@app.get("/cameras/{camera_id}/white-balance")
async def get_white_balance(camera_id: int):
    """Get white balance settings"""
    camera = camera_manager.get_camera(camera_id)
    try:
        wb_mode = mvsdk.CameraGetWbMode(camera["handle"])
        r, g, b = mvsdk.CameraGetUserClrTempGain(camera["handle"])

        return {
            "auto_wb": wb_mode == 1,
            "r_gain": r,
            "g_gain": g,
            "b_gain": b
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get white balance failed: {e.message}")

@app.put("/cameras/{camera_id}/white-balance")
async def set_white_balance(camera_id: int, config: WhiteBalanceConfig):
    """Set white balance settings"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetWbMode(camera["handle"], 1 if config.auto_wb else 0)

        if not config.auto_wb and config.r_gain and config.g_gain and config.b_gain:
            mvsdk.CameraSetUserClrTempGain(camera["handle"], config.r_gain, config.g_gain, config.b_gain)

        if config.color_temp_preset is not None:
            mvsdk.CameraSetPresetClrTemp(camera["handle"], config.color_temp_preset)

        camera_manager.publish_event(camera_id, "white_balance_changed", config.dict())
        return {"status": "success", "config": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set white balance failed: {e.message}")

@app.post("/cameras/{camera_id}/white-balance/once")
async def set_once_wb(camera_id: int):
    """Perform one-time white balance"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetOnceWB(camera["handle"])
        camera_manager.publish_event(camera_id, "white_balance_once", {})
        return {"status": "success"}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Once WB failed: {e.message}")

# =============================================================================
# Camera Configuration - Image Processing
# =============================================================================

@app.get("/cameras/{camera_id}/image-processing")
async def get_image_processing(camera_id: int):
    """Get image processing settings"""
    camera = camera_manager.get_camera(camera_id)
    try:
        gamma = mvsdk.CameraGetGamma(camera["handle"])
        contrast = mvsdk.CameraGetContrast(camera["handle"])
        saturation = mvsdk.CameraGetSaturation(camera["handle"])
        sharpness = mvsdk.CameraGetSharpness(camera["handle"])
        monochrome = mvsdk.CameraGetMonochrome(camera["handle"])
        inverse = mvsdk.CameraGetInverse(camera["handle"])
        noise_filter = mvsdk.CameraGetNoiseFilterState(camera["handle"])

        return {
            "gamma": gamma,
            "contrast": contrast,
            "saturation": saturation,
            "sharpness": sharpness,
            "monochrome": monochrome == 1,
            "inverse": inverse == 1,
            "noise_filter": noise_filter == 1
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get image processing failed: {e.message}")

@app.put("/cameras/{camera_id}/image-processing")
async def set_image_processing(camera_id: int, config: ImageProcessingConfig):
    """Set image processing settings"""
    camera = camera_manager.get_camera(camera_id)
    try:
        if config.gamma is not None:
            mvsdk.CameraSetGamma(camera["handle"], config.gamma)
        if config.contrast is not None:
            mvsdk.CameraSetContrast(camera["handle"], config.contrast)
        if config.saturation is not None:
            mvsdk.CameraSetSaturation(camera["handle"], config.saturation)
        if config.sharpness is not None:
            mvsdk.CameraSetSharpness(camera["handle"], config.sharpness)
        if config.monochrome is not None:
            mvsdk.CameraSetMonochrome(camera["handle"], 1 if config.monochrome else 0)
        if config.inverse is not None:
            mvsdk.CameraSetInverse(camera["handle"], 1 if config.inverse else 0)
        if config.noise_filter is not None:
            mvsdk.CameraSetNoiseFilter(camera["handle"], 1 if config.noise_filter else 0)

        camera_manager.publish_event(camera_id, "image_processing_changed", config.dict(exclude_none=True))
        return {"status": "success", "config": config.dict(exclude_none=True)}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set image processing failed: {e.message}")

# =============================================================================
# Trigger Control
# =============================================================================

@app.get("/cameras/{camera_id}/trigger")
async def get_trigger_config(camera_id: int):
    """Get trigger configuration"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mode = mvsdk.CameraGetTriggerMode(camera["handle"])
        delay = mvsdk.CameraGetTriggerDelayTime(camera["handle"])
        count = mvsdk.CameraGetTriggerCount(camera["handle"])

        return {
            "trigger_mode": mode,
            "trigger_delay": delay,
            "trigger_count": count
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get trigger config failed: {e.message}")

@app.put("/cameras/{camera_id}/trigger")
async def set_trigger_config(camera_id: int, config: TriggerConfig):
    """Set trigger configuration"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetTriggerMode(camera["handle"], config.trigger_mode)

        if config.trigger_delay is not None:
            mvsdk.CameraSetTriggerDelayTime(camera["handle"], config.trigger_delay)
        if config.trigger_count is not None:
            mvsdk.CameraSetTriggerCount(camera["handle"], config.trigger_count)
        if config.ext_trig_type is not None:
            mvsdk.CameraSetExtTrigSignalType(camera["handle"], config.ext_trig_type)

        camera_manager.publish_event(camera_id, "trigger_config_changed", config.dict())
        return {"status": "success", "config": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set trigger config failed: {e.message}")

@app.post("/cameras/{camera_id}/trigger/software")
async def software_trigger(camera_id: int):
    """Send software trigger"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSoftTrigger(camera["handle"])
        camera_manager.publish_event(camera_id, "software_trigger", {})
        return {"status": "triggered"}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Software trigger failed: {e.message}")

# =============================================================================
# I/O Control
# =============================================================================

@app.get("/cameras/{camera_id}/io/{io_index}")
async def get_io_state(camera_id: int, io_index: int):
    """Get I/O state"""
    camera = camera_manager.get_camera(camera_id)
    try:
        state = mvsdk.CameraGetIOStateEx(camera["handle"], io_index)
        return {"io_index": io_index, "state": state}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get IO state failed: {e.message}")

@app.put("/cameras/{camera_id}/io/{io_index}")
async def set_io_config(camera_id: int, io_index: int, config: IOConfig):
    """Configure I/O pin"""
    camera = camera_manager.get_camera(camera_id)
    try:
        # Set mode
        if config.mode in [0, 2]:  # Input modes
            mvsdk.CameraSetInPutIOMode(camera["handle"], io_index, config.mode)
        else:  # Output modes
            mvsdk.CameraSetOutPutIOMode(camera["handle"], io_index, config.mode)

        # Set state for output
        if config.state is not None and config.mode in [1, 3]:
            mvsdk.CameraSetIOStateEx(camera["handle"], io_index, config.state)

        camera_manager.publish_event(camera_id, "io_config_changed", {
            "io_index": io_index,
            "mode": config.mode
        })
        return {"status": "success", "io_index": io_index, "config": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set IO config failed: {e.message}")

# =============================================================================
# GigE Network Configuration
# =============================================================================

@app.get("/cameras/{camera_id}/network")
async def get_network_config(camera_id: int):
    """Get GigE network configuration"""
    camera = camera_manager.get_camera(camera_id)
    try:
        dev_info = camera["info"]
        ip, subnet, gateway = mvsdk.CameraGigeGetIp(dev_info)
        mac = mvsdk.CameraGigeGetMac(dev_info)

        return {
            "ip_address": ip,
            "subnet_mask": subnet,
            "gateway": gateway,
            "mac_address": mac
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get network config failed: {e.message}")

@app.put("/cameras/{camera_id}/network")
async def set_network_config(camera_id: int, config: NetworkConfig):
    """Set GigE network configuration"""
    camera = camera_manager.get_camera(camera_id)
    try:
        dev_info = camera["info"]
        mvsdk.CameraGigeSetIp(
            dev_info,
            config.ip_address,
            config.subnet_mask,
            config.gateway,
            config.persistent
        )

        camera_manager.publish_event(camera_id, "network_config_changed", config.dict())
        return {"status": "success", "config": config.dict()}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set network config failed: {e.message}")

# =============================================================================
# Statistics and Information
# =============================================================================

@app.get("/cameras/{camera_id}/info")
async def get_camera_info(camera_id: int):
    """Get detailed camera information"""
    camera = camera_manager.get_camera(camera_id)
    try:
        info = mvsdk.CameraGetInformation(camera["handle"])
        fw_version = mvsdk.CameraGetFirmwareVersion(camera["handle"])

        return {
            "camera_id": camera_id,
            "firmware_version": fw_version,
            "info": info
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get camera info failed: {e.message}")

@app.get("/cameras/{camera_id}/statistics")
async def get_statistics(camera_id: int):
    """Get frame statistics"""
    camera = camera_manager.get_camera(camera_id)
    try:
        stats = mvsdk.CameraGetFrameStatistic(camera["handle"])
        return {
            "total_frames": stats.iTotal,
            "captured_frames": stats.iCapture,
            "lost_frames": stats.iLost,
            "loss_rate": stats.iLost / stats.iTotal if stats.iTotal > 0 else 0
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get statistics failed: {e.message}")

@app.get("/cameras/{camera_id}/capability")
async def get_capability(camera_id: int):
    """Get camera capability"""
    camera = camera_manager.get_camera(camera_id)
    cap = camera.get("capability")
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not available")

    return {
        "mono_sensor": cap.sIspCapacity.bMonoSensor == 1,
        "auto_exposure": cap.sIspCapacity.bAutoExposure == 1,
        "auto_wb": cap.sIspCapacity.bAutoWb == 1,
        "hardware_isp": cap.sIspCapacity.bDeviceIsp == 1,
        "output_io_count": cap.iOutputIoCounts,
        "input_io_count": cap.iInputIoCounts,
        "resolution_range": {
            "width_min": cap.sResolutionRange.iWidthMin,
            "width_max": cap.sResolutionRange.iWidthMax,
            "height_min": cap.sResolutionRange.iHeightMin,
            "height_max": cap.sResolutionRange.iHeightMax
        }
    }

# =============================================================================
# Parameter Management
# =============================================================================

@app.post("/cameras/{camera_id}/parameters/save")
async def save_parameters(camera_id: int, team: int = 0):
    """Save camera parameters to team"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSaveParameter(camera["handle"], team)
        camera_manager.publish_event(camera_id, "parameters_saved", {"team": team})
        return {"status": "saved", "team": team}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Save parameters failed: {e.message}")

@app.post("/cameras/{camera_id}/parameters/load")
async def load_parameters(camera_id: int, team: int = 0):
    """Load camera parameters from team"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraLoadParameter(camera["handle"], team)
        camera_manager.publish_event(camera_id, "parameters_loaded", {"team": team})
        return {"status": "loaded", "team": team}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Load parameters failed: {e.message}")

# =============================================================================
# Network Speed Testing
# =============================================================================

@app.get("/cameras/{camera_id}/network/speed-test")
async def network_speed_test(
    camera_id: int,
    duration: int = 10,
    background_tasks: BackgroundTasks = None
):
    """
    Run network speed test
    Tests actual throughput, FPS, and frame loss rate
    """
    camera = camera_manager.get_camera(camera_id)

    try:
        # Get current statistics baseline
        stats_before = mvsdk.CameraGetFrameStatistic(camera["handle"])

        # Start capturing
        was_capturing = camera["is_capturing"]
        if not was_capturing:
            mvsdk.CameraSetTriggerMode(camera["handle"], 0)
            mvsdk.CameraPlay(camera["handle"])

        # Collect data
        frame_count = 0
        total_bytes = 0
        start_time = time.time()

        while (time.time() - start_time) < duration:
            try:
                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(camera["handle"], 200)
                mvsdk.CameraImageProcess(camera["handle"], pRawData, camera["frame_buffer"], FrameHead)
                mvsdk.CameraReleaseImageBuffer(camera["handle"], pRawData)

                frame_count += 1
                total_bytes += FrameHead.uBytes

                # Small delay to prevent tight loop
                await asyncio.sleep(0.001)

            except mvsdk.CameraException as e:
                if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                    break

        # Stop if we started it
        if not was_capturing:
            mvsdk.CameraStop(camera["handle"])

        # Calculate results
        elapsed = time.time() - start_time
        stats_after = mvsdk.CameraGetFrameStatistic(camera["handle"])

        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        avg_mbps = (total_bytes / elapsed) / (1024 * 1024) if elapsed > 0 else 0

        # Get resolution for theoretical calculation
        res = mvsdk.CameraGetImageResolution(camera["handle"])
        bytes_per_frame = res.iWidth * res.iHeight * 3  # Assume RGB
        theoretical_mbps = (avg_fps * bytes_per_frame) / (1024 * 1024)

        lost_frames = stats_after.iLost - stats_before.iLost
        total_frames = stats_after.iTotal - stats_before.iTotal
        loss_rate = (lost_frames / total_frames) if total_frames > 0 else 0

        camera_manager.publish_event(camera_id, "speed_test_completed", {
            "duration": elapsed,
            "fps": avg_fps,
            "throughput_mbps": avg_mbps * 8,
            "loss_rate": loss_rate
        })

        return {
            "duration_seconds": elapsed,
            "frames_captured": frame_count,
            "total_bytes": total_bytes,
            "total_mb": total_bytes / (1024 * 1024),
            "average_fps": round(avg_fps, 2),
            "average_throughput_mbps": round(avg_mbps * 8, 2),
            "average_throughput_MBs": round(avg_mbps, 2),
            "theoretical_max_mbps": round(theoretical_mbps * 8, 2),
            "efficiency_percent": round((avg_mbps / theoretical_mbps * 100), 1) if theoretical_mbps > 0 else 0,
            "frame_statistics": {
                "total": total_frames,
                "lost": lost_frames,
                "loss_rate_percent": round(loss_rate * 100, 2)
            },
            "resolution": {
                "width": res.iWidth,
                "height": res.iHeight
            },
            "status": "excellent" if loss_rate < 0.01 else ("good" if loss_rate < 0.05 else "poor")
        }

    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Speed test failed: {e.message}")

@app.get("/cameras/{camera_id}/network/packet-length")
async def get_packet_length(camera_id: int):
    """Get current GigE packet length setting"""
    camera = camera_manager.get_camera(camera_id)
    try:
        pack_len = mvsdk.CameraGetTransPackLen(camera["handle"])
        return {
            "packet_length_index": pack_len,
            "camera_id": camera_id
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Get packet length failed: {e.message}")

@app.put("/cameras/{camera_id}/network/packet-length")
async def set_packet_length(camera_id: int, packet_index: int):
    """Set GigE packet length (affects throughput)"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraSetTransPackLen(camera["handle"], packet_index)
        camera_manager.publish_event(camera_id, "packet_length_changed", {"index": packet_index})
        return {
            "status": "success",
            "packet_length_index": packet_index
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Set packet length failed: {e.message}")

@app.post("/cameras/{camera_id}/network/connection-test")
async def test_connection(camera_id: int):
    """Test camera network connection"""
    camera = camera_manager.get_camera(camera_id)
    try:
        result = mvsdk.CameraConnectTest(camera["handle"])

        return {
            "connected": result == mvsdk.CAMERA_STATUS_SUCCESS,
            "status_code": result,
            "reconnect_count": mvsdk.CameraGetReConnectCounts(camera["handle"])
        }
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {e.message}")

@app.post("/cameras/{camera_id}/network/reset-timestamp")
async def reset_timestamp(camera_id: int):
    """Reset camera frame timestamp counter"""
    camera = camera_manager.get_camera(camera_id)
    try:
        mvsdk.CameraRstTimeStamp(camera["handle"])
        camera_manager.publish_event(camera_id, "timestamp_reset", {})
        return {"status": "success"}
    except mvsdk.CameraException as e:
        raise HTTPException(status_code=500, detail=f"Reset timestamp failed: {e.message}")

# =============================================================================
# MQTT Configuration
# =============================================================================

@app.post("/mqtt/connect")
async def mqtt_connect(config: MQTTConfig):
    """Connect to MQTT broker"""
    try:
        camera_manager.init_mqtt(config.broker, config.port, config.topic_prefix)
        return {
            "status": "connected",
            "broker": config.broker,
            "port": config.port,
            "topic_prefix": config.topic_prefix
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MQTT connection failed: {str(e)}")

@app.get("/mqtt/status")
async def mqtt_status():
    """Get MQTT connection status"""
    return {
        "available": MQTT_AVAILABLE,
        "connected": camera_manager.mqtt_client.is_connected() if camera_manager.mqtt_client else False,
        "config": camera_manager.mqtt_config
    }

# =============================================================================
# Main entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
