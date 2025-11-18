#!/usr/bin/env python3
"""
MindVision GigE Camera Network Speed Test Utility

Tests actual data throughput, packet loss, and network performance
for the MindVision 47MP GigE Vision camera.
"""

import mvsdk
import time
import sys
from datetime import datetime

class CameraSpeedTest:
    def __init__(self):
        self.camera_handle = None
        self.frame_buffer = None
        self.capability = None

    def connect_camera(self, camera_index=0):
        """Connect to camera"""
        print("\n" + "="*60)
        print("MindVision GigE Camera Speed Test")
        print("="*60)

        # Enumerate cameras
        print("\n[1/5] Discovering cameras...")
        devices = mvsdk.CameraEnumerateDevice()
        if len(devices) == 0:
            print("ERROR: No cameras found!")
            return False

        if camera_index >= len(devices):
            print(f"ERROR: Camera index {camera_index} out of range!")
            return False

        dev_info = devices[camera_index]
        print(f"Found: {dev_info.GetFriendlyName()} ({dev_info.GetSn()})")
        print(f"Port: {dev_info.GetPortType()}")

        # Initialize camera
        print("\n[2/5] Connecting to camera...")
        try:
            self.camera_handle = mvsdk.CameraInit(dev_info, -1, -1)
            print("✓ Connected successfully")
        except mvsdk.CameraException as e:
            print(f"✗ Connection failed: {e.message}")
            return False

        # Get capability
        self.capability = mvsdk.CameraGetCapability(self.camera_handle)

        # Allocate frame buffer
        mono = self.capability.sIspCapacity.bMonoSensor != 0
        buffer_size = (self.capability.sResolutionRange.iWidthMax *
                      self.capability.sResolutionRange.iHeightMax *
                      (1 if mono else 3))
        self.frame_buffer = mvsdk.CameraAlignMalloc(buffer_size, 16)

        # Set output format
        if mono:
            mvsdk.CameraSetIspOutFormat(self.camera_handle, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(self.camera_handle, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

        return True

    def get_network_info(self):
        """Get current network configuration"""
        print("\n[3/5] Network Configuration:")
        print("-" * 60)

        try:
            # Get packet length
            pack_len = mvsdk.CameraGetTransPackLen(self.camera_handle)
            print(f"Packet Length Index: {pack_len}")

            # Get camera info
            info = mvsdk.CameraGetInformation(self.camera_handle)
            print(f"Camera Info: {info}")

            # Connection test
            test_result = mvsdk.CameraConnectTest(self.camera_handle)
            if test_result == mvsdk.CAMERA_STATUS_SUCCESS:
                print("Connection Status: ✓ Connected")
            else:
                print(f"Connection Status: ✗ Error (code: {test_result})")

            # Get resolution
            res = mvsdk.CameraGetImageResolution(self.camera_handle)
            print(f"Resolution: {res.iWidth}x{res.iHeight}")
            print(f"Max Resolution: {self.capability.sResolutionRange.iWidthMax}x"
                  f"{self.capability.sResolutionRange.iHeightMax}")

        except Exception as e:
            print(f"Error getting network info: {e}")

    def run_throughput_test(self, duration_seconds=10):
        """Run bandwidth throughput test"""
        print(f"\n[4/5] Running Throughput Test ({duration_seconds}s)...")
        print("-" * 60)

        # Set continuous capture mode
        mvsdk.CameraSetTriggerMode(self.camera_handle, 0)

        # Start capture
        mvsdk.CameraPlay(self.camera_handle)

        # Reset timestamp
        try:
            mvsdk.CameraRstTimeStamp(self.camera_handle)
        except:
            pass

        # Collect data
        frame_count = 0
        total_bytes = 0
        error_count = 0
        start_time = time.time()
        last_fps_time = start_time
        last_fps_count = 0

        print("\nCapturing frames...")
        print(f"{'Time':>6} | {'Frames':>8} | {'FPS':>6} | {'MB/s':>8} | {'Lost':>6} | Status")
        print("-" * 60)

        try:
            while (time.time() - start_time) < duration_seconds:
                try:
                    # Get frame
                    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(
                        self.camera_handle, 200
                    )

                    # Process frame
                    mvsdk.CameraImageProcess(
                        self.camera_handle,
                        pRawData,
                        self.frame_buffer,
                        FrameHead
                    )

                    # Release buffer
                    mvsdk.CameraReleaseImageBuffer(self.camera_handle, pRawData)

                    frame_count += 1
                    total_bytes += FrameHead.uBytes

                    # Calculate stats every second
                    current_time = time.time()
                    elapsed = current_time - last_fps_time

                    if elapsed >= 1.0:
                        # Get frame statistics
                        stats = mvsdk.CameraGetFrameStatistic(self.camera_handle)

                        fps = (frame_count - last_fps_count) / elapsed
                        mbps = (total_bytes / (current_time - start_time)) / (1024 * 1024)

                        time_elapsed = int(current_time - start_time)
                        lost = stats.iLost

                        print(f"{time_elapsed:>4}s | {frame_count:>8} | {fps:>6.1f} | "
                              f"{mbps:>8.2f} | {lost:>6} | OK")

                        last_fps_time = current_time
                        last_fps_count = frame_count

                except mvsdk.CameraException as e:
                    if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                        error_count += 1

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")

        finally:
            mvsdk.CameraStop(self.camera_handle)

        # Final results
        elapsed = time.time() - start_time
        print("\n" + "="*60)
        print("Test Results:")
        print("="*60)

        # Get final statistics
        try:
            stats = mvsdk.CameraGetFrameStatistic(self.camera_handle)

            avg_fps = frame_count / elapsed
            avg_mbps = (total_bytes / elapsed) / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)

            # Calculate theoretical vs actual
            res = mvsdk.CameraGetImageResolution(self.camera_handle)
            bytes_per_frame = res.iWidth * res.iHeight * 3  # Assume RGB
            theoretical_mbps = (avg_fps * bytes_per_frame) / (1024 * 1024)

            print(f"\nDuration: {elapsed:.2f} seconds")
            print(f"Total Frames: {frame_count}")
            print(f"Total Data: {total_mb:.2f} MB")
            print(f"Average FPS: {avg_fps:.2f}")
            print(f"Average Throughput: {avg_mbps:.2f} MB/s ({avg_mbps * 8:.2f} Mbps)")
            print(f"Theoretical Max: {theoretical_mbps:.2f} MB/s ({theoretical_mbps * 8:.2f} Mbps)")
            print(f"Efficiency: {(avg_mbps/theoretical_mbps)*100:.1f}%")

            print(f"\nFrame Statistics:")
            print(f"  Total Frames: {stats.iTotal}")
            print(f"  Captured: {stats.iCapture}")
            print(f"  Lost: {stats.iLost}")
            if stats.iTotal > 0:
                loss_rate = (stats.iLost / stats.iTotal) * 100
                print(f"  Loss Rate: {loss_rate:.2f}%")

                if loss_rate > 5:
                    print("\n⚠ WARNING: High frame loss detected!")
                    print("  Recommendations:")
                    print("  - Check network cable quality")
                    print("  - Verify switch supports jumbo frames")
                    print("  - Reduce resolution or frame rate")
                    print("  - Check CPU usage on host")
                elif loss_rate > 1:
                    print("\n⚠ NOTICE: Some frame loss detected")
                    print("  Performance may be improved")
                else:
                    print("\n✓ Excellent: Minimal frame loss")

            print(f"  Errors: {error_count}")

        except Exception as e:
            print(f"Error getting final statistics: {e}")

    def test_packet_sizes(self):
        """Test different packet sizes to find optimal setting"""
        print("\n[5/5] Testing Packet Sizes...")
        print("-" * 60)

        # Get available packet lengths
        cap = self.capability
        if cap.iPackLenDesc > 0:
            print(f"\nAvailable packet sizes: {cap.iPackLenDesc}")

            results = []

            for i in range(min(cap.iPackLenDesc, 5)):  # Test up to 5 packet sizes
                try:
                    # Set packet length
                    mvsdk.CameraSetTransPackLen(self.camera_handle, i)
                    current = mvsdk.CameraGetTransPackLen(self.camera_handle)

                    print(f"\nTesting packet size index {i}...")

                    # Run short test
                    mvsdk.CameraSetTriggerMode(self.camera_handle, 0)
                    mvsdk.CameraPlay(self.camera_handle)

                    frames = 0
                    start = time.time()

                    while (time.time() - start) < 2.0:  # 2 second test
                        try:
                            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(
                                self.camera_handle, 200
                            )
                            mvsdk.CameraImageProcess(
                                self.camera_handle,
                                pRawData,
                                self.frame_buffer,
                                FrameHead
                            )
                            mvsdk.CameraReleaseImageBuffer(self.camera_handle, pRawData)
                            frames += 1
                        except:
                            pass

                    mvsdk.CameraStop(self.camera_handle)

                    elapsed = time.time() - start
                    fps = frames / elapsed

                    # Get statistics
                    stats = mvsdk.CameraGetFrameStatistic(self.camera_handle)
                    loss_rate = 0
                    if stats.iTotal > 0:
                        loss_rate = (stats.iLost / stats.iTotal) * 100

                    results.append({
                        'index': i,
                        'fps': fps,
                        'loss_rate': loss_rate,
                        'frames': frames
                    })

                    print(f"  FPS: {fps:.2f}, Loss: {loss_rate:.2f}%")

                except Exception as e:
                    print(f"  Error testing index {i}: {e}")

            # Find best packet size
            if results:
                best = min(results, key=lambda x: (x['loss_rate'], -x['fps']))
                print(f"\n✓ Recommended packet size index: {best['index']}")
                print(f"  FPS: {best['fps']:.2f}, Loss: {best['loss_rate']:.2f}%")

                # Set to best
                mvsdk.CameraSetTransPackLen(self.camera_handle, best['index'])

        else:
            print("Packet length configuration not available")

    def cleanup(self):
        """Cleanup resources"""
        if self.camera_handle:
            try:
                mvsdk.CameraUnInit(self.camera_handle)
            except:
                pass

        if self.frame_buffer:
            try:
                mvsdk.CameraAlignFree(self.frame_buffer)
            except:
                pass

def main():
    """Main test routine"""
    # Initialize SDK
    try:
        mvsdk.CameraSdkInit(1)
    except:
        pass

    tester = CameraSpeedTest()

    try:
        # Connect
        if not tester.connect_camera(0):
            sys.exit(1)

        # Get network info
        tester.get_network_info()

        # Run throughput test
        print("\nStarting throughput test in 3 seconds...")
        print("Press Ctrl+C to stop early")
        time.sleep(3)

        tester.run_throughput_test(duration_seconds=10)

        # Test packet sizes
        print("\n\nTest packet sizes? (y/n): ", end='')
        response = input().strip().lower()
        if response == 'y':
            tester.test_packet_sizes()

        print("\n" + "="*60)
        print("Speed test complete!")
        print("="*60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
