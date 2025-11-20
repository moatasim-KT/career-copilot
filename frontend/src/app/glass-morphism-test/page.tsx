'use client';

import { Bell, Plus, Settings, User } from 'lucide-react';
import { useState } from 'react';

import { BulkAction, BulkActionsBar } from '@/components/bulk/BulkActions';
import Notification from '@/components/notifications/Notification';
import Button2 from '@/components/ui/Button2';
import DatePicker2 from '@/components/ui/DatePicker2';
import Drawer2 from '@/components/ui/Drawer2';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import Modal from '@/components/ui/Modal2';
import MultiSelect2 from '@/components/ui/MultiSelect2';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/Popover';
import Tooltip from '@/components/ui/Tooltip';
import { logger } from '@/lib/logger';

export default function GlassMorphismTestPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  const bulkActions: BulkAction[] = [
    {
      id: 'action1',
      label: 'Action 1',
      icon: <Plus className="w-4 h-4" />,
      variant: 'primary',
      onClick: async () => logger.info('Action 1'),
    },
  ];

  const multiSelectOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
            Glass Morphism Effects Test
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400">
            Testing glass morphism effects on various components
          </p>
        </div>

        {/* Test Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Modal Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Modal Backdrop
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Modal backdrop should have glass morphism effect
            </p>
            <Button2 onClick={() => setModalOpen(true)}>Open Modal</Button2>
          </div>

          {/* Drawer Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Drawer Backdrop
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Drawer backdrop should have glass morphism effect
            </p>
            <Button2 onClick={() => setDrawerOpen(true)}>Open Drawer</Button2>
          </div>

          {/* Popover Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Popover Background
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Popover should have glass morphism background
            </p>
            <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
              <PopoverTrigger>
                <Button2>Open Popover</Button2>
              </PopoverTrigger>
              <PopoverContent>
                <div className="p-4">
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    This popover has glass morphism!
                  </p>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          {/* Dropdown Menu Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Dropdown Menu
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Dropdown menu should have glass morphism
            </p>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button2>
                  <Settings className="w-4 h-4 mr-2" />
                  Menu
                </Button2>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem>
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Bell className="w-4 h-4 mr-2" />
                  Notifications
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Notification Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Floating Notification
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Notification should have glass morphism
            </p>
            <Button2 onClick={() => setShowNotification(true)}>
              Show Notification
            </Button2>
          </div>

          {/* Bulk Actions Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Bulk Actions Bar
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Bulk actions bar should have glass morphism
            </p>
            <Button2
              onClick={() =>
                setSelectedIds(selectedIds.length > 0 ? [] : ['1', '2', '3'])
              }
            >
              {selectedIds.length > 0 ? 'Clear Selection' : 'Select Items'}
            </Button2>
          </div>

          {/* DatePicker Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              DatePicker Calendar
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Calendar popover should have glass morphism
            </p>
            <DatePicker2
              label="Select Date"
              value={date}
              onChange={(newDate) => setDate(newDate || undefined)}
            />
          </div>

          {/* MultiSelect Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              MultiSelect Dropdown
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              MultiSelect dropdown should have glass morphism
            </p>
            <MultiSelect2
              label="Select Options"
              options={multiSelectOptions}
              value={selectedOptions}
              onChange={setSelectedOptions}
              placeholder="Select options"
            />
          </div>

          {/* Tooltip Test */}
          <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
              Tooltip
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Tooltip should have glass morphism
            </p>
            <Tooltip content="This tooltip has glass morphism!" position="top">
              <Button2>Hover Me</Button2>
            </Tooltip>
          </div>
        </div>

        {/* Scroll Test Section */}
        <div className="mt-16 bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
            Sticky Navigation Test
          </h3>
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
            Scroll down to see the navigation bar apply glass morphism effect when scrolled
          </p>
          <div className="h-[200vh] bg-gradient-to-b from-transparent to-blue-100 dark:to-neutral-900 rounded-lg p-8">
            <p className="text-neutral-700 dark:text-neutral-300">
              Keep scrolling to test the sticky navigation glass effect...
            </p>
          </div>
        </div>
      </div>

      {/* Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Glass Morphism Modal"
        description="The backdrop behind this modal has glass morphism effect"
      >
        <div className="space-y-4">
          <p className="text-neutral-700 dark:text-neutral-300">
            Notice the blurred, translucent backdrop behind this modal. This is the glass
            morphism effect in action!
          </p>
          <Button2 onClick={() => setModalOpen(false)}>Close</Button2>
        </div>
      </Modal>

      {/* Drawer */}
      <Drawer2
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Glass Morphism Drawer"
        description="The backdrop has glass morphism effect"
        side="right"
      >
        <div className="space-y-4">
          <p className="text-neutral-700 dark:text-neutral-300">
            The backdrop behind this drawer also has the glass morphism effect!
          </p>
          <Button2 onClick={() => setDrawerOpen(false)}>Close</Button2>
        </div>
      </Drawer2>

      {/* Notification */}
      {showNotification && (
        <Notification
          message="This notification has glass morphism!"
          type="success"
          duration={5000}
          onClose={() => setShowNotification(false)}
        />
      )}

      {/* Bulk Actions Bar */}
      <BulkActionsBar
        selectedIds={selectedIds}
        totalCount={10}
        actions={bulkActions}
        onClearSelection={() => setSelectedIds([])}
      />
    </div>
  );
}
