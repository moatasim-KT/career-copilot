# Research: WebSocket `RuntimeError` in FastAPI Application

## 1. Problem Analysis

The provided traceback indicates a `RuntimeError: Expected ASGI message "websocket.send" or "websocket.close", but got 'websocket.accept'`. This error originates from the `starlette` library, which underpins FastAPI's WebSocket handling.

The error message suggests a violation of the ASGI (Asynchronous Server Gateway Interface) protocol for WebSockets. The protocol dictates that a WebSocket connection, once accepted, can only receive `send` or `close` messages from the application. Attempting to `accept` an already accepted connection is a protocol error.

## 2. Code Investigation

Analysis of the codebase reveals a redundant call to `await websocket.accept()`. The call chain is as follows:

1.  **`backend/app/main.py` (`websocket_endpoint` function):**
    - A WebSocket connection is established.
    - `await websocket.accept()` is called immediately.
    - The connection is then passed to `websocket_service.handle_websocket_connection`.

2.  **`backend/app/services/websocket_service.py` (`handle_websocket_connection` method):**
    - This service method receives the already-accepted WebSocket.
    - It then calls `self.manager.connect` to manage the connection.

3.  **`backend/app/core/websocket_manager.py` (`connect` method):**
    - This method, part of the `WebSocketManager`, receives the WebSocket.
    - It calls `await websocket.accept()` for a *second time*.

This second `accept` call is the direct cause of the `RuntimeError`.

## 3. Root Cause

The application attempts to accept the WebSocket connection at two different points in the code: first in the FastAPI endpoint (`main.py`) and second in the connection manager (`websocket_manager.py`). This double-acceptance violates the ASGI specification.

## 4. Proposed Solution

The responsibility for accepting a WebSocket connection should reside in a single, well-defined location. In this architecture, the `WebSocketManager` is the most logical place to manage the lifecycle of a connection, including its initial acceptance.

Therefore, the solution is to **remove the redundant `await websocket.accept()` call** from the `websocket_endpoint` in `backend/app/main.py`. The `WebSocketManager`'s `connect` method will be solely responsible for accepting the connection.