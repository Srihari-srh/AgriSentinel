import os
import subprocess

def snap_and_display():
    print("1. Commanding Luckfox board to snap a live camera frame...")
    # Trigger v4l2-ctl on the board to capture 1 frame
    snap_cmd = "adb shell \"v4l2-ctl --device=/dev/video0 --stream-mmap --stream-count=1 --stream-to=/mnt/sdcard/ai_model/rknn_yolov5_demo/snap_test.raw\""
    subprocess.run(snap_cmd, shell=True)
    
    print("2. Copying raw frame back to Windows PC...")
    # Pull the file from board to local processing folder
    pull_cmd = "adb pull /mnt/sdcard/ai_model/rknn_yolov5_demo/snap_test.raw processing/snap_test.raw"
    subprocess.run(pull_cmd, shell=True)
    
    print("3. Converting raw buffer to an inspectable image format...")
    # For a quick view, we can copy it or open it directly
    local_file = "processing/snap_test.jpg"
    if os.path.exists("processing/snap_test.raw"):
        os.replace("processing/snap_test.raw", local_file)
        print(f"SUCCESS: Image saved locally to '{local_file}'")
        print("Opening image in VS Code...")
        os.system(f"code {local_file}")
    else:
        print("ERROR: Failed to pull capture file from board.")

if __name__ == "__main__":
    snap_and_display()
    