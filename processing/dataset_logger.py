# Filename: processing/dataset_logger.py
import os
import fcntl
import math
import time
import csv

# --- NATIVE I2C IMU CONFIGURATION ---
I2C_SLAVE = 0x0703
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
I2C_BUS_PATH = "/dev/i2c-3" 

try:
    i2c_fd = os.open(I2C_BUS_PATH, os.O_RDWR)
    fcntl.ioctl(i2c_fd, I2C_SLAVE, MPU6050_ADDR)
    os.write(i2c_fd, bytes([PWR_MGMT_1, 0]))
    time.sleep(0.1)
except Exception as e:
    print(f"IMU Init Error: {e}")
    exit()

def get_imu():
    try:
        os.write(i2c_fd, bytes([ACCEL_XOUT_H]))
        data = os.read(i2c_fd, 14)
        
        def parse_16bit(high, low):
            val = (high << 8) | low
            return val - 65536 if val >= 32768 else val
        
        ax = parse_16bit(data[0], data[1]) / 16384.0
        ay = parse_16bit(data[2], data[3]) / 16384.0
        az = parse_16bit(data[4], data[5]) / 16384.0
        roll = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
        
        return [ax, ay, az, roll, pitch]
    except:
        return [0.0, 0.0, 0.0, 0.0, 0.0]

# --- DATASET COLLECTION LOOP ---
if __name__ == '__main__':
    csv_file = "/mnt/sdcard/AgriSentinel/imu_dataset.csv"
    
    print("\n--- AgriSentinel Dataset Collector ---")
    print("Examples of labels: 'idle', 'tractor_vibration', 'fence_tampering', 'falling'")
    label = input("Enter the label for this recording session: ").strip().lower()
    
    # Write headers if the file is brand new
    file_exists = os.path.isfile(csv_file)
    
    print(f"\nRecording data for '{label}'. Press Ctrl+C to stop recording.")
    print("TIMESTAMP | ACC_X | ACC_Y | ACC_Z | ROLL | PITCH | LABEL")
    print("-" * 60)
    
    try:
        with open(csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "acc_x", "acc_y", "acc_z", "roll", "pitch", "label"])
            
            while True:
                imu_data = get_imu()
                timestamp = time.time()
                
                # Write to CSV
                row = [f"{timestamp:.2f}"] + [f"{val:.3f}" for val in imu_data] + [label]
                writer.writerow(row)
                f.flush() # Force write to SD card immediately
                
                # Print to console
                print(f"{row[0]} | {row[1]:>6} | {row[2]:>6} | {row[3]:>6} | {row[4]:>6} | {row[5]:>6} | {row[6]}")
                
                time.sleep(0.1) # 10Hz recording
                
    except KeyboardInterrupt:
        print(f"\nRecording stopped. Data successfully saved to {csv_file}")