'use client';

import {
  FileText,
  Calendar,
  Building,
  MapPin,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Trophy,
  Eye,
  Plus,
  Edit,
  Search,
  Filter,
} from 'lucide-react';
import { useState, useEffect, useCallback, useMemo } from 'react';

import { FilterChips, removeRuleFromQuery } from '@/components/features/FilterChips';
import { RecentSearches } from '@/components/features/RecentSearches';
import { SavedSearches, useSavedSearches } from '@/components/features/SavedSearches';
import {
  LazyAdvancedSearch,
  LazyModal,
  LazyModalFooter,
  LazyBulkActionBar,
  LazyConfirmBulkAction,
  LazyBulkOperationProgress,
  LazyUndoToast,
} from '@/components/lazy';
import Button2 from '@/components/ui/Button2';
import Card2, { CardContent } from '@/components/ui/Card2';
import { ExportDropdown } from '@/components/ui/ExportDropdown';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import { useBulkUndo } from '@/hooks/useBulkUndo';
import { useRecentSearches } from '@/hooks/useRecentSearches';
import { useWebSocket } from '@/hooks/useWebSocket';
import { staggerContainer, staggerItem, fadeVariants, springConfigs } from '@/lib/animations';
import { apiClient, type Application } from '@/lib/api';
import { createApplicationBulkActions } from '@/lib/bulkActions/applicationActions';
import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';
import { APPLICATION_SEARCH_FIELDS } from '@/lib/searchFields';
import { applySearchQuery, countSearchResults, createEmptyQuery, hasSearchCriteria, queryToSearchParams } from '@/lib/searchUtils';
import { handleApplicationStatusUpdate } from '@/lib/websocket/applications';
import type { SearchGroup, SavedSearch } from '@/types/search';

const STATUS_OPTIONS = [
  { value: 'interested', label: 'Interested' },
  { value: 'applied', label: 'Applied' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'declined', label: 'Declined' },
];

