# Filename: hardware/imu.py
import smbus2
import math
import time

# MPU6050 Registers and Addresses
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43
TEMP_OUT_H   = 0x41

# Initialize I2C bus (Luckfox Pico Mini B usually uses I2C bus 3 or 4)
I2C_BUS = 3
try:
    bus = smbus2.SMBus(I2C_BUS)
except FileNotFoundError:
    print(f"Error: I2C bus {I2C_BUS} not found. Check if I2C is enabled in your board config.")
    exit(1)

def init_mpu():
    # Wake up the MPU6050 (it starts in sleep mode by default)
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
    time.sleep(0.1)

def read_raw_data(addr):
    # Read two bytes (high and low) from the given register address
    high = bus.read_byte_data(MPU6050_ADDR, addr)
    low = bus.read_byte_data(MPU6050_ADDR, addr+1)
    
    # Combine high and low bytes using bitwise operations
    value = ((high << 8) | low)
    
    # Convert to signed 16-bit integer (2's complement)
    if value > 32768:
        value = value - 65536
    return value

def get_imu_data():
    # Read Accelerometer raw data
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(ACCEL_XOUT_H + 4)
    
    # Read Gyroscope raw data
    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_XOUT_H + 2)
    gyro_z = read_raw_data(GYRO_XOUT_H + 4)
    
    # Read Temperature raw data
    temp_raw = read_raw_data(TEMP_OUT_H)
    
    # Convert raw values to standard units
    # Accelerometer scale factor for default +/- 2g sensitivity is 16384.0
    Ax = acc_x / 16384.0
    Ay = acc_y / 16384.0
    Az = acc_z / 16384.0
    
    # Gyroscope scale factor for default +/- 250 deg/s sensitivity is 131.0
    Gx = gyro_x / 131.0
    Gy = gyro_y / 131.0
    Gz = gyro_z / 131.0
    
    # Temperature conversion formula from MPU6050 datasheet
    Temp_C = (temp_raw / 340.0) + 36.53
    
    # Calculate basic tilt angles (Roll and Pitch) in degrees using trigonometry
    roll = math.degrees(math.atan2(Ay, math.sqrt(Ax**2 + Az**2)))
    pitch = math.degrees(math.atan2(-Ax, math.sqrt(Ay**2 + Az**2)))
    
    return {
        "accel": (Ax, Ay, Az),
        "gyro": (Gx, Gy, Gz),
        "temp": Temp_C,
        "tilt": (roll, pitch)
    }

if __name__ == '__main__':
    print("Initializing MPU6050...")
    try:
        init_mpu()
        print("Reading data... Press Ctrl+C to stop.")
        while True:
            data = get_imu_data()
            print(f"Acc(g): X={data['accel'][0]:.2f} Y={data['accel'][1]:.2f} Z={data['accel'][2]:.2f} | "
                  f"Gyro(d/s): X={data['gyro'][0]:.1f} Y={data['gyro'][1]:.1f} Z={data['gyro'][2]:.1f} | "
                  f"Tilt: Roll={data['tilt'][0]:.1f} Pitch={data['tilt'][1]:.1f} | "
                  f"Temp: {data['temp']:.1f}C")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Check your wiring and verify the I2C bus number.")