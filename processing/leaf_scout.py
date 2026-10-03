import os
import time

GREEN_LED_PIN = 54
RED_LED_PIN = 55

def setup_led(gpio_num):
    # Tell Linux we want to use this GPIO pin
    if not os.path.exists(f"/sys/class/gpio/gpio{gpio_num}"):
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(gpio_num))
    time.sleep(0.1) # Brief pause to let the OS create the file
    
    # Set the pin as an output
    with open(f"/sys/class/gpio/gpio{gpio_num}/direction", "w") as f:
        f.write("out")

def turn_on_led(gpio_num):
    # Send 3.3V to the pin
    with open(f"/sys/class/gpio/gpio{gpio_num}/value", "w") as f:
        f.write("1")

def turn_off_led(gpio_num):
    # Drop the pin to 0V
    with open(f"/sys/class/gpio/gpio{gpio_num}/value", "w") as f:
        f.write("0")

# --- INITIALIZATION ---
# Run this once when your script starts
setup_led(GREEN_LED_PIN)
setup_led(RED_LED_PIN)

# --- EXAMPLE USAGE IN YOUR AI LOOP ---
# detected_disease = "blast"
# confidence = 0.85

# if detected_disease == "healthy":
#     turn_on_led(GREEN_LED_PIN)
#     turn_off_led(RED_LED_PIN)
# elif confidence > 0.5:
#     turn_on_led(RED_LED_PIN)
#     turn_off_led(GREEN_LED_PIN)