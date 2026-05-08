import asyncio
import time
from bleak import BleakClient, BleakScanner
import struct
import csv
from datetime import datetime

# BLE Configuration
CHARACTERISTIC_UUID = "6f42123f-62f9-49cc-a61f-9043dcf7ea12"
DEVICE_NAME = "NanoSense_ADS1256" # Must match the Arduino code

# Global variables
csv_file = None
csv_writer = None
first_arduino_time = None
last_print_time = 0

# ADS1256 Conversion Constants (Assuming PGA=1, VREF=2.5V from the module)
ADS1256_VREF = 2.5
MAX_24BIT_VAL = 8388607.0 # 2^23 - 1 for signed 24-bit

PRINT_INTERVAL = 5.0  # print every 5 seconds

def notification_handler(sender, data):
    global csv_writer, first_arduino_time, last_print_time

    # Check if exactly 224 bytes are received (8 samples)
    if len(data) != 224:
        return

    if csv_writer:
        for i in range(8):
            offset = i * 28
            sample_data = struct.unpack_from('<I6i', data, offset)

            ard_micros = sample_data[0]
            raw_adc = sample_data[1:7]

            if first_arduino_time is None:
                first_arduino_time = ard_micros

            delta_seconds = (ard_micros - first_arduino_time) / 1000000.0
            formatted_time = f"{delta_seconds:.6f}"

            voltages = [(val / MAX_24BIT_VAL) * (2 * ADS1256_VREF) for val in raw_adc]

            row = [formatted_time, ard_micros] + [f"{v:.8f}" for v in voltages]
            csv_writer.writerow(row)

            current_time = time.time()
            if current_time - last_print_time >= PRINT_INTERVAL:
                print(f"[{formatted_time}s] Arduino µs: {ard_micros} | CH1: {voltages[0]:.4f}V | CH2: {voltages[1]:.4f}V | CH3: {voltages[2]:.4f}V | CH4: {voltages[3]:.4f}V | CH5: {voltages[4]:.4f}V | CH6: {voltages[5]:.4f}V")
                last_print_time = current_time

async def run_ble():
    global csv_file, csv_writer, first_arduino_time, last_print_time
    print(f"Scanning for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=5.0)
    
    if not device:
        print(f"Could not find {DEVICE_NAME}.")
        return

    print(f"Found {DEVICE_NAME}. Connecting...")
    
    async with BleakClient(device) as client:
        print("Connected!")

        filename = f"sensor_data_24bit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_file = open(filename, mode='w', newline='')
        csv_writer = csv.writer(csv_file)

        csv_writer.writerow(['Relative_Time(s)', 'Ard_Micros', 'CH1(V)', 'CH2(V)', 'CH3(V)', 'CH4(V)', 'CH5(V)', 'CH6(V)'])
        print(f"Started saving data to {filename}")

        first_arduino_time = None
        last_print_time = time.time()
        
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        
        while True:
            await asyncio.sleep(1)

def main():
    global csv_file
    try:
        asyncio.run(run_ble())
    except KeyboardInterrupt:
        print("\n\n[System Message] Communication terminated safely by user (Ctrl+C).")
    finally:
        if csv_file and not csv_file.closed:
            csv_file.close()
            print("CSV file safely saved and closed.")

if __name__ == "__main__":
    main()