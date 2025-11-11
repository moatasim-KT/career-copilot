
import React, { useState, useEffect } from 'react';
import { FunnelChart, Funnel, Tooltip, LabelList, ResponsiveContainer } from 'recharts';
import ChartWrapper from './ChartWrapper';
import apiClient from '@/lib/api/client';

interface SuccessRateData {
  name: string;
  value: number;
}

const SuccessRateChart = () => {
  const [data, setData] = useState<SuccessRateData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/analytics/success-rate');
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
      title="Application Success Rate"
      isLoading={isLoading}
      error={error}
    >
      <ResponsiveContainer width="100%" height={300}>
        <FunnelChart>
          <Tooltip />
          <Funnel dataKey="value" data={data} isAnimationActive>
            <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
};

export default SuccessRateChart;
