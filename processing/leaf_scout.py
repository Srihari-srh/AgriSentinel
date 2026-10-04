import cv2
import time
from periphery import GPIO

# --- HARDWARE CONFIGURATION ---
GREEN_LED_PIN = 16
RED_LED_PIN = 17

# Initialize GPIO pins as outputs once at startup
try:
    green_led = GPIO(GREEN_LED_PIN, "out")
    red_led = GPIO(RED_LED_PIN, "out")
    print("GPIO initialization successful: Green LED on Pin 16, Red LED on Pin 17.")
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    green_led = None
    red_led = None

def update_status_indicators(detection_count):
    """
    Controls physical breadboard LEDs based on YOLO inference results.
    - Healthy (0 detections): Green LED ON, Red LED OFF
    - Diseased (>0 detections): Red LED ON, Green LED OFF
    """
    if green_led is None or red_led is None:
        return

    try:
        if detection_count == 0:
            print("STATUS: 🟢 HEALTHY -> Green LED ON")
            green_led.write(True)   # Turn Green LED ON
            red_led.write(False)  # Turn Red LED OFF
        else:
            print(f"STATUS: 🔴 DISEASE DETECTED ({detection_count} instances) -> Red LED ON")
            green_led.write(False) # Turn Green LED OFF
            red_led.write(True)    # Turn Red LED ON
            
    except IOError as e:
        print(f"Hardware LED control error: {e}")

def main():
    print("Starting AgriSentinel Leaf Scout Stream...")
    
    # Initialize video capture (adjust index if using external camera or default stream)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Retrying...")
                time.sleep(0.1)
                continue

            # --- PLACEHOLDER FOR RKNN MODEL INFERENCE ---
            # Replace this block with your actual RKNN model execution call.
            # Example:
            # results = rknn_model.inference(frame)
            # detection_count = results.get("count", 0)
            
            # Simulated inference check for stream loop validation:
            detection_count = 0  # Set to >0 to test red LED trigger logic

            # Update hardware indicator lights based on analysis output
            update_status_indicators(detection_count)

            # Optional: Display frame locally if a desktop environment is attached
            # cv2.imshow("AgriSentinel Live Feed", frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

            time.sleep(0.1) # Control loop sampling frequency

    except KeyboardInterrupt:
        print("Stopping Leaf Scout execution gracefully...")
    
    finally:
        # Clean up camera and close GPIO channels safely
        cap.release()
        cv2.destroyAllWindows()
        if green_led:
            green_led.write(False)
            green_led.close()
        if red_led:
            red_led.write(False)
            red_led.close()
        print("Hardware states reset and GPIO closed.")

if __name__ == "__main__":
    main()