import cv2
import numpy as np
from rknnlite.api import RKNNLite
import time

# Luckfox Pico Default System LED Path
LED_PATH = "/sys/class/leds/work/brightness"

def set_led(state):
    """Turns the onboard LED ON (True) or OFF (False)."""
    try:
        with open(LED_PATH, 'w') as f:
            f.write("1" if state else "0")
    except Exception as e:
        pass # Failsafe if LED path varies by board version

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def main():
    print("[INIT] Loading NPU Engine...")
    rknn = RKNNLite()
    
    # Load your exact model
    ret = rknn.load_rknn('./model/paddy_rv1103.rknn')
    if ret != 0:
        print("Failed to load RKNN model.")
        return

    # Bind to Core 0 of the RV1103 NPU
    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0)
    if ret != 0:
        print("Failed to initialize NPU runtime.")
        return

    print("[INIT] Activating Camera Module...")
    # /dev/video0 is the default MIPI CSI camera port on Luckfox
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    print("\n[READY] AgriSentinel Live Monitoring Started. Press Ctrl+C to stop.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            # Convert OpenCV BGR to RGB for the AI model
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Execute real-time NPU inference
            outputs = rknn.inference(inputs=[img_rgb])
            
            disease_detected = False
            
            # Parse the 3 output tensors from YOLOv5
            for tensor in outputs:
                # The raw NPU output needs a sigmoid activation to convert to percentages (0.0 to 1.0)
                tensor_probs = sigmoid(tensor)
                
                # YOLOv5 tensor structure: The 4th index is the "Objectness" confidence score
                # If any grid cell has an objectness score > 60%, we flag it as diseased
                max_confidence = np.max(tensor_probs[..., 4])
                
                if max_confidence > 0.60:
                    disease_detected = True
                    break # Stop checking other tensors, disease is confirmed

            # Trigger Hardware Response
            if disease_detected:
                print("STATUS: 🔴 DISEASE DETECTED -> LED ON")
                set_led(True)
            else:
                print("STATUS: 🟢 HEALTHY -> LED OFF")
                set_led(False)

            # Prevent CPU thermal throttling
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
    finally:
        set_led(False)
        cap.release()
        rknn.release()

if __name__ == '__main__':
    main()