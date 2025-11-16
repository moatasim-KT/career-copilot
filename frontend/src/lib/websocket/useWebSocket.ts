/**
 * React hook for WebSocket connection
 * 
 * Usage:
 * ```tsx
 * const { connected, send, on } = useWebSocket();
 * 
 * useEffect(() => {
 *   const unsubscribe = on('notification', (data) => {
 *     logger.info('Received notification:', data);
 *   });
 *   
 *   return unsubscribe;
 * }, [on]);
 * 
 * const handleSend = () => {
 *   send('message', { text: 'Hello!' });
 * };
 * ```
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';

import { getWebSocketService } from './service';
import type { WebSocketService } from './service';


interface UseWebSocketReturn {
    connected: boolean;
    connecting: boolean;
    error: Event | null;
    reconnectAttempts: number;
    send: (type: string, data?: any) => void;
    on: (type: string, handler: (data: any) => void) => () => void;
    connect: () => void;
    disconnect: () => void;
}

export function useWebSocket(autoConnect: boolean = true): UseWebSocketReturn {
    const [connected, setConnected] = useState(false);
    const [connecting, setConnecting] = useState(false);
    const [error, setError] = useState<Event | null>(null);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    const serviceRef = useRef<WebSocketService | null>(null);
    const unsubscribersRef = useRef<(() => void)[]>([]);

    // Initialize service
    useEffect(() => {
        serviceRef.current = getWebSocketService();

        return () => {
            // Cleanup on unmount
            unsubscribersRef.current.forEach(unsub => unsub());
            unsubscribersRef.current = [];
        };
    }, []);

    // Set up event listeners
    useEffect(() => {
        if (!serviceRef.current) return;

        const service = serviceRef.current;

        const unsubConnect = service.onConnect(() => {
            setConnected(true);
            setConnecting(false);
            setError(null);
            setReconnectAttempts(0);
        });

        const unsubDisconnect = service.onDisconnect(() => {
            setConnected(false);
            setReconnectAttempts(service.getReconnectAttempts());
        });

        const unsubError = service.onError((err) => {
            setError(err);
            setConnecting(false);
        });

        unsubscribersRef.current.push(unsubConnect, unsubDisconnect, unsubError);

        return () => {
            unsubConnect();
            unsubDisconnect();
            unsubError();
        };
    }, []);

    // Auto-connect
    useEffect(() => {
        if (!autoConnect || !serviceRef.current) return;

        const token = localStorage.getItem('token');
        if (token && !serviceRef.current.isConnected()) {
            setConnecting(true);
            serviceRef.current.connect(token);
        }
    }, [autoConnect]);

    const send = useCallback((type: string, data: any = {}) => {
        serviceRef.current?.send(type, data);
    }, []);

    const on = useCallback((type: string, handler: (data: any) => void) => {
        if (!serviceRef.current) {
            return () => { };
        }
        return serviceRef.current.on(type, handler);
    }, []);

    const connect = useCallback(() => {
        if (!serviceRef.current) return;

        const token = localStorage.getItem('token');
        if (token) {
            setConnecting(true);
            serviceRef.current.connect(token);
        }
    }, []);

    const disconnect = useCallback(() => {
        if (!serviceRef.current) return;
        serviceRef.current.disconnect();
        setConnected(false);
        setConnecting(false);
    }, []);

    return {
        connected,
        connecting,
        error,
        reconnectAttempts,
        send,
        on,
        connect,
        disconnect,
    };
}
