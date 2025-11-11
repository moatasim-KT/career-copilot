# WebSocket Testing Guide

This guide provides instructions for testing the WebSocket real-time functionality in the Career Copilot application.

## Prerequisites

1. Backend server running with WebSocket support at `ws://localhost:8002/ws`
2. Frontend development server running
3. Multiple browser tabs/windows for multi-tab testing
4. Browser DevTools open (Network tab for WebSocket inspection)

## Test Scenarios

### 1. Connection Establishment

**Test:** Verify WebSocket connects on page load

**Steps:**
1. Open the application in a browser
2. Open DevTools → Network tab → WS filter
3. Look for WebSocket connection to `ws://localhost:8002/ws`
4. Check connection status indicator in navigation (should be green)

**Expected Result:**
- WebSocket connection established
- Status indicator shows "Connected" (green dot)
- No errors in console

---

### 2. Real-time Job Recommendations

**Test:** Verify new job notifications appear in real-time

**Steps:**
1. Open the application
2. Trigger a new job recommendation from backend (or use test script)
3. Observe toast notification
4. Check Jobs navigation link for badge count
5. Navigate to Jobs page

**Expected Result:**
- Toast notification appears: "New Job Match!"
- Badge appears on Jobs link with count
- New job appears in jobs list with smooth animation
- Badge clears when Jobs page is visited

**Backend Test Command:**
```python
# Send test job recommendation via WebSocket
await websocket_manager.broadcast({
    "type": "job:recommendation",
    "data": {
        "job": {
            "id": 999,
            "title": "Senior Software Engineer",
            "company": "Test Company",
            "match_score": 95
        },
        "reason": "Matches your skills"
    }
})
```

---

### 3. Real-time Application Status Updates

**Test:** Verify application status changes appear in real-time

**Steps:**
1. Open Applications page
2. Trigger an application status change from backend
3. Observe toast notification
4. Check application card/row for updated status
5. Check dashboard for updated stats

**Expected Result:**
- Toast notification appears with status change
- Application status updates instantly without page refresh
- Dashboard stats update in real-time
- Status badge animates on change

**Backend Test Command:**
```python
# Send test application status change via WebSocket
await websocket_manager.broadcast({
    "type": "application:status_change",
    "data": {
        "application_id": 1,
        "old_status": "applied",
        "new_status": "interview",
        "job_title": "Software Engineer",
        "company": "Tech Corp"
    }
})
```

---

### 4. Real-time Notifications

**Test:** Verify notifications appear in real-time

**Steps:**
1. Open the application
2. Trigger a notification from backend
3. Observe toast notification
4. Check notification bell for badge count
5. Open notification center

**Expected Result:**
- Toast notification appears
- Notification bell badge increments
- Notification appears in notification center
- Sound plays (if enabled in preferences)

**Backend Test Command:**
```python
# Send test notification via WebSocket
await websocket_manager.broadcast({
    "type": "notification:new",
    "data": {
        "id": "test-123",
        "category": "job_alert",
        "title": "New Job Alert",
        "description": "5 new jobs match your profile",
        "timestamp": "2024-01-15T10:30:00Z"
    }
})
```

---

### 5. Connection Status Indicator

**Test:** Verify connection status indicator works correctly

**Steps:**
1. Open the application
2. Observe green dot (connected)
3. Stop backend server
4. Observe status change to yellow (reconnecting) then red (disconnected)
5. Hover over status indicator to see tooltip
6. Click reconnect button
7. Restart backend server
8. Observe reconnection

**Expected Result:**
- Status indicator reflects current connection state
- Tooltip shows appropriate message
- Reconnect button appears when disconnected
- Automatic reconnection works when server is back

---

### 6. Reconnection with Exponential Backoff

**Test:** Verify reconnection attempts with increasing delays

**Steps:**
1. Open the application (connected)
2. Stop backend server
3. Observe reconnection attempts in console
4. Note increasing delay between attempts
5. Restart backend server
6. Verify successful reconnection

**Expected Result:**
- First reconnect attempt after ~1 second
- Second attempt after ~1.5 seconds
- Third attempt after ~2.25 seconds
- Delays increase exponentially up to max (30 seconds)
- Successful reconnection when server is back
- Toast notification: "Reconnected"

**Console Output:**
```
[WebSocket] Connection closed: 1006 - 
[WebSocket] Reconnecting in 1000ms (attempt 1)
[WebSocket] Connecting to ws://localhost:8002/ws
[WebSocket] Connection closed: 1006 - 
[WebSocket] Reconnecting in 1500ms (attempt 2)
...
```

---

### 7. Offline Mode

**Test:** Verify offline mode detection and handling

**Steps:**
1. Open the application (connected)
2. Open DevTools → Network tab
3. Enable "Offline" mode
4. Observe offline banner/toast
5. Try to perform actions
6. Disable "Offline" mode
7. Observe reconnection

