import asyncio
import json

import websockets


async def test_connection():
	uri = "ws://localhost:8000/ws?token=guest"
	print(f"Connecting to {uri}...")
	try:
		async with websockets.connect(uri) as websocket:
			print("Connected!")

			# Wait for welcome message
			response = await websocket.recv()
			print(f"Received: {response}")

			# Send ping
			await websocket.send(json.dumps({"type": "ping"}))
			print("Sent ping")

			# Wait for pong
			response = await websocket.recv()
			print(f"Received: {response}")

	except Exception as e:
		print(f"Connection failed: {e}")


if __name__ == "__main__":
	asyncio.run(test_connection())
