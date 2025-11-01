# Plan: Fix WebSocket `RuntimeError`

This plan outlines the steps to resolve the `RuntimeError: Expected ASGI message "websocket.send" or "websocket.close", but got 'websocket.accept'` in the FastAPI application.

## 1. Code Modification

*   **Objective:** Remove the redundant `websocket.accept()` call.
*   **File to Modify:** `backend/app/main.py`
*   **Action:**
    1.  Open `backend/app/main.py`.
    2.  Locate the `websocket_endpoint` function.
    3.  Delete the line `await websocket.accept()`.
    4.  Save the file.

## 2. Verification

*   **Objective:** Ensure the fix resolves the error and doesn't introduce new issues.
*   **Steps:**
    1.  **Run the backend server:**
        *   Execute the command `make run-backend` from the project root directory.
        *   Observe the console output for any startup errors.
    2.  **Create a WebSocket test client:**
        *   Create a new file named `test_websocket.py` in the project root.
        *   Add the following Python code to the file to create a simple WebSocket client that connects to the endpoint:
            ```python
            import asyncio
            import websockets

            async def test_websocket():
                uri = "ws://localhost:8002/ws"
                try:
                    async with websockets.connect(uri, extra_headers={"Authorization": "Bearer development_token"}) as websocket:
                        print("Connection established.")
                        # Test receiving the welcome message
                        welcome_message = await websocket.recv()
                        print(f"< {welcome_message}")

                        # Test sending a message
                        await websocket.send('{"type": "ping"}')
                        print("> PING")

                        # Test receiving a response
                        response = await websocket.recv()
                        print(f"< {response}")

                except Exception as e:
                    print(f"Connection failed: {e}")

            if __name__ == "__main__":
                asyncio.run(test_websocket())
            ```
    3.  **Run the test client:**
        *   In a new terminal, execute `python test_websocket.py`.
        *   Observe the output. A successful connection and message exchange will confirm the fix. The `RuntimeError` should no longer appear in the backend server's console output.
    4.  **Run existing tests:**
        *   Execute `make test-python` to ensure no existing tests have been broken by the change.

## 3. Cleanup

*   **Objective:** Remove the temporary test file.
*   **Action:**
    1.  Delete the `test_websocket.py` file.