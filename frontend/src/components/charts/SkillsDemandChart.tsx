
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
} from 'recharts';
import ChartWrapper from './ChartWrapper';
import apiClient from '@/lib/api/client';
import { Button } from '../ui/Button';

interface SkillsDemandData {
  skill: string;
  demand: number;
  userHasSkill: boolean;
}

const SkillsDemandChart = () => {
  const [data, setData] = useState<SkillsDemandData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [sortBy, setSortBy] = useState<'demand' | 'skill'>('demand');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/analytics/skills-demand');
        setData(response.data);
      } catch (err) {
        setError(true);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const sortedData = [...data].sort((a, b) => {
    if (sortBy === 'demand') {
      return b.demand - a.demand;
    }
    return a.skill.localeCompare(b.skill);
  });

  return (
    <ChartWrapper
      title="Skills Demand"
      isLoading={isLoading}
      error={error}
    >
      <div className="flex justify-end space-x-2 mb-4">
        <Button size="sm" onClick={() => setSortBy('demand')} disabled={sortBy === 'demand'}>Sort by Demand</Button>
        <Button size="sm" onClick={() => setSortBy('skill')} disabled={sortBy === 'skill'}>Sort by Name</Button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={sortedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="skill" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="demand" fill="#8884d8" onClick={(data) => console.log(`Clicked on ${data.skill}`)}>
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.userHasSkill ? '#82ca9d' : '#8884d8'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
};

export default SkillsDemandChart;
