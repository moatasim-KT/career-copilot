/**
 * WebSocket Test Component
 * For testing real-time functionality during development
 */

'use client';

import { Send, Trash2, Wifi, WifiOff } from 'lucide-react';
import { useState, useEffect } from 'react';

import Card from '@/components/ui/Card2';
import { webSocketService } from '@/lib/api/websocket';
import { logger } from '@/lib/logger';

import Button2 from '../ui/Button2';

interface TestMessage {
  id: string;
  timestamp: Date;
  type: string;
  data: unknown;
}

export default function WebSocketTest() {
  const [messages, setMessages] = useState<TestMessage[]>([]);
  const [testMessage, setTestMessage] = useState('');
  const [wsUrl] = useState('ws://localhost:8002/ws');

  const [connectionStatus, setConnectionStatus] = useState(webSocketService.getStatus());

  useEffect(() => {
    const updateStatus = () => setConnectionStatus(webSocketService.getStatus());

    webSocketService.on('connected', updateStatus);
    webSocketService.on('disconnected', updateStatus);
    webSocketService.on('reconnecting', updateStatus);

    const onDashboardUpdate = (data: any) => {
      logger.log('WebSocket Test: Dashboard update', data);
      addMessage('dashboard-update', data);
    };

    const onApplicationStatus = (data: any) => {
      logger.log('WebSocket Test: Application status update', data);
      addMessage('application-status-update', data);
    };

    const onAnalyticsUpdate = (data: any) => {
      logger.log('WebSocket Test: Analytics update', data);
      addMessage('analytics-update', data);
    };

    // Assuming 'dashboard:update' exists, or maybe it's just analytics
    webSocketService.on('dashboard:update', onDashboardUpdate);
    webSocketService.on('application:status', onApplicationStatus);
    webSocketService.on('analytics:update', onAnalyticsUpdate);

    return () => {
      webSocketService.off('connected', updateStatus);
      webSocketService.off('disconnected', updateStatus);
      webSocketService.off('reconnecting', updateStatus);

      webSocketService.off('dashboard:update', onDashboardUpdate);
      webSocketService.off('application:status', onApplicationStatus);
      webSocketService.off('analytics:update', onAnalyticsUpdate);
    };
  }, []);

  const connected = connectionStatus === 'connected';
  const connecting = connectionStatus === 'connecting';

  const addMessage = (type: string, data: unknown) => {
    const newMessage: TestMessage = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      type,
      data,
    };
    setMessages(prev => [newMessage, ...prev.slice(0, 49)]); // Keep last 50 messages
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const sendTestMessage = () => {
    if (testMessage.trim()) {
      // This would send a message to the server if we had that functionality
      addMessage('test_sent', { message: testMessage });
      setTestMessage('');
    }
  };

  const testJobMatch = () => {
    // Simulate a job match notification
    const mockJobMatch = {
      type: 'job_match',
      job: {
        id: Math.floor(Math.random() * 1000),
        title: 'Senior React Developer',
        company: 'Tech Corp',
        location: 'San Francisco, CA',
        tech_stack: ['React', 'TypeScript', 'Node.js'],
      },
      match_score: 85.5,
      timestamp: new Date().toISOString(),
      message:
        'New job match found: Senior React Developer at Tech Corp (Score: 85.5%)',
    };
    addMessage('job_match', mockJobMatch);
  };

  const testApplicationUpdate = () => {
    // Simulate an application status update
    const mockUpdate = {
      type: 'application_status_update',
      application: {
        id: Math.floor(Math.random() * 1000),
        job_title: 'Frontend Developer',
        job_company: 'StartupXYZ',
        status: 'interview',
        old_status: 'applied',
      },
      timestamp: new Date().toISOString(),
      message: 'Application status updated: interview',
    };
    addMessage('application_status_update', mockUpdate);
  };

  const testAnalyticsUpdate = () => {
    // Simulate analytics update
    const mockAnalytics = {
      type: 'analytics_update',
      analytics: {
        total_jobs: 45,
        total_applications: 12,
        interviews_scheduled: 3,
        offers_received: 1,
      },
      timestamp: new Date().toISOString(),
      message: 'Analytics data updated',
    };
    addMessage('analytics_update', mockAnalytics);
  };

  const getStatusColor = () => {
    if (connected) return 'text-green-600';
    if (connecting) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusIcon = () => {
    if (connected) return <Wifi className="h-4 w-4" />;
    if (connecting)
      return (
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
      );
    return <WifiOff className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">WebSocket Test Console</h2>
            <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
              {getStatusIcon()}
              <span className="text-sm font-medium">
                {connected
                  ? 'Connected'
                  : connecting
                    ? 'Connecting...'
                    : 'Disconnected'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-neutral-700">Connection Control</h3>
              <div className="flex space-x-2">
                <Button2 onClick={() => webSocketService.disconnect()} disabled={!connected} variant="outline" size="sm">
                  Disconnect
                </Button2>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium text-neutral-700">Test Notifications</h3>
              <div className="flex flex-wrap gap-2">
                <Button2 onClick={testJobMatch} size="sm" variant="outline">
                  Job Match
                </Button2>
                <Button2 onClick={testApplicationUpdate} size="sm" variant="outline">
                  App Update
                </Button2>
                <Button2 onClick={testAnalyticsUpdate} size="sm" variant="outline">
                  Analytics
                </Button2>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2 mb-4">
            <input
              type="text"
              value={testMessage}
              onChange={e => setTestMessage(e.target.value)}
              placeholder="Enter test message..."
              className="flex-1 px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={e => e.key === 'Enter' && sendTestMessage()}
            />
            <Button2 onClick={sendTestMessage} size="sm">
              <Send className="h-4 w-4" />
            </Button2>
            <Button2 onClick={clearMessages} size="sm" variant="outline">
              <Trash2 className="h-4 w-4" />
            </Button2>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Message Log</h3>
            <span className="text-sm text-neutral-500">{messages.length} messages</span>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-neutral-500">
                No messages yet. Connect to start receiving messages.
              </div>
            ) : (
              messages.map(message => (
                <div
                  key={message.id}
                  className="p-3 bg-neutral-50 rounded-lg border-l-4 border-blue-500"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-neutral-900">
                      {message.type}
                    </span>
                    <span className="text-xs text-neutral-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <pre className="text-xs text-neutral-700 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(message.data, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}