
'use client';

import React from 'react';
import { useNotification } from './NotificationProvider';

const Notification = () => {
  const { notification, hideNotification } = useNotification();

  if (!notification) {
    return null;
  }

  const baseClasses = 'p-4 rounded-md shadow-lg text-white';
  const typeClasses = {
    info: 'bg-blue-500',
    error: 'bg-red-500',
    success: 'bg-green-500',
  };

  return (
    <div className={`fixed top-5 right-5 ${baseClasses} ${typeClasses[notification.type]}`}>
      <div className="flex justify-between items-center">
        <span>{notification.message}</span>
        <button onClick={hideNotification} className="ml-4 text-white font-bold">X</button>
      </div>
    </div>
  );
};

export default Notification;
