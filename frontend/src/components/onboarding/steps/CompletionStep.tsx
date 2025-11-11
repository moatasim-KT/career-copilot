
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { motion } from 'framer-motion';
import apiClient from '@/lib/api/client';
import { Job } from '@/types/job'; // Assuming Job type exists

const CompletionStep = () => {
  const [recommendedJobs, setRecommendedJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendedJobs = async () => {
      try {
        const response = await apiClient.get('/jobs/recommended?limit=3');
        setRecommendedJobs(response.data);
      } catch (error) {
        console.error('Failed to fetch recommended jobs:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchRecommendedJobs();
  }, []);

  return (
    <div className="text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 260, damping: 20 }}
      >
        <svg className="w-24 h-24 mx-auto text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </motion.div>
      <h2 className="mt-4 text-2xl font-bold">You're all set!</h2>
      <p className="mt-2 text-gray-600">
        You can now start exploring job opportunities.
      </p>
      
      <div className="mt-8">
        <h3 className="text-xl font-semibold">Here are some jobs we think you'll like:</h3>
        {isLoading ? (
          <p className="mt-4">Loading recommended jobs...</p>
        ) : (
          <div className="mt-4 space-y-4">
            {recommendedJobs.map(job => (
              <div key={job.id} className="p-4 border rounded-lg text-left">
                <h4 className="font-bold">{job.title}</h4>
                <p className="text-sm text-gray-600">{job.company.name} - {job.location}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 flex justify-center space-x-4">
        <Button>View Dashboard</Button>
        <Button variant="outline">Browse Jobs</Button>
      </div>
    </div>
  );
};

export default CompletionStep;
