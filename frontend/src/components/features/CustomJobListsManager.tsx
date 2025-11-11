/**
 * Custom Job Lists Manager Component
 * Displays custom job lists with drag-to-reorder functionality
 */

'use client';

import { Folder, Trash2, Edit } from 'lucide-react';
import { toast } from 'sonner';

import { DraggableList } from '@/components/ui/DraggableList';
import { useCustomJobLists, CustomJobList } from '@/hooks/useCustomJobLists';

interface CustomJobListsManagerProps {
  onSelectList?: (list: CustomJobList) => void;
}

export function CustomJobListsManager({ onSelectList }: CustomJobListsManagerProps) {
  const { lists, isLoading, deleteList, reorderLists } = useCustomJobLists();

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this list?')) {
      deleteList(id);
      toast.success('List deleted');
    }
  };

  const handleSelect = (list: CustomJobList) => {
    if (onSelectList) {
      onSelectList(list);
    }
  };

  const getColorClass = (color?: string) => {
    const colorMap: Record<string, string> = {
      blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      green: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      red: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
      yellow: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    };
    return colorMap[color || 'blue'] || colorMap.blue;
  };

  const renderListItem = (list: CustomJobList, isDragging = false) => (
    <div
      className={`flex items-center justify-between p-4 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 transition-shadow cursor-pointer ${
        isDragging ? 'shadow-2xl ring-2 ring-blue-500 dark:ring-blue-400' : 'hover:shadow-md'
      }`}
      onClick={() => handleSelect(list)}
    >
      <div className="flex items-center space-x-3 flex-1 ml-8">
        <div className={`p-2 rounded-lg ${getColorClass(list.color)}`}>
          <Folder className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-neutral-900 dark:text-neutral-100">{list.name}</h4>
          {list.description && (
            <p className="text-sm text-neutral-600 dark:text-neutral-400">{list.description}</p>
          )}
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            {list.jobIds.length} {list.jobIds.length === 1 ? 'job' : 'jobs'}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={() => toast.info('Edit feature coming soon')}
          className="p-2 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
          aria-label="Edit list"
        >
          <Edit className="h-4 w-4" />
        </button>
        <button
          onClick={() => handleDelete(list.id)}
          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          aria-label="Delete list"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-20 bg-neutral-200 dark:bg-neutral-700 rounded-lg animate-pulse"
          ></div>
        ))}
      </div>
    );
  }

  if (lists.length === 0) {
    return (
      <div className="text-center py-8">
        <Folder className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
        <p className="text-neutral-600 dark:text-neutral-400">No custom lists</p>
        <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-1">
          Create lists to organize your job searches
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Drag lists to reorder them
        </p>
      </div>

      <DraggableList
        items={lists}
        onReorder={reorderLists}
        renderItem={renderListItem}
        getItemId={(list) => list.id}
        className="space-y-3"
      />
    </div>
  );
}
