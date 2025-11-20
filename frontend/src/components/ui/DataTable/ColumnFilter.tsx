import { Column } from '@tanstack/react-table';
import React from 'react';

import Input2 from '@/components/ui/Input2';

interface ColumnFilterProps<TData, TValue> {
  column: Column<TData, TValue>;
}

export function ColumnFilter<TData, TValue>({
  column,
}: ColumnFilterProps<TData, TValue>) {
  const columnFilterValue = column.getFilterValue();

  return (
    <Input2
      value={(columnFilterValue ?? '') as string}
      onChange={(e) => column.setFilterValue(e.target.value)}
      placeholder={'Filter...'}
      className="w-36 border shadow rounded"
    />
  );
}