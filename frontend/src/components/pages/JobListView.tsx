import React from 'react';
import { Job } from '@/lib/api';
import JobCard from '@/components/ui/JobCard';

interface JobListViewProps {
  jobs: Job[];
  onJobClick: (jobId: number) => void;
}

export function JobListView({ jobs, onJobClick }: JobListViewProps) {
  if (jobs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No jobs found. Adjust your filters or search criteria.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} onClick={() => onJobClick(job.id)} />
      ))}
    </div>
  );
}
