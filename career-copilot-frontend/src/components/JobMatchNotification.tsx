
'use client';

import React, { useEffect } from 'react';
import { useNotification } from './NotificationProvider';

interface JobMatchNotificationProps {
  jobTitle: string;
  company: string;
  link: string;
}

const JobMatchNotification = ({ jobTitle, company, link }: JobMatchNotificationProps) => {
  const { showNotification } = useNotification();

  useEffect(() => {
    showNotification({
      message: `New Job Match: ${jobTitle} at ${company}!`, 
      type: 'success'
    });
  }, [jobTitle, company, showNotification]);

  return null; // This component doesn't render anything directly, it just triggers a notification
};

export default JobMatchNotification;
