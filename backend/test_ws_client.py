import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/sessions/test-session"
    try:
        async with websockets.connect(uri) as websocket:
            print("Successfully connected to WS")
            # We don't need to send anything, just stay open
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"WS connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
