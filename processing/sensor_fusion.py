# Filename: processing/sensor_fusion.py
import smbus2
import math
import time
import serial

# --- IMU CONFIGURATION ---
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43
I2C_BUS = 3

try:
    imu_bus = smbus2.SMBus(I2C_BUS)
    imu_bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
    time.sleep(0.1)
except Exception as e:
    print(f"IMU Init Error: {e}")

def read_imu_raw(addr):
    high = imu_bus.read_byte_data(MPU6050_ADDR, addr)
    low = imu_bus.read_byte_data(MPU6050_ADDR, addr+1)
    val = ((high << 8) | low)
    return val - 65536 if val > 32768 else val

def get_imu():
    ax = read_imu_raw(ACCEL_XOUT_H) / 16384.0
    ay = read_imu_raw(ACCEL_XOUT_H + 2) / 16384.0
    az = read_imu_raw(ACCEL_XOUT_H + 4) / 16384.0
    gx = read_imu_raw(GYRO_XOUT_H) / 131.0
    gy = read_imu_raw(GYRO_XOUT_H + 2) / 131.0
    gz = read_imu_raw(GYRO_XOUT_H + 4) / 131.0
    roll = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
    return {"ax": ax, "ay": ay, "az": az, "gx": gx, "gy": gy, "gz": gz, "roll": roll, "pitch": pitch}

# --- GPS CONFIGURATION ---
UART_PORT = '/dev/ttyS3'
BAUD_RATE = 9600
try:
    gps_serial = serial.Serial(UART_PORT, BAUD_RATE, timeout=0) # Timeout 0 = Non-blocking!
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
    print("Starting Sensor Fusion...")
    print("TIMESTAMP | LAT | LON | SATS | ACC_X | ACC_Y | ACC_Z | ROLL | PITCH")
    print("-" * 70)
    
    # Store the last known GPS data so IMU doesn't have to wait
    last_gps = {"fix": False, "lat": 0.0, "lon": 0.0, "sats": 0}
    gps_buffer = ""

    try:
        while True:
            # 1. Non-blocking GPS Read (Grabs whatever is in the UART buffer right now)
            if gps_serial.in_waiting > 0:
                gps_buffer += gps_serial.read(gps_serial.in_waiting).decode('ascii', errors='ignore')
                if '\n' in gps_buffer:
                    lines = gps_buffer.split('\n')
                    gps_buffer = lines[-1] # Keep the incomplete line for next time
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
            
            time.sleep(0.1) # Run loop at roughly 10Hz
            
    except KeyboardInterrupt:
        print("\nSensor Fusion Stopped.")