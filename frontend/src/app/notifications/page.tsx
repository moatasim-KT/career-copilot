/**
 * Notifications History Page
 * Full list of all notifications with filters, search, and bulk actions
 */

'use client';

import { formatDistanceToNow, format } from 'date-fns';
import {
  Bell,
  Search,
  Filter,
  Check,
  CheckCheck,
  Trash2,
  X,
  ChevronDown,
} from 'lucide-react';
import { useState, useMemo } from 'react';

import { Badge } from '@/components/ui/Badge';
import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import { Checkbox } from '@/components/ui/Checkbox';
import Input2 from '@/components/ui/Input2';
import { m, AnimatePresence } from '@/lib/motion';
import {
  getCategoryIcon,
  getCategoryColor,
  getCategoryLabel,
  categoryLabels,
} from '@/lib/notificationTemplates';
import { cn } from '@/lib/utils';
import type { Notification, NotificationCategory, NotificationFilter } from '@/types/notification';

// Mock notifications - in production, this would come from API
const generateMockNotifications = (): Notification[] => {
  const categories: NotificationCategory[] = ['system', 'job_alert', 'application', 'recommendation', 'social'];
  const notifications: Notification[] = [];

  for (let i = 1; i <= 50; i++) {
    const category = categories[Math.floor(Math.random() * categories.length)];
    const isRead = Math.random() > 0.4;
    const daysAgo = Math.floor(Math.random() * 30);

    notifications.push({
      id: `${i}`,
      userId: '1',
      category,
      title: `Notification ${i}`,
      description: `This is a sample notification description for notification ${i}. It contains some details about the event.`,
      timestamp: new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000),
      read: isRead,
      actionUrl: `/action/${i}`,
      actionLabel: 'View Details',
      priority: Math.random() > 0.7 ? 'high' : 'normal',
    });
  }

  return notifications.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

interface NotificationItemProps {
  notification: Notification;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
}

