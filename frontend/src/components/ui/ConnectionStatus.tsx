
import React, { useState, useEffect } from 'react';
import { webSocketService } from '@/lib/api/websocket';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/Tooltip';
import { Button } from '@/components/ui/Button';

const ConnectionStatus = () => {
  const [status, setStatus] = useState<'healthy' | 'degraded' | 'disconnected'>('disconnected');
  const [connectionInfo, setConnectionInfo] = useState(webSocketService.getConnectionInfo());

  useEffect(() => {
    const updateStatus = () => {
      setStatus(webSocketService.getHealthStatus());
      setConnectionInfo(webSocketService.getConnectionInfo());
    };

    const interval = setInterval(updateStatus, 5000); // Update every 5 seconds
    webSocketService.on('connected', updateStatus);
    webSocketService.on('disconnected', updateStatus);
    webSocketService.on('reconnecting', updateStatus);

    return () => {
      clearInterval(interval);
      webSocketService.off('connected', updateStatus);
      webSocketService.off('disconnected', updateStatus);
      webSocketService.off('reconnecting', updateStatus);
    };
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'disconnected':
        return 'text-red-500';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy':
        return <Wifi className={`h-5 w-5 ${getStatusColor()}`} />;
      case 'degraded':
        return <Wifi className={`h-5 w-5 ${getStatusColor()}`} />;
      case 'disconnected':
        return <WifiOff className={`h-5 w-5 ${getStatusColor()}`} />;
    }
  };

  const handleReconnect = () => {
    webSocketService.reconnect();
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className={`text-sm ${getStatusColor()}`}>{status}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Status: {status}</p>
          <p>Reconnect attempts: {connectionInfo.reconnectAttempts}</p>
          {status === 'disconnected' && (
            <Button size="sm" onClick={handleReconnect} className="mt-2">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reconnect
            </Button>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ConnectionStatus;
