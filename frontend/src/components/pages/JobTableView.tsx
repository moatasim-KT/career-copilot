import React from 'react';
import { Job } from '@/lib/api';

interface JobTableViewProps {
  jobs: Job[];
  onJobClick: (jobId: number) => void;
}

export function JobTableView({ jobs, onJobClick }: JobTableViewProps) {
  if (jobs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No jobs found. Adjust your filters or search criteria.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Title
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Company
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Location
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Job Type
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Source
            </th>
            <th scope="col" className="relative px-6 py-3">
              <span className="sr-only">View</span>
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {jobs.map((job) => (
            <tr key={job.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => onJobClick(job.id)}>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {job.title}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.company}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.location || 'N/A'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.job_type}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {job.source}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button onClick={() => onJobClick(job.id)} className="text-blue-600 hover:text-blue-900">
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
