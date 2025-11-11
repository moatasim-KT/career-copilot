
import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import ChartWrapper from './ChartWrapper';
import apiClient from '@/lib/api/client';
import { Button } from '../ui/Button';

interface ApplicationTimelineData {
  date: string;
  count: number;
}

const ApplicationTimelineChart = () => {
  const [data, setData] = useState<ApplicationTimelineData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showLegend, setShowLegend] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/analytics/application-timeline');
        setData(response.data);
      } catch (err) {
        setError(true);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <ChartWrapper
      title="Application Timeline"
      isLoading={isLoading}
      error={error}
    >
      <div className="flex justify-end mb-4">
        <Button size="sm" onClick={() => setShowLegend(!showLegend)}>
          {showLegend ? 'Hide Legend' : 'Show Legend'}
        </Button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          {showLegend && <Legend />}
          <Line
            type="monotone"
            dataKey="count"
            stroke="#8884d8"
            activeDot={{ r: 8 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
};

export default ApplicationTimelineChart;
