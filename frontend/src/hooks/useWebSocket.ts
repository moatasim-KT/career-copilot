
import { useEffect, useRef, useState } from 'react';

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

  // keep latest callbacks in refs so the main connection effect doesn't
  // re-run when parent re-creates handlers. This prevents an effect loop
  // where reconnect is started repeatedly.
  const dashboardRef = useRef(onDashboardUpdate);
  const applicationRef = useRef(onApplicationStatusUpdate);
  const analyticsRef = useRef(onAnalyticsUpdate);

  // keep refs up to date without re-running connection logic
  useEffect(() => {
    dashboardRef.current = onDashboardUpdate;
  }, [onDashboardUpdate]);
  useEffect(() => {
    applicationRef.current = onApplicationStatusUpdate;
  }, [onApplicationStatusUpdate]);
  useEffect(() => {
    analyticsRef.current = onAnalyticsUpdate;
  }, [onAnalyticsUpdate]);

  useEffect(() => {
    let stopped = false;
    let closeCurrent: (() => void) | null = null;

    const connect = async () => {
      setConnectionStatus('connecting');
      try {
        const newWs = new WebSocket(url);
        newWs.onopen = () => setConnectionStatus('open');
        newWs.onclose = () => setConnectionStatus('closed');
        newWs.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            switch (data.type) {
              case 'notification':
                handleNotification(data.payload);
                break;
              case 'dashboard-update':
                dashboardRef.current?.(data.payload);
                break;
              case 'application-status-update':
                applicationRef.current?.(data.payload);
                break;
              case 'analytics-update':
                analyticsRef.current?.(data.payload);
                break;
              default:
                break;
            }
          } catch (err) {
            // ignore malformed messages
          }
        };
        if (stopped) {
          newWs.close();
          return;
        }
        setWs(newWs);

        const healthMonitor = new HealthMonitor(newWs);
        healthMonitor.start();

        closeCurrent = () => {
          try {
            healthMonitor.stop();
          } catch (_e) {
            // ignore errors during shutdown
          }
          try {
            newWs.close();
          } catch (_e) {
            // ignore errors during shutdown
          }
          setWs(null);
        };
      } catch (error) {
        setConnectionStatus('closed');
      }
    };

    const reconnector = new Reconnector(async () => {
      // The Reconnector expects a connect function that returns Promise<void>.
      await connect();
    });
    reconnector.start();

    return () => {
      stopped = true;
      reconnector.stop();
      if (closeCurrent) closeCurrent();
    };
    // only re-run when URL changes. callbacks are read from refs.
  }, [url]);

  return { ws, connectionStatus };
}