**Expected Result:**
- Offline toast appears: "Connection Lost"
- Status indicator shows red (disconnected)
- Actions are queued (if applicable)
- Reconnection toast appears when back online
- Queued messages are sent
- Data resyncs automatically

---

### 8. Multi-tab Synchronization

**Test:** Verify real-time updates work across multiple tabs

**Steps:**
1. Open application in Tab 1
2. Open application in Tab 2
3. Trigger a job recommendation from backend
4. Observe both tabs receive the update
5. Click Jobs link in Tab 1 (clears badge)
6. Verify badge remains in Tab 2 until clicked

**Expected Result:**
- Both tabs receive real-time updates
- Toast notifications appear in both tabs
- Badge counts are independent per tab
- No duplicate WebSocket connections (check Network tab)

---

### 9. Message Queue

**Test:** Verify messages are queued when offline and sent on reconnect

**Steps:**
1. Open the application
2. Disconnect from network (or stop backend)
3. Trigger actions that would send WebSocket messages
4. Reconnect to network (or start backend)
5. Verify queued messages are sent

**Expected Result:**
- Messages are queued while offline
- Queue is processed on reconnection
- No messages are lost
- Console shows: "Processing X queued messages"

---

### 10. Mobile Device Testing

**Test:** Verify WebSocket works on mobile devices

**Steps:**
1. Open application on mobile device (or use DevTools device emulation)
2. Test connection establishment
3. Test real-time updates
4. Test reconnection when switching networks (WiFi ↔ Cellular)
5. Test app backgrounding and foregrounding

**Expected Result:**
- WebSocket connects on mobile
- Real-time updates work
- Reconnection works when network changes
- Connection resumes when app is foregrounded

---

### 11. Slow Network Testing

**Test:** Verify WebSocket works on slow networks

**Steps:**
1. Open DevTools → Network tab
2. Enable network throttling (Slow 3G)
3. Open the application
4. Observe connection establishment
5. Test real-time updates
6. Test reconnection

**Expected Result:**
- Connection establishes (may take longer)
- Real-time updates work (with delay)
- Reconnection works
- No timeout errors

---

### 12. Heartbeat/Ping-Pong

**Test:** Verify heartbeat keeps connection alive

**Steps:**
1. Open the application
2. Let it sit idle for 5+ minutes
3. Observe WebSocket connection in DevTools
4. Trigger a real-time update
5. Verify update is received

**Expected Result:**
- Connection stays alive
- Ping messages sent every 30 seconds
- Pong responses received
- Real-time updates still work after idle period

---

## Automated Testing

Run the automated tests:

```bash
cd frontend
npm test -- websocket.test.ts
```

## Performance Testing

### Connection Overhead

1. Open DevTools → Performance tab
2. Start recording
3. Refresh page
4. Stop recording
5. Analyze WebSocket connection time

**Target:** < 100ms to establish connection

### Message Latency

1. Send a test message from backend
2. Measure time until toast appears
3. Repeat 10 times and calculate average

**Target:** < 200ms latency

### Memory Usage

1. Open DevTools → Memory tab
2. Take heap snapshot
3. Let application run for 30 minutes with frequent updates
4. Take another heap snapshot
5. Compare memory usage

**Target:** No significant memory leaks

---

## Troubleshooting

### WebSocket Not Connecting

**Check:**
- Backend server is running
- WebSocket URL is correct (`NEXT_PUBLIC_WS_URL`)
- No CORS issues
- Firewall/proxy not blocking WebSocket

**Console Errors:**
```
[WebSocket] Connection error: ...
```

### Real-time Updates Not Appearing

**Check:**
- WebSocket is connected (green status indicator)
- Event handlers are subscribed
- Backend is sending correct event types
- No JavaScript errors in console

### Reconnection Not Working

**Check:**
- `maxReconnectAttempts` not exceeded
- Backend server is actually running
- Network is actually online
- No manual disconnect was triggered

---

## Backend WebSocket Test Server

If you need to test without the full backend, here's a simple test server:

```python
# test_ws_server.py
import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    try:
        # Send test messages periodically
        while True:
            await asyncio.sleep(10)
            
            # Send test job recommendation
            await websocket.send_json({
                "type": "job:recommendation",
                "data": {
                    "job": {
                        "id": 999,
                        "title": "Test Job",
                        "company": "Test Company",
                        "match_score": 95
                    }
                }
            })
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

Run with:
```bash
python test_ws_server.py
```

---

## Success Criteria

All tests should pass with:
- ✅ WebSocket connects successfully
- ✅ Real-time updates appear instantly
- ✅ Reconnection works automatically
- ✅ Offline mode is detected and handled
- ✅ Multi-tab updates work
- ✅ No memory leaks
- ✅ Works on mobile devices
- ✅ Works on slow networks

---

## Notes

- WebSocket URL is configured via `NEXT_PUBLIC_WS_URL` environment variable
- Default: `ws://localhost:8002/ws`
- Production: Should use `wss://` (secure WebSocket)
- Connection status is persisted across page reloads
- Message queue has a max size of 100 messages
