import React from 'react';

import JobCard from '@/components/ui/JobCard';
import { staggerContainer, staggerItem, fadeVariants } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
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
      <m.div 
        className="text-center py-8 text-gray-500"
        variants={fadeVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        No jobs found. Adjust your filters or search criteria.
      </m.div>
    );
  }

  return (
    <m.div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      exit="hidden"
    >
      <AnimatePresence mode="popLayout">
        {jobs.map((job) => (
          <m.div 
            key={job.id} 
            variants={staggerItem}
            layout
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
            onClick={() => onJobClick(job.id)}
          >
            <JobCard
              job={job}
              isSelected={selectedJobIds.includes(job.id)}
              onSelect={() => onSelectJob(job.id)}
            />
          </m.div>
        ))}
      </AnimatePresence>
    </m.div>
  );
}
