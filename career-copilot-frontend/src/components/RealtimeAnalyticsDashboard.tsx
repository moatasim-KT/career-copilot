
'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';

interface AnalyticsData {
  totalJobs: number;
  totalApplications: number;
  // Add more analytics data fields as needed
}

const RealtimeAnalyticsDashboard = () => {
  const { token } = useAuth();
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    if (token) {
      const ws = new WebSocket(`ws://localhost:8002/ws/${token}`);

      ws.onopen = () => {
        console.log('Analytics WebSocket connection established');
      };

      ws.onmessage = (event) => {
        console.log('Analytics WebSocket message received:', event.data);
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'analytics_update') {
            setAnalyticsData(data.payload);
          }
        } catch (error) {
          console.error('Error parsing analytics WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('Analytics WebSocket connection closed');
      };

      ws.onerror = (error) => {
        console.error('Analytics WebSocket error:', error);
      };

      return () => {
        ws.close();
      };
    }
  }, [token]);

  return (
    <div className="p-4 bg-white shadow rounded-lg">
      <h2 className="text-xl font-bold mb-4">Real-time Analytics Dashboard</h2>
      {analyticsData ? (
        <div>
          <p>Total Jobs: {analyticsData.totalJobs}</p>
          <p>Total Applications: {analyticsData.totalApplications}</p>
          {/* Render charts and other analytics here */}
        </div>
      ) : (
        <p>Loading analytics data...</p>
      )}
    </div>
  );
};

export default RealtimeAnalyticsDashboard;
