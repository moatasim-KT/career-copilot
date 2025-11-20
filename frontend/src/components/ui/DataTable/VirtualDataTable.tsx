/**
 * VirtualDataTable Component
 * 
 * A virtualized version of the DataTable component that efficiently renders large datasets
 * by only rendering visible rows in the viewport. Uses @tanstack/react-virtual
 * for optimal performance with 100+ rows.
 * 
 * Features:
 * - Virtual scrolling for performance with large datasets (automatically enabled for 100+ rows)
 * - All standard DataTable features (sorting, filtering, selection, etc.)
 * - Smooth scrolling with configurable overscan
 * - Responsive design with mobile card view
 * - Performance monitoring and FPS tracking
 */

'use client';

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
import { useVirtualizer } from '@tanstack/react-virtual';
import { clsx } from 'clsx';
import { ArrowUpDown, Search, X, ChevronDown, ChevronRight } from 'lucide-react';
import React, { useRef, useEffect, useState } from 'react';

import Button from '@/components/ui/Button2';
import { Checkbox } from '@/components/ui/Checkbox';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import Input from '@/components/ui/Input2';
import Select from '@/components/ui/Select2';
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
      className="h-12 px-4 text-left align-middle font-medium text-muted-foreground dark:bg-neutral-800"
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

interface VirtualDataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  isLoading?: boolean;
  renderSubComponent?: (row: TData) => React.ReactNode;
  /** Estimated height of each row in pixels (default: 53) */
  estimatedRowHeight?: number;
  /** Number of rows to render outside the visible area (default: 5) */
  overscan?: number;
  /** Enable virtualization (default: auto-enabled for 100+ rows) */
  enableVirtualization?: boolean;
  /** Enable performance monitoring */
  enablePerformanceMonitoring?: boolean;
}

/**
 * Performance Monitor Hook
 * Tracks FPS and render performance
 */
