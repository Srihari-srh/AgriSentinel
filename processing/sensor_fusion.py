# Filename: processing/sensor_fusion.py
import os
import fcntl
import math
import time
import serial

# --- NATIVE I2C IMU CONFIGURATION ---
I2C_SLAVE = 0x0703
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
I2C_BUS_PATH = "/dev/i2c-3" # Configured for Pins 14 (SDA) and 15 (SCL)

try:
    # Open the I2C device file natively
    i2c_fd = os.open(I2C_BUS_PATH, os.O_RDWR)
    # Tell the Linux kernel we want to talk to the MPU6050
    fcntl.ioctl(i2c_fd, I2C_SLAVE, MPU6050_ADDR)
    # Write 0 to the Power Management register to wake it up
    os.write(i2c_fd, bytes([PWR_MGMT_1, 0]))
    time.sleep(0.1)
except Exception as e:
    print(f"IMU Init Error (Check wiring or bus number): {e}")

def get_imu():
    try:
        # Tell the sensor we want to start reading from the Accelerometer X register
        os.write(i2c_fd, bytes([ACCEL_XOUT_H]))
        # Read 14 consecutive bytes (Accel X, Y, Z, Temp, Gyro X, Y, Z) directly from silicon
        data = os.read(i2c_fd, 14)
        
        def parse_16bit(high, low):
            val = (high << 8) | low
            return val - 65536 if val >= 32768 else val
        
        # Scale Accelerometer (16384.0 for +/- 2g)
        ax = parse_16bit(data[0], data[1]) / 16384.0
        ay = parse_16bit(data[2], data[3]) / 16384.0
        az = parse_16bit(data[4], data[5]) / 16384.0
        
        # Scale Gyroscope (131.0 for +/- 250 d/s)
        gx = parse_16bit(data[8], data[9]) / 131.0
        gy = parse_16bit(data[10], data[11]) / 131.0
        gz = parse_16bit(data[12], data[13]) / 131.0
        
        roll = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
        
        return {"ax": ax, "ay": ay, "az": az, "gx": gx, "gy": gy, "gz": gz, "roll": roll, "pitch": pitch}
    except:
        return {"ax": 0.0, "ay": 0.0, "az": 0.0, "gx": 0.0, "gy": 0.0, "gz": 0.0, "roll": 0.0, "pitch": 0.0}

# --- NATIVE UART GPS CONFIGURATION ---
UART_PORT = '/dev/ttyS3' # Configured for Pins 12 (TX) and 13 (RX)
BAUD_RATE = 9600
try:
    gps_serial = serial.Serial(UART_PORT, BAUD_RATE, timeout=0)
except Exception as e:
    print(f"GPS Init Error: {e}")

def parse_nmea(sentence):
    try:
        parts = sentence.split(',')
        if parts[0] == '$GPGGA' and len(parts) >= 15 and parts[6] != '0':
            lat = float(parts[2][:2]) + float(parts[2][2:])/60.0
            if parts[3] == 'S': lat = -lat
            lon = float(parts[4][:3]) + float(parts[4][3:])/60.0
            if parts[5] == 'W': lon = -lon
            return {"fix": True, "lat": lat, "lon": lon, "sats": int(parts[7])}
    except:
        pass
    return None

# --- MAIN FUSION LOOP ---
if __name__ == '__main__':
    print("Starting NATIVE Sensor Fusion (I2C3 & UART3)...")
    print("TIMESTAMP | LAT | LON | SATS | ACC_X | ACC_Y | ACC_Z | ROLL | PITCH")
    print("-" * 70)
    
    last_gps = {"fix": False, "lat": 0.0, "lon": 0.0, "sats": 0}
    gps_buffer = ""

    try:
        while True:
            # 1. Non-blocking GPS Read
            if 'gps_serial' in locals() and gps_serial.in_waiting > 0:
                gps_buffer += gps_serial.read(gps_serial.in_waiting).decode('ascii', errors='ignore')
                if '\n' in gps_buffer:
                    lines = gps_buffer.split('\n')
                    gps_buffer = lines[-1]
                    for line in lines[:-1]:
                        if line.startswith('$GPGGA'):
                            parsed = parse_nmea(line.strip())
                            if parsed:
                                last_gps = parsed
            
            # 2. Fast IMU Read
            imu = get_imu()
            timestamp = time.time()
            
            # 3. Print Fused Data
            print(f"{timestamp:.2f} | {last_gps['lat']:.5f} | {last_gps['lon']:.5f} | {last_gps['sats']} | "
                  f"{imu['ax']: .2f} | {imu['ay']: .2f} | {imu['az']: .2f} | {imu['roll']: .1f} | {imu['pitch']: .1f}")
            
            time.sleep(0.1) # 10Hz loop
            
    except KeyboardInterrupt:
        print("\nSensor Fusion Stopped.")