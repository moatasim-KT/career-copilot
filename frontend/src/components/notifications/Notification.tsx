'use client';

import { XCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';

interface NotificationProps {
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number; // in milliseconds, 0 for sticky
  onClose?: () => void;
}

const iconMap = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: AlertTriangle,
};

const colorMap = {
  success: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-800',
    icon: 'text-green-400',
  },
  error: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-800',
    icon: 'text-red-400',
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    icon: 'text-blue-400',
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-800',
    icon: 'text-yellow-400',
  },
};

export default function Notification({
  message,
  type = 'info',
  duration = 5000,
  onClose,
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(true);
  const Icon = iconMap[type];
  const colors = colorMap[type];

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        if (onClose) onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  if (!isVisible) return null;

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 p-4 rounded-lg shadow-lg flex items-center space-x-3 ${colors.bg} ${colors.border} border`}
      role="alert"
    >
      <Icon className={`h-6 w-6 flex-shrink-0 ${colors.icon}`} aria-hidden="true" />
      <p className={`text-sm font-medium ${colors.text}`}>{message}</p>
      <button
        onClick={() => {
          setIsVisible(false);
          if (onClose) onClose();
        }}
        className={`ml-auto -mx-1.5 -my-1.5 ${colors.text} rounded-lg focus:ring-2 focus:ring-offset-2 focus:ring-offset-white p-1.5 hover:${colors.bg} inline-flex h-8 w-8`}
      >
        <span className="sr-only">Dismiss</span>
        <XCircle className="h-5 w-5" />
      </button>
    </div>
  );
}