function usePerformanceMonitor(enabled: boolean) {
  const [fps, setFps] = useState<number>(60);
  const [renderTime, setRenderTime] = useState<number>(0);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const renderStartRef = useRef(0);

  useEffect(() => {
    if (!enabled) return;

    let animationFrameId: number;

    const measureFPS = () => {
      frameCountRef.current++;
      const currentTime = performance.now();
      const elapsed = currentTime - lastTimeRef.current;

      if (elapsed >= 1000) {
        const currentFps = Math.round((frameCountRef.current * 1000) / elapsed);
        setFps(currentFps);
        frameCountRef.current = 0;
        lastTimeRef.current = currentTime;
      }

      animationFrameId = requestAnimationFrame(measureFPS);
    };

    animationFrameId = requestAnimationFrame(measureFPS);

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [enabled]);

  const startRender = () => {
    if (enabled) {
      renderStartRef.current = performance.now();
    }
  };

  const endRender = () => {
    if (enabled && renderStartRef.current > 0) {
      const renderDuration = performance.now() - renderStartRef.current;
      setRenderTime(renderDuration);
      renderStartRef.current = 0;
    }
  };

  return { fps, renderTime, startRender, endRender };
}

export function VirtualDataTable<TData, TValue>({
  columns,
  data,
  isLoading,
  renderSubComponent,
  estimatedRowHeight = 53,
  overscan = 5,
  enableVirtualization,
  enablePerformanceMonitoring = false,
}: VirtualDataTableProps<TData, TValue>) {
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
    columns.map((c, idx) => {
      if (c.id) return c.id;
      // Type assertion for accessor columns
      const col = c as any;
      return typeof col.accessorKey === 'string' ? col.accessorKey : `col-${idx}`;
    }),
  );

  const debouncedGlobalFilter = useDebounce(globalFilter, 300);
  const isMobile = useMediaQuery('(max-width: 768px)');

  // Performance monitoring
  const { fps, renderTime, startRender, endRender } = usePerformanceMonitor(
    enablePerformanceMonitoring || false,
  );

  // Determine if virtualization should be enabled
  const shouldVirtualize = enableVirtualization !== undefined
    ? enableVirtualization
    : data.length > 100;

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

  const handleDragEnd = (event: any) => {
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
      .filter((col) => {
        const c = col as any;
        return c.accessorKey;
      })
      .map((col) => (col as any).accessorKey as keyof TData);
    exportToCSV(dataToExport, columnKeys, 'datatable_export');
  };

  // Virtualization setup
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const rows = tableWithSelection.getRowModel().rows;

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => estimatedRowHeight,
    overscan,
    enabled: shouldVirtualize,
  });

  const virtualRows = shouldVirtualize ? virtualizer.getVirtualItems() : null;
  const totalSize = shouldVirtualize ? virtualizer.getTotalSize() : 0;

  // Measure render performance
  useEffect(() => {
    startRender();
    return () => endRender();
  });

  // Mobile card view (non-virtualized for simplicity)
  if (isMobile) {
    return (
      <div>
        {table.getRowModel().rows.map((row) => (
          <div key={row.id} className="border-b dark:border-neutral-700 p-4">
            {row.getVisibleCells().map((cell) => (
              <div key={cell.id} className="flex justify-between">
                <span className="font-medium">
                  {typeof cell.column.columnDef.header === 'string'
                    ? cell.column.columnDef.header
                    : cell.column.id}
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
              {shouldVirtualize && (
                <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">
                  (Virtualized)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Performance Monitor */}
        {enablePerformanceMonitoring && (
          <div className="mb-2 flex items-center gap-4 text-xs text-neutral-600 dark:text-neutral-400 bg-neutral-100 dark:bg-neutral-800 p-2 rounded">
            <span className={clsx('font-mono', {
              'text-green-600 dark:text-green-400': fps >= 55,
              'text-yellow-600 dark:text-yellow-400': fps >= 30 && fps < 55,
              'text-red-600 dark:text-red-400': fps < 30,
            })}>
              FPS: {fps}
            </span>
            <span className="font-mono">
              Render: {renderTime.toFixed(2)}ms
            </span>
            <span className="font-mono">
              Rows: {rows.length}
            </span>
            {shouldVirtualize && virtualRows && (
              <span className="font-mono">
                Visible: {virtualRows.length}
              </span>
            )}
          </div>
        )}

        <div
          ref={tableContainerRef}
          className="rounded-md border dark:border-neutral-700 overflow-auto"
          style={{
            maxHeight: shouldVirtualize ? '600px' : undefined,
          }}
        >
          <table
            className="w-full text-sm min-w-[600px] md:min-w-full"
            style={{ width: table.getCenterTotalSize() }}
          >
            <thead className="bg-neutral-50 dark:bg-neutral-900 sticky top-0 z-10">
              {tableWithSelection.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  <SortableContext
                    items={columnOrder}
                    strategy={horizontalListSortingStrategy}
                  >
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="h-12 px-4 text-left align-middle font-medium text-muted-foreground dark:bg-neutral-800"
                      >
                        <DraggableHeader
                          header={header}
                        />
                      </th>
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
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={memoizedColumns.length} className="h-24 text-center">
                    No results.
                  </td>
                </tr>
              ) : shouldVirtualize && virtualRows ? (
                <>
                  {/* Spacer for virtual scrolling */}
                  {virtualRows.length > 0 && virtualRows[0].index > 0 && (
                    <tr>
                      <td
                        colSpan={memoizedColumns.length}
                        style={{ height: `${virtualRows[0].start}px` }}
                      />
                    </tr>
                  )}

                  {/* Render only visible rows */}
                  {virtualRows.map((virtualRow) => {
                    const row = rows[virtualRow.index];
                    return (
                      <React.Fragment key={row.id}>
                        <tr
                          data-state={row.getIsSelected() && 'selected'}
                          data-index={virtualRow.index}
                          className="border-b dark:border-neutral-700 transition-colors hover:bg-muted/50 dark:hover:bg-neutral-700 data-[state=selected]:bg-muted"
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
                        {row.getIsExpanded() && renderSubComponent && (
                          <tr>
                            <td colSpan={memoizedColumns.length}>
                              {renderSubComponent(row.original)}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}

                  {/* Spacer after visible rows */}
                  {virtualRows.length > 0 && (
                    <tr>
                      <td
                        colSpan={memoizedColumns.length}
                        style={{
                          height: `${totalSize -
                            (virtualRows[virtualRows.length - 1]?.end || 0)
                            }px`,
                        }}
                      />
                    </tr>
                  )}
                </>
              ) : (
                // Non-virtualized rendering for small datasets
                rows.map((row) => (
                  <React.Fragment key={row.id}>
                    <tr
                      data-state={row.getIsSelected() && 'selected'}
                      className="border-b dark:border-neutral-700 transition-colors hover:bg-muted/50 dark:hover:bg-neutral-700 data-[state=selected]:bg-muted"
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
                    {row.getIsExpanded() && renderSubComponent && (
                      <tr>
                        <td colSpan={memoizedColumns.length}>
                          {renderSubComponent(row.original)}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
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
              onChange={(e) => {
                tableWithSelection.setPageSize(Number(e.target.value));
              }}
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="30">30</option>
              <option value="40">40</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
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

export default VirtualDataTable;
