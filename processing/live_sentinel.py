import os
import subprocess
import time
from periphery import GPIO

# Hardware Pin Definitions
GREEN_PIN = 16  # Healthy Plant Indicator
RED_PIN = 17    # Diseased Plant Indicator

def setup_gpio():
    """Initializes GPIO pins for LED feedback with a sysfs fallback."""
    try:
        green = GPIO(GREEN_PIN, "out")
        red = GPIO(RED_PIN, "out")
        print("GPIO initialized successfully using periphery library.")
        return green, red
    except Exception as e:
        print(f"Periphery init warning: {e}. Switching to sysfs fallback.")
        os.system(f"echo {GREEN_PIN} > /sys/class/gpio/export 2>/dev/null")
        os.system(f"echo out > /sys/class/gpio/gpio{GREEN_PIN}/direction 2>/dev/null")
        os.system(f"echo {RED_PIN} > /sys/class/gpio/export 2>/dev/null")
        os.system(f"echo out > /sys/class/gpio/gpio{RED_PIN}/direction 2>/dev/null")
        return None, None

def set_led_status(green_gpio, red_gpio, status):
    """Controls LED output based on health status."""
    if green_gpio and red_gpio:
        if status == "HEALTHY":
            green_gpio.write(True)
            red_gpio.write(False)
        else:
            green_gpio.write(False)
            red_gpio.write(True)
    else:
        # Sysfs fallback control
        if status == "HEALTHY":
            os.system(f"echo 1 > /sys/class/gpio/gpio{GREEN_PIN}/value")
            os.system(f"echo 0 > /sys/class/gpio/gpio{RED_PIN}/value")
        else:
            os.system(f"echo 0 > /sys/class/gpio/gpio{GREEN_PIN}/value")
            os.system(f"echo 1 > /sys/class/gpio/gpio{RED_PIN}/value")

def run_detection_pipeline():
    print("Starting AgriSentinel Live Crop Disease Detection Pipeline...")
    green_led, red_led = setup_gpio()
    
    binary_path = "/tmp/rknn_yolov5_demo"
    model_path = "model/paddy_rv1103.rknn"
    raw_frame = "live_frame.raw"
    target_image = "live_inference.jpg"
    
    try:
        while True:
            # Step 1: Capture a live frame from the camera node (/dev/video0)
            capture_cmd = f"v4l2-ctl --device=/dev/video0 --stream-mmap --stream-count=1 --stream-to={raw_frame}"
            os.system(capture_cmd)
            
            if not os.path.exists(raw_frame) or os.path.getsize(raw_frame) == 0:
                print("Waiting for camera stream buffer...")
                time.sleep(1)
                continue
                
            # Map raw buffer into processing format for inference
            os.system(f"cp {raw_frame} {target_image}")
            
            # Step 2: Execute NPU-accelerated YOLOv5 C++ binary on the captured frame
            inference_cmd = f"export LD_LIBRARY_PATH=lib:$LD_LIBRARY_PATH && {binary_path} {model_path} {target_image}"
            result = subprocess.run(inference_cmd, shell=True, capture_output=True, text=True)
            output_log = result.stdout
            
            # Step 3: Evaluate detection output for disease markers
            if "cls:" in output_log or "@ (" in output_log or "box" in output_log:
                print("STATUS: 🔴 DISEASE DETECTED -> Red LED ON (Pin 17)")
                set_led_status(green_led, red_led, "DISEASED")
                
                # Automatically save snapshot of the diseased crop for verification
                saved_name = f"diseased_{int(time.time())}.jpg"
                os.system(f"cp {target_image} {saved_name}")
                print(f"Saved local archive of diseased crop: {saved_name}")
            else:
                print("STATUS: 🟢 HEALTHY CROP -> Green LED ON (Pin 16)")
                set_leds = set_led_status(green_led, red_led, "HEALTHY")
                
            time.sleep(2) # Scan cooldown delay
            
    except KeyboardInterrupt:
        print("\nStopping pipeline safely...")
        set_led_status(green_led, red_led, "HEALTHY")
        if green_led: green_led.close()
        if red_led: red_led.close()

if __name__ == "__main__":
    run_detection_pipeline()
    