function NotificationItem({
  notification,
  isSelected,
  onToggleSelect,
  onMarkAsRead,
  onDelete,
}: NotificationItemProps) {
  const CategoryIcon = getCategoryIcon(notification.category);
  const categoryColor = getCategoryColor(notification.category);

  return (
    <m.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className={cn(
        'group relative p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:shadow-md transition-all',
        !notification.read && 'bg-primary-50/30 dark:bg-primary-900/10 border-primary-200 dark:border-primary-800',
        isSelected && 'ring-2 ring-primary-500 dark:ring-primary-400',
      )}
    >
      <div className="flex items-start gap-4">
        {/* Checkbox */}
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggleSelect(notification.id)}
          className="mt-1"
        />

        {/* Category Icon */}
        <div className={cn(
          'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
          categoryColor,
        )}>
          <CategoryIcon className="w-5 h-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                  {notification.title}
                </h3>
                {!notification.read && (
                  <span className="w-2 h-2 bg-primary-600 dark:bg-primary-400 rounded-full" />
                )}
              </div>
              <span className={cn(
                'inline-block text-xs px-2 py-0.5 rounded-full font-medium mb-2',
                categoryColor,
              )}>
                {getCategoryLabel(notification.category)}
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {!notification.read && (
                <button
                  onClick={() => onMarkAsRead(notification.id)}
                  className="p-1.5 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
                  title="Mark as read"
                >
                  <Check className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => onDelete(notification.id)}
                className="p-1.5 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
            {notification.description}
          </p>

          <div className="flex items-center justify-between">
            <span className="text-xs text-neutral-500 dark:text-neutral-500">
              {formatDistanceToNow(notification.timestamp, { addSuffix: true })} • {format(notification.timestamp, 'MMM d, yyyy')}
            </span>

            {notification.actionUrl && notification.actionLabel && (
              <a
                href={notification.actionUrl}
                className="text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
              >
                {notification.actionLabel} →
              </a>
            )}
          </div>
        </div>
      </div>
    </m.div>
  );
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>(generateMockNotifications());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<NotificationFilter>({});
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Filter and search notifications
  const filteredNotifications = useMemo(() => {
    return notifications.filter(notification => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (
          !notification.title.toLowerCase().includes(query) &&
          !notification.description.toLowerCase().includes(query)
        ) {
          return false;
        }
      }

      // Read/Unread filter
      if (filter.read !== undefined && notification.read !== filter.read) {
        return false;
      }

      // Category filter
      if (filter.categories && filter.categories.length > 0) {
        if (!filter.categories.includes(notification.category)) {
          return false;
        }
      }

      return true;
    });
  }, [notifications, searchQuery, filter]);

  // Pagination
  const totalPages = Math.ceil(filteredNotifications.length / itemsPerPage);
  const paginatedNotifications = filteredNotifications.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  const unreadCount = notifications.filter(n => !n.read).length;
  const selectedCount = selectedIds.size;

  const handleToggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === paginatedNotifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(paginatedNotifications.map(n => n.id)));
    }
  };

  const handleMarkAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, read: true } : n)),
    );
  };

  const handleDelete = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(id);
      return newSet;
    });
  };

  const handleBulkMarkAsRead = () => {
    setNotifications(prev =>
      prev.map(n => (selectedIds.has(n.id) ? { ...n, read: true } : n)),
    );
    setSelectedIds(new Set());
  };

  const handleBulkDelete = () => {
    setNotifications(prev => prev.filter(n => !selectedIds.has(n.id)));
    setSelectedIds(new Set());
  };

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const handleCategoryFilter = (category: NotificationCategory) => {
    setFilter(prev => {
      const categories = prev.categories || [];
      const newCategories = categories.includes(category)
        ? categories.filter(c => c !== category)
        : [...categories, category];
      return { ...prev, categories: newCategories.length > 0 ? newCategories : undefined };
    });
    setCurrentPage(1);
  };

  const handleReadFilter = (read: boolean | undefined) => {
    setFilter(prev => ({ ...prev, read }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilter({});
    setSearchQuery('');
    setCurrentPage(1);
  };

  const activeFilterCount =
    (filter.categories?.length || 0) +
    (filter.read !== undefined ? 1 : 0) +
    (searchQuery ? 1 : 0);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Bell className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
            Notifications
          </h1>
        </div>
        <p className="text-neutral-600 dark:text-neutral-400">
          {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}` : 'All caught up!'}
        </p>
      </div>

      {/* Search and Filters */}
      <Card2 className="mb-6 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
              <Input2
                type="text"
                placeholder="Search notifications..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-10"
              />
            </div>
          </div>

          {/* Filter Toggle */}
          <Button2
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="relative"
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            {activeFilterCount > 0 && (
              <Badge variant="primary" className="ml-2">
                {activeFilterCount}
              </Badge>
            )}
            <ChevronDown className={cn(
              'w-4 h-4 ml-2 transition-transform',
              showFilters && 'rotate-180',
            )} />
          </Button2>
        </div>

        {/* Filter Panel */}
        <AnimatePresence>
          {showFilters && (
            <m.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-4 mt-4 border-t border-neutral-200 dark:border-neutral-700">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Read Status Filter */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                      Status
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Button2
                        size="sm"
                        variant={filter.read === undefined ? 'primary' : 'outline'}
                        onClick={() => handleReadFilter(undefined)}
                      >
                        All
                      </Button2>
                      <Button2
                        size="sm"
                        variant={filter.read === false ? 'primary' : 'outline'}
                        onClick={() => handleReadFilter(false)}
                      >
                        Unread
                      </Button2>
                      <Button2
                        size="sm"
                        variant={filter.read === true ? 'primary' : 'outline'}
                        onClick={() => handleReadFilter(true)}
                      >
                        Read
                      </Button2>
                    </div>
                  </div>

                  {/* Category Filter */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                      Category
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {(Object.keys(categoryLabels) as NotificationCategory[]).map(category => (
                        <Button2
                          key={category}
                          size="sm"
                          variant={filter.categories?.includes(category) ? 'primary' : 'outline'}
                          onClick={() => handleCategoryFilter(category)}
                        >
                          {getCategoryLabel(category)}
                        </Button2>
                      ))}
                    </div>
                  </div>
                </div>

                {activeFilterCount > 0 && (
                  <div className="mt-4 flex justify-end">
                    <Button2
                      size="sm"
                      variant="ghost"
                      onClick={clearFilters}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Clear filters
                    </Button2>
                  </div>
                )}
              </div>
            </m.div>
          )}
        </AnimatePresence>
      </Card2>

      {/* Bulk Actions */}
      <AnimatePresence>
        {selectedCount > 0 && (
          <m.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-4"
          >
            <Card2 className="p-4 bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  {selectedCount} notification{selectedCount !== 1 ? 's' : ''} selected
                </span>
                <div className="flex items-center gap-2">
                  <Button2
                    size="sm"
                    variant="outline"
                    onClick={handleBulkMarkAsRead}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Mark as read
                  </Button2>
                  <Button2
                    size="sm"
                    variant="destructive"
                    onClick={handleBulkDelete}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </Button2>
                  <Button2
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedIds(new Set())}
                  >
                    Cancel
                  </Button2>
                </div>
              </div>
            </Card2>
          </m.div>
        )}
      </AnimatePresence>

      {/* Quick Actions */}
      {unreadCount > 0 && selectedCount === 0 && (
        <div className="mb-4 flex justify-end">
          <Button2
            size="sm"
            variant="outline"
            onClick={handleMarkAllAsRead}
          >
            <CheckCheck className="w-4 h-4 mr-2" />
            Mark all as read
          </Button2>
        </div>
      )}

      {/* Select All */}
      {paginatedNotifications.length > 0 && (
        <div className="mb-4 flex items-center gap-2">
          <Checkbox
            checked={selectedIds.size === paginatedNotifications.length && paginatedNotifications.length > 0}
            onCheckedChange={handleSelectAll}
          />
          <span className="text-sm text-neutral-600 dark:text-neutral-400">
            Select all on this page
          </span>
        </div>
      )}

      {/* Notifications List */}
      <div className="space-y-3 mb-6">
        <AnimatePresence mode="popLayout">
          {paginatedNotifications.length > 0 ? (
            paginatedNotifications.map(notification => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                isSelected={selectedIds.has(notification.id)}
                onToggleSelect={handleToggleSelect}
                onMarkAsRead={handleMarkAsRead}
                onDelete={handleDelete}
              />
            ))
          ) : (
            <m.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <Card2 className="p-12 text-center">
                <Bell className="w-16 h-16 mx-auto mb-4 text-neutral-300 dark:text-neutral-600" />
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                  No notifications found
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                  {activeFilterCount > 0
                    ? 'Try adjusting your filters'
                    : 'You\'re all caught up!'}
                </p>
                {activeFilterCount > 0 && (
                  <Button2 variant="outline" onClick={clearFilters}>
                    Clear filters
                  </Button2>
                )}
              </Card2>
            </m.div>
          )}
        </AnimatePresence>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button2
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button2>
          <span className="text-sm text-neutral-600 dark:text-neutral-400">
            Page {currentPage} of {totalPages}
          </span>
          <Button2
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </Button2>
        </div>
      )}
    </div>
  );
}
