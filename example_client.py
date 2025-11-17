#!/usr/bin/env python3
"""
Example client for MindVision Camera API
Demonstrates basic usage of REST endpoints
"""

import requests
import json
import base64
import time
from PIL import Image
from io import BytesIO

# API Configuration
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")

def main():
    """Main example flow"""

    print_section("MindVision Camera API - Example Client")

    # 1. Check API health
    print_section("1. Checking API Health")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))

    # 2. Discover cameras
    print_section("2. Discovering Cameras")
    response = requests.get(f"{BASE_URL}/cameras/discover")
    cameras = response.json()
    print(f"Found {len(cameras)} camera(s):")
    for i, cam in enumerate(cameras):
        print(f"  [{i}] {cam['friendly_name']} ({cam['product_name']}) - SN: {cam['serial_number']}")

    if len(cameras) == 0:
        print("\nNo cameras found. Please connect a camera and try again.")
        return

    # 3. Connect to first camera
    print_section("3. Connecting to Camera")
    camera_index = 0
    response = requests.post(f"{BASE_URL}/cameras/{camera_index}/connect")
    camera_info = response.json()
    camera_id = camera_info["camera_id"]
    print(f"Connected to camera {camera_id}")
    print(f"  Name: {camera_info['friendly_name']}")
    print(f"  Type: {camera_info['sensor_type']}")
    print(f"  Port: {camera_info['port_type']}")

    try:
        # 4. Get camera capability
        print_section("4. Camera Capabilities")
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/capability")
        cap = response.json()
        print(json.dumps(cap, indent=2))

        # 5. Configure camera
        print_section("5. Configuring Camera")

        # Set resolution
        print("Setting resolution to 1920x1080...")
        resolution_config = {
            "width": 1920,
            "height": 1080,
            "offset_x": 0,
            "offset_y": 0
        }
        response = requests.put(
            f"{BASE_URL}/cameras/{camera_id}/resolution",
            json=resolution_config
        )
        print(f"  Status: {response.json()['status']}")

        # Configure exposure
        print("\nConfiguring exposure (manual, 30ms, gain=100)...")
        exposure_config = {
            "auto_exposure": False,
            "exposure_time": 30000,  # 30ms in microseconds
            "analog_gain": 100
        }
        response = requests.put(
            f"{BASE_URL}/cameras/{camera_id}/exposure",
            json=exposure_config
        )
        print(f"  Status: {response.json()['status']}")

        # Configure image processing
        print("\nConfiguring image processing...")
        processing_config = {
            "gamma": 100,
            "contrast": 100,
            "saturation": 100,
            "sharpness": 3,
            "noise_filter": True
        }
        response = requests.put(
            f"{BASE_URL}/cameras/{camera_id}/image-processing",
            json=processing_config
        )
        print(f"  Status: {response.json()['status']}")

        # 6. Start capturing
        print_section("6. Starting Capture")
        response = requests.post(f"{BASE_URL}/cameras/{camera_id}/start")
        print(f"Capture status: {response.json()['status']}")

        # Wait for camera to stabilize
        print("Waiting for camera to stabilize...")
        time.sleep(2)

        # 7. Capture images
        print_section("7. Capturing Images")

        # Capture single JPEG
        print("Capturing JPEG image...")
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/snap?format=jpeg")
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            filename = "captured_image.jpg"
            image.save(filename)
            print(f"  Saved to: {filename}")
            print(f"  Size: {image.size}")
            print(f"  Mode: {image.mode}")
        else:
            print(f"  Failed: {response.status_code}")

        # Get frame as base64
        print("\nGetting frame as base64...")
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/frame?encoding=base64")
        if response.status_code == 200:
            frame_data = response.json()
            print(f"  Size: {frame_data['width']}x{frame_data['height']}")
            print(f"  Mono: {frame_data['is_mono']}")
            print(f"  Timestamp: {frame_data['timestamp']}")

            # Decode and save
            image_data = base64.b64decode(frame_data["image"])
            image = Image.open(BytesIO(image_data))
            filename = "frame_base64.jpg"
            image.save(filename)
            print(f"  Saved to: {filename}")
        else:
            print(f"  Failed: {response.status_code}")

        # 8. Get statistics
        print_section("8. Camera Statistics")
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/statistics")
        stats = response.json()
        print(f"Total frames: {stats['total_frames']}")
        print(f"Captured frames: {stats['captured_frames']}")
        print(f"Lost frames: {stats['lost_frames']}")
        print(f"Loss rate: {stats['loss_rate']*100:.2f}%")

        # 9. Test trigger
        print_section("9. Testing Software Trigger")
        print("Setting trigger mode to software...")
        trigger_config = {
            "trigger_mode": 1,  # Software trigger
            "trigger_delay": 0
        }
        response = requests.put(
            f"{BASE_URL}/cameras/{camera_id}/trigger",
            json=trigger_config
        )
        print(f"  Status: {response.json()['status']}")

        print("\nSending software trigger...")
        response = requests.post(f"{BASE_URL}/cameras/{camera_id}/trigger/software")
        print(f"  Status: {response.json()['status']}")

        # Wait a bit then capture triggered image
        time.sleep(0.1)
        print("\nCapturing triggered image...")
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/snap?format=jpeg&timeout=2000")
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            filename = "triggered_image.jpg"
            image.save(filename)
            print(f"  Saved to: {filename}")
        else:
            print(f"  Failed: {response.status_code}")

        # Set back to continuous mode
        print("\nSetting trigger mode back to continuous...")
        trigger_config["trigger_mode"] = 0
        requests.put(f"{BASE_URL}/cameras/{camera_id}/trigger", json=trigger_config)

        # 10. Save parameters
        print_section("10. Parameter Management")
        print("Saving current parameters to team 1...")
        response = requests.post(f"{BASE_URL}/cameras/{camera_id}/parameters/save?team=1")
        print(f"  Status: {response.json()['status']}")

        # 11. Get camera status
        print_section("11. Camera Status")
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/status")
        status = response.json()
        print(json.dumps(status, indent=2))

    finally:
        # 12. Stop and disconnect
        print_section("12. Cleanup")
        print("Stopping capture...")
        response = requests.post(f"{BASE_URL}/cameras/{camera_id}/stop")
        print(f"  Status: {response.json()['status']}")

        print("\nDisconnecting camera...")
        response = requests.post(f"{BASE_URL}/cameras/{camera_id}/disconnect")
        print(f"  Status: {response.json()['status']}")

    print_section("Example Complete!")
    print("Check the working directory for captured images:")
    print("  - captured_image.jpg")
    print("  - frame_base64.jpg")
    print("  - triggered_image.jpg")
    print()

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API server.")
        print("Make sure the API server is running: python camera_api.py")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
