# Filename: hardware/gps.py
import serial
import time

# Configure UART Port (Change '/dev/ttyS3' to match the UART port you wired to)
UART_PORT = '/dev/ttyS3'
BAUD_RATE = 9600

def convert_to_decimal_degrees(raw_value, direction):
    """ Converts NMEA format (DDMM.MMMMM) to Decimal Degrees (DD.DDDDD) """
    if not raw_value:
        return 0.0
    
    # Extract degrees and minutes
    dot_idx = raw_value.find('.')
    degrees = float(raw_value[:dot_idx-2])
    minutes = float(raw_value[dot_idx-2:])
    
    decimal = degrees + (minutes / 60.0)
    if direction == 'S' or direction == 'W':
        decimal = -decimal
    return decimal

def parse_gpgga(sentence):
    """ Parses the $GPGGA NMEA sentence for location and fix data """
    try:
        parts = sentence.split(',')
        if len(parts) >= 15 and parts[0] == '$GPGGA':
            fix_quality = int(parts[6]) if parts[6] else 0
            sats = int(parts[7]) if parts[7] else 0
            
            if fix_quality > 0:
                lat = convert_to_decimal_degrees(parts[2], parts[3])
                lon = convert_to_decimal_degrees(parts[4], parts[5])
                alt = float(parts[9]) if parts[9] else 0.0
                return {"fix": True, "lat": lat, "lon": lon, "alt": alt, "sats": sats}
            else:
                return {"fix": False, "lat": None, "lon": None, "alt": None, "sats": sats}
    except Exception as e:
        pass
    return None

def read_gps_data():
    print(f"Connecting to GPS on {UART_PORT} at {BAUD_RATE} baud...")
    try:
        ser = serial.Serial(UART_PORT, BAUD_RATE, timeout=1)
        print("Reading GPS data... (Take board near a window for a fix!) Press Ctrl+C to stop.")
        
        while True:
            line = ser.readline().decode('ascii', errors='replace').strip()
            
            # We look specifically for the GPGGA sentence (Global Positioning System Fix Data)
            if line.startswith('$GPGGA'):
                data = parse_gpgga(line)
                if data:
                    if data['fix']:
                        print(f"[FIX OK] Sats: {data['sats']} | Lat: {data['lat']:.6f} | Lon: {data['lon']:.6f} | Alt: {data['alt']}m")
                    else:
                        print(f"[NO FIX] Sats in view: {data['sats']} (Waiting for satellite lock...)")
                        
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        print("Ensure the correct UART_PORT is set and wiring is correct.")
    except KeyboardInterrupt:
        print("\nGPS reading stopped.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == '__main__':
    read_gps_data()