
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  horizontalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFacetedMinMaxValues,
  getPaginationRowModel,
  getGroupedRowModel,
  getExpandedRowModel,
  SortingState,
  ColumnFiltersState,
  useReactTable,
  ExpandedState,
  VisibilityState,
} from '@tanstack/react-table';
import { clsx } from 'clsx';
import { ArrowUpDown, Search, X, ChevronDown, ChevronRight } from 'lucide-react';
import React from 'react';

import { Button2 as Button } from '@/components/ui/Button2';
import { Checkbox } from '@/components/ui/Checkbox';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { Input2 as Input } from '@/components/ui/Input2';
import {
  Select2 as Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select2';
import { useDebounce } from '@/hooks/use-debounce';
import { useMediaQuery } from '@/hooks/use-media-query';
import { exportToCSV } from '@/lib/export';

import { ColumnFilter } from './ColumnFilter';

const DraggableHeader = ({ header }: { header: any }) => {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: header.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <th
      ref={setNodeRef}
      style={style}
      className="h-12 px-4 text-left align-middle font-medium text-muted-foreground"
    >
      <div
        className={clsx('flex items-center', {
          'cursor-pointer select-none': header.column.getCanSort(),
        })}
        onClick={header.column.getToggleSortingHandler()}
      >
        {header.isPlaceholder
          ? null
          : flexRender(
            header.column.columnDef.header,
            header.getContext(),
          )}
        {{
          asc: <ArrowUpDown className="ml-2 h-4 w-4" />,
          desc: <ArrowUpDown className="ml-2 h-4 w-4" />,
        }[header.column.getIsSorted() as string] ?? null}
      </div>
      {header.column.getCanFilter() ? (
        <div>
          <ColumnFilter column={header.column} />
        </div>
      ) : null}
      <div
        {...attributes}
        {...listeners}
        onMouseDown={header.getResizeHandler()}
        onTouchStart={header.getResizeHandler()}
        className={clsx(
          'absolute top-0 right-0 h-full w-1 cursor-col-resize select-none touch-none',
          {
            'bg-blue-500': header.column.getIsResizing(),
          },
        )}
      />
    </th>
  );
};


interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  isLoading?: boolean;
  renderSubComponent: (row: TData) => React.ReactNode;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  isLoading,
  renderSubComponent,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const [rowSelection, setRowSelection] = React.useState({});
  const [expanded, setExpanded] = React.useState<ExpandedState>({});
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [columnOrder, setColumnOrder] = React.useState<string[]>(
    columns.map((c, idx) =>
      c.id ?? (typeof c.accessorKey === 'string' ? c.accessorKey : `col-${idx}`),
    ),
  );

  const debouncedGlobalFilter = useDebounce(globalFilter, 300);
  const isMobile = useMediaQuery('(max-width: 768px)');

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
    getFilteredRowModel: getFilteredRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    getPaginationRowModel: getPaginationRowModel(),
    onRowSelectionChange: setRowSelection,
    getGroupedRowModel: getGroupedRowModel(),
    onExpandedChange: setExpanded,
    getExpandedRowModel: getExpandedRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onColumnOrderChange: setColumnOrder,
    columnResizeMode: 'onChange',
    columnResizeDirection: 'ltr',
    state: {
      sorting,
      globalFilter: debouncedGlobalFilter,
      columnFilters,
      rowSelection,
      expanded,
      columnVisibility,
      columnOrder,
    },
  });

  const memoizedColumns = React.useMemo<ColumnDef<TData, TValue>[]>(
    () => [
      {
        id: 'expander',
        header: () => null,
        cell: ({ row }) => {
          return row.getCanExpand() ? (
            <button
              {...{
                onClick: row.getToggleExpandedHandler(),
                style: { cursor: 'pointer' },
              }}
            >
              {row.getIsExpanded() ? <ChevronDown /> : <ChevronRight />}
            </button>
          ) : null;
        },
      },
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
      ...columns,
    ],
    [columns],
  );

  const tableWithSelection = useReactTable({
    ...table.options,
    columns: memoizedColumns,
  });

  const sensors = useSensors(
    useSensor(MouseSensor, {}),
    useSensor(TouchSensor, {}),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      setColumnOrder((items) => {
        const oldIndex = items.indexOf(active.id);
        const newIndex = items.indexOf(over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleExport = (exportType: 'all' | 'selected' | 'current') => {
    let dataToExport: TData[] = [];
    switch (exportType) {
      case 'all':
        dataToExport = data;
        break;
      case 'selected':
        dataToExport = table.getSelectedRowModel().rows.map((row) => row.original);
        break;
      case 'current':
        dataToExport = table.getRowModel().rows.map((row) => row.original);
        break;
    }
    const columnKeys = columns
      .filter((col) => col.accessorKey)
      .map((col) => col.accessorKey as keyof TData);
    exportToCSV(dataToExport, columnKeys, 'datatable_export');
  };

  if (isMobile) {
    return (
      <div>
        {table.getRowModel().rows.map((row) => (
          <div key={row.id} className="border-b p-4">
            {row.getVisibleCells().map((cell) => (
              <div key={cell.id} className="flex justify-between">
                <span className="font-medium">
                  {flexRender(cell.column.columnDef.header, cell.getContext())}
                </span>
                <span>{flexRender(cell.column.columnDef.cell, cell.getContext())}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  return (
    <DndContext
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
      sensors={sensors}
    >
      <div>
        <div className="flex items-center justify-between py-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Filter all columns..."
              value={globalFilter}
              onChange={(event) =>
                setGlobalFilter(event.target.value)
              }
              className="max-w-sm pl-10"
            />
            {globalFilter && (
              <X
                className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground cursor-pointer"
                onClick={() => setGlobalFilter('')}
              />
            )}
          </div>
          <div className="flex items-center space-x-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="ml-auto">
                  Columns
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {tableWithSelection
                  .getAllColumns()
                  .filter(
                    (column) => column.getCanHide(),
                  )
                  .map((column) => {
                    return (
                      <DropdownMenuCheckboxItem
                        key={column.id}
                        className="capitalize"
                        checked={column.getIsVisible()}
                        onCheckedChange={(value) =>
                          column.toggleVisibility(!!value)
                        }
                      >
                        {column.id}
                      </DropdownMenuCheckboxItem>
                    );
                  })}
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="ml-auto">
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleExport('all')}>
                  Export All
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('current')}>
                  Export Current View
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('selected')}>
                  Export Selected
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <div className="text-sm text-muted-foreground">
              Showing {table.getFilteredRowModel().rows.length} of {data.length} results
            </div>
          </div>
        </div>
        <div className="rounded-md border">
          <table className="w-full text-sm" style={{ width: table.getCenterTotalSize() }}>
            <thead>
              {tableWithSelection.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  <SortableContext
                    items={columnOrder}
                    strategy={horizontalListSortingStrategy}
                  >
                    {headerGroup.headers.map((header) => (
                      <DraggableHeader
                        key={header.id}
                        header={header}
                        table={tableWithSelection}
                      />
                    ))}
                  </SortableContext>
                </tr>
              ))}
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={memoizedColumns.length} className="h-24 text-center">
                    Loading...
                  </td>
                </tr>
              ) : tableWithSelection.getRowModel().rows?.length ? (
                tableWithSelection.getRowModel().rows.map((row) => (
                  <React.Fragment key={row.id}>
                    <tr
                      data-state={row.getIsSelected() && 'selected'}
                      className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                    >
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="p-4 align-middle">
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext(),
                          )}
                        </td>
                      ))}
                    </tr>
                    {row.getIsExpanded() && (
                      <tr>
                        <td colSpan={memoizedColumns.length}>
                          {renderSubComponent(row.original)}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              ) : (
                <tr>
                  <td colSpan={memoizedColumns.length} className="h-24 text-center">
                    No results.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between space-x-2 py-4">
          <div className="flex-1 text-sm text-muted-foreground">
            {tableWithSelection.getFilteredSelectedRowModel().rows.length} of{' '}
            {tableWithSelection.getFilteredRowModel().rows.length} row(s) selected.
          </div>
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium">Rows per page</p>
            <Select
              value={`${tableWithSelection.getState().pagination.pageSize}`}
              onChange={(value) => {
                tableWithSelection.setPageSize(Number(value));
              }}
            >
              <SelectTrigger className="h-8 w-[70px]">
                <SelectValue placeholder={tableWithSelection.getState().pagination.pageSize} />
              </SelectTrigger>
              <SelectContent side="top">
                {[10, 20, 30, 40, 50].map((pageSize) => (
                  <SelectItem key={pageSize} value={`${pageSize}`}>
                    {pageSize}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex w-[100px] items-center justify-center text-sm font-medium">
            Page {tableWithSelection.getState().pagination.pageIndex + 1} of{' '}
            {tableWithSelection.getPageCount()}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              className="hidden h-8 w-8 p-0 lg:flex"
              onClick={() => tableWithSelection.setPageIndex(0)}
              disabled={!tableWithSelection.getCanPreviousPage()}
            >
              <span className="sr-only">Go to first page</span>
              <ArrowUpDown className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => tableWithSelection.previousPage()}
              disabled={!tableWithSelection.getCanPreviousPage()}
            >
              <span className="sr-only">Go to previous page</span>
              <ArrowUpDown className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => tableWithSelection.nextPage()}
              disabled={!tableWithSelection.getCanNextPage()}
            >
              <span className="sr-only">Go to next page</span>
              <ArrowUpDown className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="hidden h-8 w-8 p-0 lg:flex"
              onClick={() => tableWithSelection.setPageIndex(tableWithSelection.getPageCount() - 1)}
              disabled={!tableWithSelection.getCanNextPage()}
            >
              <span className="sr-only">Go to last page</span>
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </DndContext>
  );
}
