#!/bin/sh
export LD_LIBRARY_PATH=lib:$LD_LIBRARY_PATH
echo "Starting AgriSentinel Live Camera Detection Loop..."

# Ensure your GPIO pins 16 (Green) and 17 (Red) are exported and set to output
if [ ! -d /sys/class/gpio/gpio16 ]; then
    echo 16 > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio16/direction
fi
if [ ! -d /sys/class/gpio/gpio17 ]; then
    echo 17 > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio17/direction
fi

while true; do
    # 1. Capture a live frame from the board camera (/dev/video0)
    # Using v4l2grab or the native stream tool to overwrite 'live_frame.jpg'
    v4l2grab -d /dev/video0 -o model/live_frame.jpg -W 640 -H 640 2>/dev/null
    
    if [ ! -f model/live_frame.jpg ]; then
        echo "Waiting for camera stream..."
        sleep 1
        continue
    fi

    # 2. Run the compiled C++ YOLOv5 RKNN binary on the live captured frame
    /tmp/rknn_yolov5_demo model/paddy_rv1103.rknn model/live_frame.jpg > /tmp/inference_out.txt 2>&1
    
    # 3. Parse output and trigger physical LEDs (Pin 16 = Green, Pin 17 = Red)
    if grep -q "cls:" /tmp/inference_out.txt || grep -q "@ (" /tmp/inference_out.txt; then
        echo "STATUS: 🔴 DISEASE DETECTED -> Red LED ON (Pin 17)"
        echo 0 > /sys/class/gpio/gpio16/value  # Green OFF
        echo 1 > /sys/class/gpio/gpio17/value  # Red ON
    else
        echo "STATUS: 🟢 HEALTHY -> Green LED ON (Pin 16)"
        echo 1 > /sys/class/gpio/gpio16/value  # Green ON
        echo 0 > /sys/class/gpio/gpio17/value  # Red OFF
    fi

    # Brief delay before capturing the next live frame
    sleep 2
done