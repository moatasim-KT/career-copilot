/**
 * WebSocket Client for Real-time Updates
 * Handles WebSocket connections for live dashboard updates
 */

class WebSocketClient {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.heartbeatInterval = null;
        this.heartbeatIntervalMs = 30000; // 30 seconds
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            // Determine WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const wsUrl = `${protocol}//${host}/ws/dashboard`;

            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = this.onOpen.bind(this);
            this.ws.onmessage = this.onMessage.bind(this);
            this.ws.onclose = this.onClose.bind(this);
            this.ws.onerror = this.onError.bind(this);

        } catch (error) {
            console.warn('WebSocket connection failed:', error.message);
            this.scheduleReconnect();
        }
    }

    /**
     * Handle WebSocket open event
     */
    onOpen() {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.startHeartbeat();
        
        // Send initial subscription message
        this.send({
            type: 'subscribe',
            topics: ['job_updates', 'statistics']
        });
    }

    /**
     * Handle WebSocket message
     */
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        } catch (error) {
            console.warn('Failed to parse WebSocket message:', error.message);
        }
    }

    /**
     * Handle WebSocket close event
     */
    onClose(event) {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.stopHeartbeat();
        
        if (event.code !== 1000) { // Not a normal closure
            this.scheduleReconnect();
        }
    }

    /**
     * Handle WebSocket error
     */
    onError(error) {
        console.error('WebSocket error:', error);
    }

    /**
     * Handle incoming messages
     */
    handleMessage(data) {
        switch (data.type) {
            case 'job_created':
                this.handleJobCreated(data.payload);
                break;
            case 'job_updated':
                this.handleJobUpdated(data.payload);
                break;
            case 'job_deleted':
                this.handleJobDeleted(data.payload);
                break;
            case 'statistics_updated':
                this.handleStatisticsUpdated(data.payload);
                break;
            case 'pong':
                // Heartbeat response
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    /**
     * Handle job created event
     */
    handleJobCreated(job) {
        if (this.dashboard) {
            const transformedJob = this.dashboard.transformJobData(job);
            this.dashboard.jobs.unshift(transformedJob);
            this.dashboard.filteredJobs = [...this.dashboard.jobs];
            this.dashboard.renderJobs();
            this.dashboard.updateStats();
            
            ToastNotification.info('New job opportunity added');
        }
    }

    /**
     * Handle job updated event
     */
    handleJobUpdated(job) {
        if (this.dashboard) {
            const jobIndex = this.dashboard.jobs.findIndex(j => j.id === job.id);
            if (jobIndex !== -1) {
                const transformedJob = this.dashboard.transformJobData(job);
                this.dashboard.jobs[jobIndex] = transformedJob;
                this.dashboard.filteredJobs = [...this.dashboard.jobs];
                this.dashboard.renderJobs();
                this.dashboard.updateStats();
            }
        }
    }

    /**
     * Handle job deleted event
     */
    handleJobDeleted(jobId) {
        if (this.dashboard) {
            this.dashboard.jobs = this.dashboard.jobs.filter(job => job.id !== jobId);
            this.dashboard.filteredJobs = this.dashboard.filteredJobs.filter(job => job.id !== jobId);
            this.dashboard.renderJobs();
            this.dashboard.updateStats();
        }
    }

    /**
     * Handle statistics updated event
     */
    handleStatisticsUpdated(stats) {
        if (this.dashboard) {
            this.dashboard.updateStatsFromAPI(stats);
        }
    }

    /**
     * Send message to WebSocket server
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            this.send({ type: 'ping' });
        }, this.heartbeatIntervalMs);
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('Max WebSocket reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
        
        console.log(`Scheduling WebSocket reconnection in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
    }
}

// Export for use in other modules
window.WebSocketClient = WebSocketClient;