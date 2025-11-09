import { ColumnDef } from '@tanstack/react-table';
import { motion } from 'framer-motion';
import React from 'react';

import { Button } from '@/components/ui/Button2';
import { Checkbox } from '@/components/ui/Checkbox';
import { DataTable } from '@/components/ui/DataTable';
import { fadeVariants } from '@/lib/animations';
import { Job } from '@/lib/api';

interface JobTableViewProps {
  jobs: Job[];
  onJobClick: (jobId: number) => void;
}

export function JobTableView({ jobs, onJobClick }: JobTableViewProps) {
  const columns: ColumnDef<Job>[] = [
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: 'title',
      header: 'Title',
    },
    {
      accessorKey: 'company',
      header: 'Company',
    },
    {
      accessorKey: 'location',
      header: 'Location',
    },
    {
      accessorKey: 'job_type',
      header: 'Job Type',
    },
    {
      accessorKey: 'source',
      header: 'Source',
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <Button variant="outline" onClick={() => onJobClick(row.original.id)}>
          View
        </Button>
      ),
    },
  ];

  return (
    <motion.div
      variants={fadeVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      <DataTable
        columns={columns}
        data={jobs}
        renderSubComponent={(row) => (
          <div className="p-4 bg-gray-100">
            <p>
              <strong>Description:</strong> {row.description}
            </p>
          </div>
        )}
      />
    </motion.div>
  );
}