
import { useEffect, useState } from 'react';

import { handleAnalyticsUpdate } from '../lib/websocket/analytics';
import { handleApplicationStatusUpdate } from '../lib/websocket/applications';
import { handleDashboardUpdate } from '../lib/websocket/dashboard';
import { HealthMonitor } from '../lib/websocket/health';
import { handleNotification } from '../lib/websocket/notifications';
import { Reconnector } from '../lib/websocket/reconnection';

export function useWebSocket(
  url: string,
  onDashboardUpdate: (data: any) => void,
  onApplicationStatusUpdate: (data: any) => void,
  onAnalyticsUpdate: (data: any) => void,
) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState('closed');

  useEffect(() => {
    const connect = async () => {
      setConnectionStatus('connecting');
      try {
        const newWs = new WebSocket(url);
        newWs.onopen = () => setConnectionStatus('open');
        newWs.onclose = () => setConnectionStatus('closed');
        newWs.onmessage = (event) => {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case 'notification':
              handleNotification(data.payload);
              break;
            case 'dashboard-update':
              handleDashboardUpdate(data.payload, onDashboardUpdate);
              break;
            case 'application-status-update':
              handleApplicationStatusUpdate(data.payload, onApplicationStatusUpdate);
              break;
            case 'analytics-update':
              handleAnalyticsUpdate(data.payload, onAnalyticsUpdate);
              break;
            default:
              break;
          }
        };
        setWs(newWs);

        const healthMonitor = new HealthMonitor(newWs);
        healthMonitor.start();

        return () => {
          healthMonitor.stop();
          newWs.close();
        };
      } catch (error) {
        setConnectionStatus('closed');
      }
    };

    const reconnector = new Reconnector(connect);
    reconnector.start();

    return () => {
      reconnector.stop();
    };
  }, [url, onDashboardUpdate, onApplicationStatusUpdate, onAnalyticsUpdate]);

  return { ws, connectionStatus };
}
