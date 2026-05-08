from bleak import BleakScanner
import asyncio
TARGET = "05:07:99:8D:11:B9"
async def test():
    devices = await BleakScanner.discover(timeout=5)
    for d in devices:
        if d.address == TARGET:
            print("Found target device:", d)
            break

asyncio.run(test())