const SORT_OPTIONS = [
  { value: 'created_at_desc', label: 'Newest First' },
  { value: 'created_at_asc', label: 'Oldest First' },
  { value: 'applied_date_desc', label: 'Recently Applied' },
  { value: 'applied_date_asc', label: 'Oldest Applied' },
  { value: 'status_asc', label: 'Status A-Z' },
  { value: 'company_asc', label: 'Company A-Z' },
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('created_at_desc');
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Advanced Search state
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [advancedSearchQuery, setAdvancedSearchQuery] = useState<SearchGroup>(createEmptyQuery());
  const { saveSearch } = useSavedSearches('applications');
  const { addRecentSearch } = useRecentSearches('applications');

  // Bulk operations state
  const [selectedApplicationIds, setSelectedApplicationIds] = useState<number[]>([]);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmAction, setConfirmAction] = useState<any>(null);
  const [showProgress, setShowProgress] = useState(false);
  const [progressData, _setProgressData] = useState({
    totalItems: 0,
    processedItems: 0,
    successCount: 0,
    failureCount: 0,
    errors: [] as any[],
    isComplete: false,
  });
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Undo functionality
  const { undoState, isUndoing, storeUndo, undo, clearUndo, canUndo } = useBulkUndo({
    timeout: 5000,
    onUndo: async (state) => {
      // Restore previous state
      const { previousState, affectedIds } = state;

      // Restore applications to their previous state
      await Promise.all(
        affectedIds.map((appId) => {
          const prevApp = previousState.find((a: Application) => a.id === appId);
          if (prevApp) {
            return apiClient.updateApplication(appId as number, prevApp);
          }
        }),
      );

      setSuccessMessage('Action undone successfully');
      loadApplications();
    },
  });

  const handleApplicationUpdate = useCallback((data: any) => {
    logger.log('Application update received:', data);
    if (data.applicationId) {
      setApplications(prev =>
        prev.map(app =>
          app.id === data.applicationId
            ? { ...app, status: data.status }
            : app,
        ),
      );
      setLastUpdated(new Date());
    }
  }, []);

  useWebSocket(
    'ws://localhost:8080/api/ws',
    // onDashboardUpdate (not needed here)
    () => { },
    // onApplicationStatusUpdate
    (data) => handleApplicationStatusUpdate(data, handleApplicationUpdate),
    // onAnalyticsUpdate (not needed)
    () => { },
  );

  const [formData, setFormData] = useState({
    job_id: 0,
    status: 'interested' as Application['status'],
    notes: '',
    applied_date: '',
    interview_date: '',
    response_date: '',
  });

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.getApplications();
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setApplications(response.data);
        setLastUpdated(new Date());
      }
    } catch (error) {
      logger.error('Failed to load applications', error);
      setError('Failed to load applications');
    } finally {
      setIsLoading(false);
    }
  };

  const updateApplicationStatus = async (appId: number, newStatus: string) => {
    try {
      const response = await apiClient.updateApplication(appId, { status: newStatus as any });
      if (response.error) {
        setError(response.error);
      } else {
        loadApplications();
      }
    } catch (error) {
      logger.error('Failed to update application', error);
      setError('Failed to update application');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.job_id || formData.job_id === 0) {
      setError('Please select a job');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = editingApplication
        ? await apiClient.updateApplication(editingApplication.id, formData)
        : await apiClient.createApplication(formData);

      if (response.error) {
        setError(response.error);
      } else {
        setShowApplicationModal(false);
        setEditingApplication(null);
        resetForm();
        loadApplications();
      }
    } catch (error) {
      logger.error('Failed to save application', error);
      setError('Failed to save application');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      job_id: 0,
      status: 'interested' as Application['status'],
      notes: '',
      applied_date: '',
      interview_date: '',
      response_date: '',
    });
  };

  const openAddModal = () => {
    setEditingApplication(null);
    resetForm();
    setShowApplicationModal(true);
  };

  const startEdit = (application: Application) => {
    setEditingApplication(application);
    setFormData({
      job_id: application.job_id,
      status: application.status,
      notes: application.notes || '',
      applied_date: application.applied_date ? application.applied_date.split('T')[0] : '',
      interview_date: application.interview_date ? application.interview_date.split('T')[0] : '',
      response_date: application.response_date ? application.response_date.split('T')[0] : '',
    });
    setShowApplicationModal(true);
  };

  const closeModal = () => {
    setShowApplicationModal(false);
    setEditingApplication(null);
    resetForm();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'interested':
        return <Eye className="h-4 w-4 text-yellow-500" />;
      case 'applied':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'interview':
        return <Calendar className="h-4 w-4 text-purple-500" />;
      case 'offer':
        return <Trophy className="h-4 w-4 text-green-500" />;
      case 'accepted':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'declined':
        return <XCircle className="h-4 w-4 text-neutral-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-neutral-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'interested':
        return 'bg-yellow-100 text-yellow-800';
      case 'applied':
        return 'bg-blue-100 text-blue-800';
      case 'interview':
        return 'bg-purple-100 text-purple-800';
      case 'offer':
        return 'bg-green-100 text-green-800';
      case 'accepted':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'declined':
        return 'bg-neutral-100 text-neutral-800';
      default:
        return 'bg-neutral-100 text-neutral-800';
    }
  };

  // Apply advanced search if active
  const handleApplyAdvancedSearch = (query: SearchGroup) => {
    setAdvancedSearchQuery(query);

    // Add to recent searches
    const resultCount = countSearchResults(applications, query);
    addRecentSearch(query, resultCount);

    // Update URL with search params
    const params = queryToSearchParams(query);
    window.history.pushState({}, '', `?${params.toString()}`);
  };

  const handleClearAdvancedSearch = () => {
    setAdvancedSearchQuery(createEmptyQuery());
    window.history.pushState({}, '', window.location.pathname);
  };

  const handleRemoveFilter = (ruleId: string) => {
    const updatedQuery = removeRuleFromQuery(advancedSearchQuery, ruleId);
    setAdvancedSearchQuery(updatedQuery);

    // Update URL
    if (hasSearchCriteria(updatedQuery)) {
      const params = queryToSearchParams(updatedQuery);
      window.history.pushState({}, '', `?${params.toString()}`);
    } else {
      window.history.pushState({}, '', window.location.pathname);
    }
  };

  const handleLoadSavedSearch = (search: SavedSearch) => {
    setAdvancedSearchQuery(search.query);
    const params = queryToSearchParams(search.query);
    window.history.pushState({}, '', `?${params.toString()}`);
  };

  const handleLoadRecentSearch = (query: SearchGroup) => {
    setAdvancedSearchQuery(query);
    const params = queryToSearchParams(query);
    window.history.pushState({}, '', `?${params.toString()}`);
  };

  const handlePreviewSearch = async (query: SearchGroup): Promise<number> => {
    return countSearchResults(applications, query);
  };

  // Create bulk actions
  const bulkActions = createApplicationBulkActions({
    applications,
    onSuccess: (message) => {
      setSuccessMessage(message);
      setSelectedApplicationIds([]);
      setTimeout(() => setSuccessMessage(''), 3000);
    },
    onError: (message) => {
      setErrorMessage(message);
      setTimeout(() => setErrorMessage(''), 5000);
    },
    onRefresh: loadApplications,
  });

  // Handle bulk action with confirmation
  const handleBulkAction = async (action: any) => {
    if (action.requiresConfirmation) {
      setConfirmAction(action);
      setShowConfirmDialog(true);
    } else {
      await executeBulkAction(action);
    }
  };

  // Execute bulk action
  const executeBulkAction = async (action: any) => {
    // Store previous state for undo (only for non-destructive actions)
    if (!action.requiresConfirmation) {
      const affectedApps = applications.filter(app => selectedApplicationIds.includes(app.id));
      storeUndo(action.id, action.label, affectedApps, selectedApplicationIds);
    }

    try {
      await action.action(selectedApplicationIds);
    } catch (error) {
      logger.error('Bulk action failed:', error);
    }
  };

  // Confirm and execute action
  const handleConfirmAction = async () => {
    if (confirmAction) {
      setShowConfirmDialog(false);
      await executeBulkAction(confirmAction);
      setConfirmAction(null);
    }
  };

  // Handle selection toggle
  const handleSelectApplication = (appId: number) => {
    setSelectedApplicationIds(prev =>
      prev.includes(appId) ? prev.filter(id => id !== appId) : [...prev, appId],
    );
  };

  // Handle select all
  const handleSelectAll = () => {
    if (selectedApplicationIds.length === filteredAndSortedApplications.length) {
      setSelectedApplicationIds([]);
    } else {
      setSelectedApplicationIds(filteredAndSortedApplications.map(app => app.id));
    }
  };

  const filteredAndSortedApplications = useMemo(() => {
    let filtered = applications;

    // Apply advanced search first if active
    if (hasSearchCriteria(advancedSearchQuery)) {
      // Map application fields for search
      const searchableApps = applications.map(app => ({
        ...app,
        job_title: app.job?.title || '',
        company: app.job?.company || '',
      }));
      filtered = applySearchQuery(searchableApps, advancedSearchQuery);
    } else {
      // Apply basic filters only if no advanced search
      filtered = applications.filter(app => {
        const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
        const matchesSearch =
          (app.job?.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
          (app.job?.company || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
          (app.notes || '').toLowerCase().includes(searchTerm.toLowerCase());

        return matchesStatus && matchesSearch;
      });
    }

    // Sort the filtered results
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'created_at_desc':
          return new Date(b.applied_date || '').getTime() - new Date(a.applied_date || '').getTime();
        case 'created_at_asc':
          return new Date(a.applied_date || '').getTime() - new Date(b.applied_date || '').getTime();
        case 'applied_date_desc':
          return new Date(b.applied_date || '').getTime() - new Date(a.applied_date || '').getTime();
        case 'applied_date_asc':
          return new Date(a.applied_date || '').getTime() - new Date(b.applied_date || '').getTime();
        case 'status_asc':
          return a.status.localeCompare(b.status);
        case 'company_asc':
          return (a.job?.company || '').localeCompare(b.job?.company || '');
        default:
          return 0;
      }
    });
  }, [applications, searchTerm, statusFilter, sortBy, advancedSearchQuery]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-neutral-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Card2 key={i}>
                <CardContent className="p-6">
                  <div className="h-4 bg-neutral-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-neutral-200 rounded w-1/2 mb-4"></div>
                  <div className="h-4 bg-neutral-200 rounded w-1/4"></div>
                </CardContent>
              </Card2>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <m.div
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div>
          <m.h1
            className="text-3xl font-bold text-neutral-900"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            Applications
          </m.h1>
          <m.p
            className="text-neutral-600 mt-1"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            Track your job applications and their progress
          </m.p>
          {lastUpdated && (
            <m.p
              className="text-sm text-neutral-500 mt-1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              key={lastUpdated.toISOString()}
            >
              Last updated: {lastUpdated.toLocaleTimeString()}
            </m.p>
          )}
        </div>
        <m.div
          className="flex items-center space-x-3"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <m.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <ExportDropdown
              data={filteredAndSortedApplications}
              selectedIds={selectedApplicationIds}
              filename="applications"
              csvColumns={[
                { key: 'id', header: 'ID' },
                { key: 'job_id', header: 'Job ID' },
                { key: 'status', header: 'Status' },
                { key: 'applied_date', header: 'Applied Date' },
                { key: 'interview_date', header: 'Interview Date' },
                { key: 'response_date', header: 'Response Date' },
                { key: 'notes', header: 'Notes' },
              ]}
              pdfColumns={[
                { key: 'id', header: 'ID', width: 30 },
                {
                  key: 'job',
                  header: 'Job Title',
                  formatter: (job) => job?.title || 'N/A',
                },
                {
                  key: 'job',
                  header: 'Company',
                  formatter: (job) => job?.company || 'N/A',
                },
                { key: 'status', header: 'Status' },
                {
                  key: 'applied_date',
                  header: 'Applied',
                  formatter: (date) => date ? new Date(date).toLocaleDateString() : 'N/A',
                },
              ]}
              pdfOptions={{
                title: 'Job Applications',
                subtitle: `Export of ${filteredAndSortedApplications.length} applications`,
                theme: 'striped',
              }}
              variant="outline"
              onExportStart={(type) => {
                logger.log('Export started', { type });
              }}
              onExportComplete={(type) => {
                setSuccessMessage(`Export completed successfully (${type})`);
                setTimeout(() => setSuccessMessage(''), 3000);
              }}
              onExportError={(error) => {
                setErrorMessage(`Export failed: ${error.message}`);
                setTimeout(() => setErrorMessage(''), 5000);
              }}
            />
          </m.div>
          <m.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button2
              variant="outline"
              onClick={loadApplications}
              disabled={isLoading}
              className="flex items-center space-x-2"
            >
              <FileText className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Loading...' : 'Refresh'}</span>
            </Button2>
          </m.div>
          <m.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button2 onClick={openAddModal} className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Add Application</span>
            </Button2>
          </m.div>
        </m.div>
      </m.div>

      <AnimatePresence>
        {error && (
          <m.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -10, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Card2 className="border-red-200 bg-red-50">
              <CardContent className="flex items-center p-4">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-800 ml-3">{error}</p>
              </CardContent>
            </Card2>
          </m.div>
        )}
      </AnimatePresence>

      {/* Search and Filters */}
      <m.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card2>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <m.div
                className="relative"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
                <Input
                  type="text"
                  placeholder="Search applications..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  disabled={hasSearchCriteria(advancedSearchQuery)}
                />
              </m.div>

              <m.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35 }}
              >
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  options={[
                    { value: 'all', label: 'All Status' },
                    ...STATUS_OPTIONS,
                  ]}
                  disabled={hasSearchCriteria(advancedSearchQuery)}
                />
              </m.div>

              <m.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
              >
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  options={SORT_OPTIONS}
                />
              </m.div>
            </div>

            {/* Advanced Search Controls */}
            <m.div
              className="mt-4 flex items-center space-x-2"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
            >
              <Button2
                type="button"
                variant="outline"
                onClick={() => setShowAdvancedSearch(true)}
                className="flex items-center space-x-2"
              >
                <Filter className="h-4 w-4" />
                <span>Advanced Search</span>
              </Button2>

              <SavedSearches
                onLoad={handleLoadSavedSearch}
                onSave={saveSearch}
                context="applications"
              />

              <RecentSearches
                onLoad={handleLoadRecentSearch}
                context="applications"
              />
            </m.div>

            {/* Active Filter Chips */}
            {hasSearchCriteria(advancedSearchQuery) && (
              <m.div
                className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ delay: 0.5 }}
              >
                <FilterChips
                  query={advancedSearchQuery}
                  onRemoveFilter={handleRemoveFilter}
                  onClearAll={handleClearAdvancedSearch}
                />
              </m.div>
            )}

            <m.div
              className="mt-4 pt-4 border-t border-neutral-200"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
                      checked={selectedApplicationIds.length === filteredAndSortedApplications.length && filteredAndSortedApplications.length > 0}
                      onChange={handleSelectAll}
                    />
                    <span className="text-sm font-medium text-neutral-700">Select All</span>
                  </label>
                  {selectedApplicationIds.length > 0 && (
                    <span className="text-sm text-neutral-600">
                      {selectedApplicationIds.length} selected
                    </span>
                  )}
                </div>
                <m.div
                  className="text-sm text-neutral-600"
                  key={`${filteredAndSortedApplications.length}-${statusFilter}`}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  Showing {filteredAndSortedApplications.length} of {applications.length} applications
                  {statusFilter !== 'all' && ` with status: ${statusFilter}`}
                </m.div>
              </div>
            </m.div>
          </CardContent>
        </Card2>
      </m.div>

      {/* Application Form Modal */}
      <LazyModal
        isOpen={showApplicationModal}
        onClose={closeModal}
        title={editingApplication ? 'Edit Application' : 'Add New Application'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-1 md:grid-cols-2">
            <Select
              label="Job *"
              value={formData.job_id.toString()}
              onChange={(e) => setFormData(prev => ({ ...prev, job_id: parseInt(e.target.value) || 0 }))}
              options={[
                { value: '0', label: 'Select a job...' },
                // Note: In a real implementation, you'd fetch available jobs
                // For now, this is a placeholder
              ]}
              className="min-h-[44px]"
            />
            <Select
              label="Status"
              value={formData.status}
              onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as Application['status'] }))}
              options={STATUS_OPTIONS}
              className="min-h-[44px]"
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-1 md:grid-cols-3">
            <Input
              label="Applied Date"
              type="date"
              value={formData.applied_date}
              onChange={(e) => setFormData(prev => ({ ...prev, applied_date: e.target.value }))}
              className="min-h-[44px]"
            />
            <Input
              label="Interview Date"
              type="date"
              value={formData.interview_date}
              onChange={(e) => setFormData(prev => ({ ...prev, interview_date: e.target.value }))}
              className="min-h-[44px]"
            />
            <Input
              label="Response Date"
              type="date"
              value={formData.response_date}
              onChange={(e) => setFormData(prev => ({ ...prev, response_date: e.target.value }))}
              className="min-h-[44px]"
            />
          </div>
          <Textarea
            label="Notes"
            rows={4}
            value={formData.notes}
            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
            placeholder="Add any notes about this application..."
            className="min-h-[44px]"
          />

          <LazyModalFooter>
            <Button2
              type="button"
              variant="outline"
              onClick={closeModal}
            >
              Cancel
            </Button2>
            <Button2
              type="submit"
              loading={isSubmitting}
            >
              {editingApplication ? 'Update Application' : 'Add Application'}
            </Button2>
          </LazyModalFooter>
        </form>
      </LazyModal>

      {filteredAndSortedApplications.length > 0 ? (
        <m.div
          className="space-y-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <AnimatePresence mode="popLayout">
            {filteredAndSortedApplications.map((application) => (
              <m.div
                key={application.id}
                variants={staggerItem}
                layout
                initial="hidden"
                animate="visible"
                exit={{
                  opacity: 0,
                  y: -10,
                  scale: 0.95,
                  transition: {
                    duration: 0.2,
                    ease: 'easeIn',
                  },
                }}
                transition={springConfigs.smooth}
              >
                <Card2 hover className="transition-all duration-200">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <input
                          type="checkbox"
                          className="mt-1 rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
                          checked={selectedApplicationIds.includes(application.id)}
                          onChange={() => handleSelectApplication(application.id)}
                        />
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="text-lg font-semibold text-neutral-900">
                              {application.job?.title || 'Unknown Position'}
                            </h3>
                            <div className="flex items-center space-x-1">
                              <m.div
                                key={`icon-${application.status}`}
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={springConfigs.bouncy}
                              >
                                {getStatusIcon(application.status)}
                              </m.div>
                              <m.span
                                key={`badge-${application.status}`}
                                initial={{ opacity: 0, scale: 0.9, y: -5 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                transition={springConfigs.bouncy}
                                className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(application.status)}`}
                              >
                                {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                              </m.span>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-600 mb-3">
                            <div className="flex items-center space-x-1">
                              <Building className="h-4 w-4" />
                              <span>{application.job?.company || 'Unknown Company'}</span>
                            </div>
                            {application.job?.location && (
                              <div className="flex items-center space-x-1">
                                <MapPin className="h-4 w-4" />
                                <span>{application.job.location}</span>
                              </div>
                            )}
                            {application.applied_date && (
                              <div className="flex items-center space-x-1">
                                <Clock className="h-4 w-4" />
                                <span>Applied {new Date(application.applied_date).toLocaleDateString()}</span>
                              </div>
                            )}
                          </div>

                          {application.notes && (
                            <p className="text-sm text-neutral-600 mb-3">
                              <strong>Notes:</strong> {application.notes}
                            </p>
                          )}

                          <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-500">
                            {application.interview_date && (
                              <span>Interview: {new Date(application.interview_date).toLocaleDateString()}</span>
                            )}
                            {application.response_date && (
                              <span>Response: {new Date(application.response_date).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 ml-4">
                          <m.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            <Button2
                              variant="ghost"
                              size="sm"
                              onClick={() => startEdit(application)}
                              title="Edit Application"
                            >
                              <Edit className="h-4 w-4" />
                            </Button2>
                          </m.div>

                          <m.div
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                          >
                            <Select
                              value={application.status}
                              onChange={(e) => updateApplicationStatus(application.id, e.target.value)}
                              options={STATUS_OPTIONS}
                              className="w-32"
                            />
                          </m.div>
                        </div>
                      </div>
                    </div>

                    {/* Interview Feedback Section */}
                    {application.interview_feedback && (
                      <m.div
                        className="mt-4 pt-4 border-t border-neutral-200"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        transition={{ delay: 0.1, duration: 0.3 }}
                      >
                        <h4 className="text-sm font-medium text-neutral-900 mb-2">Interview Feedback</h4>

                        {application.interview_feedback.questions && application.interview_feedback.questions.length > 0 && (
                          <m.div
                            className="mb-2"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.15 }}
                          >
                            <p className="text-xs font-medium text-neutral-700">Questions Asked:</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {application.interview_feedback.questions.map((question, idx) => (
                                <m.span
                                  key={idx}
                                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                                  initial={{ opacity: 0, scale: 0.8 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  transition={{ delay: 0.2 + idx * 0.05 }}
                                >
                                  {question}
                                </m.span>
                              ))}
                            </div>
                          </m.div>
                        )}

                        {application.interview_feedback.skill_areas && application.interview_feedback.skill_areas.length > 0 && (
                          <m.div
                            className="mb-2"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                          >
                            <p className="text-xs font-medium text-neutral-700">Skill Areas Discussed:</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {application.interview_feedback.skill_areas.map((skill, idx) => (
                                <m.span
                                  key={idx}
                                  className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                                  initial={{ opacity: 0, scale: 0.8 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  transition={{ delay: 0.25 + idx * 0.05 }}
                                >
                                  {skill}
                                </m.span>
                              ))}
                            </div>
                          </m.div>
                        )}

                        {application.interview_feedback.notes && (
                          <m.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.25 }}
                          >
                            <p className="text-xs font-medium text-neutral-700">Notes:</p>
                            <p className="text-sm text-neutral-600 mt-1">{application.interview_feedback.notes}</p>
                          </m.div>
                        )}
                      </m.div>
                    )}

                    {/* Job Tech Stack */}
                    {application.job?.tech_stack && application.job.tech_stack.length > 0 && (
                      <m.div
                        className="mt-4 pt-4 border-t border-neutral-200"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        transition={{ delay: 0.15, duration: 0.3 }}
                      >
                        <p className="text-xs font-medium text-neutral-700 mb-2">Required Tech Stack:</p>
                        <div className="flex flex-wrap gap-1">
                          {application.job.tech_stack.slice(0, 10).map((tech, idx) => (
                            <m.span
                              key={tech}
                              className="px-2 py-1 bg-neutral-100 text-neutral-700 text-xs rounded-full"
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: 0.2 + idx * 0.03 }}
                              whileHover={{ scale: 1.05 }}
                            >
                              {tech}
                            </m.span>
                          ))}
                          {application.job.tech_stack.length > 10 && (
                            <m.span
                              className="px-2 py-1 bg-neutral-100 text-neutral-600 text-xs rounded-full"
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: 0.5 }}
                            >
                              +{application.job.tech_stack.length - 10} more
                            </m.span>
                          )}
                        </div>
                      </m.div>
                    )}
                  </CardContent>
                </Card2>
              </m.div>
            ))}
          </AnimatePresence>
        </m.div>
      ) : (
        <m.div
          variants={fadeVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          <Card2>
            <CardContent className="text-center py-12">
              <m.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1, ...springConfigs.gentle }}
              >
                <FileText className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
              </m.div>
              <m.h3
                className="text-lg font-medium text-neutral-900 mb-2"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                {searchTerm || statusFilter !== 'all'
                  ? 'No applications found'
                  : 'No applications yet'
                }
              </m.h3>
              <m.p
                className="text-neutral-600 mb-4"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search terms or filters'
                  : 'Start by adding jobs and creating applications to track your progress'
                }
              </m.p>
              {!searchTerm && statusFilter === 'all' && (
                <m.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <Button2 onClick={openAddModal}>
                    Add Your First Application
                  </Button2>
                </m.div>
              )}
            </CardContent>
          </Card2>
        </m.div>
      )}

      {/* Advanced Search Panel */}
      <LazyAdvancedSearch
        isOpen={showAdvancedSearch}
        onClose={() => setShowAdvancedSearch(false)}
        onSearch={handleApplyAdvancedSearch}
        fields={APPLICATION_SEARCH_FIELDS}
        initialQuery={advancedSearchQuery}
        onPreview={handlePreviewSearch}
        onSave={saveSearch}
        resultCount={filteredAndSortedApplications.length}
      />

      {/* Bulk Action Bar */}
      {selectedApplicationIds.length > 0 && (
        <LazyBulkActionBar
          selectedCount={selectedApplicationIds.length}
          selectedIds={selectedApplicationIds}
          actions={bulkActions.map(action => ({
            ...action,
            action: () => handleBulkAction(action),
          }))}
          onClearSelection={() => setSelectedApplicationIds([])}
        />
      )}

      {/* Confirmation Dialog */}
      <LazyConfirmBulkAction
        isOpen={showConfirmDialog}
        onClose={() => {
          setShowConfirmDialog(false);
          setConfirmAction(null);
        }}
        onConfirm={handleConfirmAction}
        title={`Confirm ${confirmAction?.label}`}
        message={`Are you sure you want to ${confirmAction?.label.toLowerCase()} ${selectedApplicationIds.length} application${selectedApplicationIds.length > 1 ? 's' : ''}?`}
        itemCount={selectedApplicationIds.length}
        itemNames={applications
          .filter(app => selectedApplicationIds.includes(app.id))
          .map(app => `${app.job?.title || 'Unknown'} at ${app.job?.company || 'Unknown'}`)
        }
        confirmLabel={confirmAction?.label || 'Confirm'}
        isDestructive={confirmAction?.variant === 'destructive'}
        showDontAskAgain={false}
      />

      {/* Progress Dialog */}
      <LazyBulkOperationProgress
        isOpen={showProgress}
        onClose={() => setShowProgress(false)}
        title="Processing Bulk Operation"
        totalItems={progressData.totalItems}
        processedItems={progressData.processedItems}
        successCount={progressData.successCount}
        failureCount={progressData.failureCount}
        errors={progressData.errors}
        isComplete={progressData.isComplete}
      />

      {/* Undo Toast */}
      <LazyUndoToast
        isVisible={canUndo}
        message={`${undoState?.actionName || 'Action'} applied to ${undoState?.affectedIds.length || 0} application${(undoState?.affectedIds.length || 0) > 1 ? 's' : ''}`}
        onUndo={undo}
        onDismiss={clearUndo}
        isUndoing={isUndoing}
      />

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50">
          <Card2 className="border-green-200 bg-green-50">
            <CardContent className="flex items-center p-4">
              <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
              <p className="text-sm text-green-800 ml-3">{successMessage}</p>
            </CardContent>
          </Card2>
        </div>
      )}

      {errorMessage && (
        <div className="fixed top-4 right-4 z-50">
          <Card2 className="border-red-200 bg-red-50">
            <CardContent className="flex items-center p-4">
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
              <p className="text-sm text-red-800 ml-3">{errorMessage}</p>
            </CardContent>
          </Card2>
        </div>
      )}
    </div>
  );
}