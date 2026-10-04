import subprocess
import time
import os
from periphery import GPIO

GREEN_LED_PIN = 16
RED_LED_PIN = 17

try:
    green_led = GPIO(GREEN_LED_PIN, "out")
    red_led = GPIO(RED_LED_PIN, "out")
    print("GPIO Initialized successfully on Pins 16 & 17.")
except Exception as e:
    print(f"GPIO Init Warning: {e}")
    green_led = None
    red_led = None

def set_leds(status):
    if not green_led or not red_led:
        return
    if status == "HEALTHY":
        green_led.write(True)
        red_led.write(False)
    else:
        green_led.write(False)
        red_led.write(True)

def run_inference_loop():
    print("Starting AgriSentinel Manager with NPU Cooling Cooldown...")
    
    binary_path = "/tmp/rknn_yolov5_demo"
    model_path = "model/paddy_rv1103.rknn"
    target_image = "model/test_disease.jpg" 
    
    try:
        while True:
            cmd = f"export LD_LIBRARY_PATH=lib:$LD_LIBRARY_PATH && {binary_path} {model_path} {target_image}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout
            
            # Check if NPU allocation failed
            if "fail!" in output or "ret=-" in output:
                print("NPU busy, cooling down memory...")
                time.sleep(2)
                continue

            print("--- Model Raw Output ---")
            print(output.strip())
            
            # Check for detections
            if "cls:" in output or "@ (" in output or "result" in output:
                print("STATUS: 🔴 DISEASE DETECTED -> Red LED ON")
                set_leds("DISEASE")
            else:
                print("STATUS: 🟢 HEALTHY -> Green LED ON")
                set_leds("HEALTHY")
                
            print("-" * 30)
            
            # Give the NPU plenty of breathing room between runs
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("Stopping safely...")
        if green_led: green_led.write(False); green_led.close()
        if red_led: red_led.write(False); red_led.close()

if __name__ == "__main__":
    run_inference_loop()