'use client';

import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { webSocketService } from '@/lib/api/websocket';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

/**
 * ConnectionStatus Component
 * 
 * Displays a small indicator showing the WebSocket connection status
 * - Connected: Green dot
 * - Connecting/Reconnecting: Yellow dot with pulse animation
 * - Disconnected: Red dot
 * 
 * Features:
 * - Tooltip with status message
 * - Manual reconnect button
 * - Smooth animations
 * - Accessible
 */

interface ConnectionStatusProps {
  className?: string;
  showLabel?: boolean;
}

export function ConnectionStatus({ className, showLabel = false }: ConnectionStatusProps) {
  const [status, setStatus] = useState<'connected' | 'connecting' | 'reconnecting' | 'disconnected'>('disconnected');
  const [isTooltipVisible, setIsTooltipVisible] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  useEffect(() => {
    // Set initial status
    setStatus(webSocketService.getStatus());

    // Subscribe to status changes
    const handleConnected = () => setStatus('connected');
    const handleDisconnected = () => setStatus('disconnected');
    const handleReconnecting = () => setStatus('reconnecting');
    const handleError = () => setStatus('disconnected');

    webSocketService.on('connected', handleConnected);
    webSocketService.on('disconnected', handleDisconnected);
    webSocketService.on('reconnecting', handleReconnecting);
    webSocketService.on('error', handleError);

    return () => {
      webSocketService.off('connected', handleConnected);
      webSocketService.off('disconnected', handleDisconnected);
      webSocketService.off('reconnecting', handleReconnecting);
      webSocketService.off('error', handleError);
    };
  }, []);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await webSocketService.reconnect();
    } catch (error) {
      console.error('Manual reconnection failed:', error);
    } finally {
      // Reset reconnecting state after 2 seconds
      setTimeout(() => {
        setIsReconnecting(false);
      }, 2000);
    }
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500',
          icon: Wifi,
          label: 'Connected',
          message: 'Real-time updates active',
          pulse: false,
        };
      case 'connecting':
        return {
          color: 'bg-yellow-500',
          icon: RefreshCw,
          label: 'Connecting',
          message: 'Establishing connection...',
          pulse: true,
        };
      case 'reconnecting':
        return {
          color: 'bg-yellow-500',
          icon: RefreshCw,
          label: 'Reconnecting',
          message: 'Attempting to reconnect...',
          pulse: true,
        };
      case 'disconnected':
        return {
          color: 'bg-red-500',
          icon: WifiOff,
          label: 'Disconnected',
          message: 'Real-time updates unavailable',
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;
  const showReconnectButton = status === 'disconnected';

  return (
    <div
      className={cn('relative flex items-center gap-2', className)}
      onMouseEnter={() => setIsTooltipVisible(true)}
      onMouseLeave={() => setIsTooltipVisible(false)}
    >
      {/* Status Indicator */}
      <div className="relative flex items-center gap-2">
        {/* Dot indicator */}
        <div className="relative">
          <div
            className={cn(
              'w-2 h-2 rounded-full transition-colors duration-200',
              config.color,
            )}
          />
          {/* Pulse animation for connecting/reconnecting */}
          {config.pulse && (
            <m.div
              className={cn('absolute inset-0 rounded-full', config.color)}
              initial={{ scale: 1, opacity: 0.5 }}
              animate={{ scale: 2, opacity: 0 }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'easeOut',
              }}
            />
          )}
        </div>

        {/* Label (optional) */}
        {showLabel && (
          <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
            {config.label}
          </span>
        )}
      </div>

      {/* Reconnect Button */}
      {showReconnectButton && (
        <button
          onClick={handleReconnect}
          disabled={isReconnecting}
          className={cn(
            'p-1 rounded-md transition-colors',
            'text-neutral-600 dark:text-neutral-400',
            'hover:text-neutral-900 dark:hover:text-neutral-100',
            'hover:bg-neutral-100 dark:hover:bg-neutral-800',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
          aria-label="Reconnect"
          title="Reconnect"
        >
          <RefreshCw
            className={cn(
              'h-3.5 w-3.5',
              isReconnecting && 'animate-spin',
            )}
          />
        </button>
      )}

      {/* Tooltip */}
      <AnimatePresence>
        {isTooltipVisible && (
          <m.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.15 }}
            className={cn(
              'absolute top-full right-0 mt-2 z-50',
              'px-3 py-2 rounded-md shadow-lg',
              'bg-neutral-900 dark:bg-neutral-800',
              'border border-neutral-700',
              'min-w-[200px]',
            )}
            role="tooltip"
          >
            {/* Arrow */}
            <div
              className={cn(
                'absolute -top-1 right-4',
                'w-2 h-2 rotate-45',
                'bg-neutral-900 dark:bg-neutral-800',
                'border-l border-t border-neutral-700',
              )}
            />

            {/* Content */}
            <div className="relative flex items-start gap-2">
              <Icon className="h-4 w-4 text-neutral-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-medium text-white">
                  {config.label}
                </div>
                <div className="text-xs text-neutral-400 mt-0.5">
                  {config.message}
                </div>
                {showReconnectButton && (
                  <button
                    onClick={handleReconnect}
                    disabled={isReconnecting}
                    className={cn(
                      'mt-2 text-xs font-medium',
                      'text-primary-400 hover:text-primary-300',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                    )}
                  >
                    {isReconnecting ? 'Reconnecting...' : 'Reconnect now'}
                  </button>
                )}
              </div>
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Compact version for mobile or space-constrained layouts
 */
export function ConnectionStatusCompact({ className }: { className?: string }) {
  const { isAuthenticated } = useAuth();

  // Don't show connection status on login/public pages
  if (!isAuthenticated) {
    return null;
  }

  return <ConnectionStatus className={className} showLabel={false} />;
}

/**
 * Full version with label
 */
export function ConnectionStatusFull({ className }: { className?: string }) {
  return <ConnectionStatus className={className} showLabel={true} />;
}
