
import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import ChartWrapper from './ChartWrapper';
import apiClient from '@/lib/api/client';

interface ApplicationStatusData {
  name: string;
  value: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const ApplicationStatusChart = () => {
  const [data, setData] = useState<ApplicationStatusData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/analytics/application-status');
        setData(response.data);
      } catch (err) {
        setError(true);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handlePieClick = (data: any, index: number) => {
    console.log(`Clicked on ${data.name} at index ${index}`);
    // Implement click functionality, e.g., navigate to a filtered list
  };

  return (
    <ChartWrapper
      title="Application Status"
      isLoading={isLoading}
      error={error}
    >
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            onClick={handlePieClick}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
};

export default ApplicationStatusChart;
