
import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import ChartWrapper from './ChartWrapper';
import apiClient from '@/lib/api/client';
import { Button } from '../ui/Button';

interface SalaryDistributionData {
  range: string;
  count: number;
}

const SalaryDistributionChart = ({ userTargetSalary }: { userTargetSalary: number }) => {
  const [data, setData] = useState<SalaryDistributionData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showLegend, setShowLegend] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/analytics/salary-distribution');
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
      title="Salary Distribution"
      isLoading={isLoading}
      error={error}
    >
      <div className="flex justify-end mb-4">
        <Button size="sm" onClick={() => setShowLegend(!showLegend)}>
          {showLegend ? 'Hide Legend' : 'Show Legend'}
        </Button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" />
          <YAxis />
          <Tooltip />
          {showLegend && <Legend />}
          <Bar dataKey="count" fill="#8884d8" />
          {userTargetSalary && (
            <ReferenceLine
              y={userTargetSalary}
              label="Your Target"
              stroke="red"
              strokeDasharray="3 3"
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
};

export default SalaryDistributionChart;
