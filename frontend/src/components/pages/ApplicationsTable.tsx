
import { ColumnDef } from '@tanstack/react-table';
import React from 'react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button2';
import { Checkbox } from '@/components/ui/Checkbox';
import { DataTable } from '@/components/ui/DataTable';
import { Application } from '@/lib/api';

interface ApplicationsTableProps {
  applications: Application[];
  onApplicationClick: (applicationId: number) => void;
}

export function ApplicationsTable({ applications, onApplicationClick }: ApplicationsTableProps) {
  const columns: ColumnDef<Application>[] = [
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
      accessorKey: 'job.title',
      header: 'Job Title',
    },
    {
      accessorKey: 'job.company',
      header: 'Company',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        let variant: 'default' | 'secondary' | 'destructive' | 'outline' = 'default';
        if (status === 'applied') {
          variant = 'secondary';
        } else if (status === 'rejected') {
          variant = 'destructive';
        }
        return <Badge variant={variant}>{status}</Badge>;
      },
    },
    {
      accessorKey: 'applied_at',
      header: 'Applied At',
      cell: ({ row }) => {
        const date = new Date(row.getValue('applied_at'));
        return date.toLocaleDateString();
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <Button variant="outline" onClick={() => onApplicationClick(row.original.id)}>
          View
        </Button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={applications}
      renderSubComponent={(row) => (
        <div className="p-4 bg-gray-100">
          <p>
            <strong>Notes:</strong> {row.notes}
          </p>
        </div>
      )}
    />
  );
}
