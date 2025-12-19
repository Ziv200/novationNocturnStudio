import hid
import time
import sys

# Nocturn
VID = 0x1235
PID = 0x000a

def main():
    print(f"Looking for Nocturn (VID: 0x{VID:04X}, PID: 0x{PID:04X})...")
    
    # Enumerate to verify it's there and see path
    devices = hid.enumerate(VID, PID)
    if not devices:
        print("Device not found via hidapi.")
        sys.exit(1)
    
    for d in devices:
        print(f"Found: {d['product_string']} (Path: {d['path']})")

    try:
        h = hid.device()
        h.open(VID, PID)
        print(f"Opened device: {h.get_manufacturer_string()} {h.get_product_string()}")
        h.set_nonblocking(1) # Enable non-blocking mode
        
        # Init sequence? 
        # Often Nocturn needs a "hello" to start sending data.
        # Based on reversed protocols (e.g. from open-source linux drivers), 
        # we might just need to read. Some sources say sending anything works.
        # Let's try sending a simple report if reading is silent.
        
        print("Entering read loop. interact with the controller...")
        
        while True:
            # Read 64 bytes
            data = h.read(64)
            if data:
                hex_data = " ".join([f"{x:02X}" for x in data])
                print(f"DATA: {hex_data}")
            
            time.sleep(0.01)

    except IOError as e:
        print(f"IOError: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        try:
            h.close()
        except:
            pass

if __name__ == "__main__":
    main()
