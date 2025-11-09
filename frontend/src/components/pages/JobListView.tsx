import { motion, AnimatePresence } from 'framer-motion';
import React from 'react';

import JobCard from '@/components/ui/JobCard';
import { staggerContainer, staggerItem } from '@/lib/animations';
// use a loose type here to accommodate shapes from API and the UI JobCard
type AnyJob = any;

interface JobListViewProps {
  jobs: AnyJob[];
  onJobClick: (jobId: number) => void;
  selectedJobIds: number[];
  onSelectJob: (jobId: number) => void;
}

export function JobListView({ jobs, onJobClick, selectedJobIds, onSelectJob }: JobListViewProps) {
  if (jobs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No jobs found. Adjust your filters or search criteria.
      </div>
    );
  }

  return (
    <motion.div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      <AnimatePresence>
        {jobs.map((job) => (
          <motion.div key={job.id} variants={staggerItem} layout onClick={() => onJobClick(job.id)}>
            <JobCard
              job={job}
              isSelected={selectedJobIds.includes(job.id)}
              onSelect={() => onSelectJob(job.id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
