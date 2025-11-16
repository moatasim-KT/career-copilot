





/* eslint-disable @typescript-eslint/no-unused-vars */
'use client';

import {
  Plus,
  Search,
  MapPin,
  Building,
  ExternalLink,
  Edit,
  Trash2,
  Briefcase,
  DollarSign,
  Clock,
  AlertCircle,
  CheckCircle,
  X,
  Filter,
  SortAsc,
  SortDesc,
  Star,
  StarOff,
  RefreshCw,
  Upload,
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';

import { DataImport, type DataImportColumn } from '@/components/features/DataImport';
import { FilterChips, removeRuleFromQuery } from '@/components/features/FilterChips';
import { RecentSearches } from '@/components/features/RecentSearches';
import { SavedSearches, useSavedSearches } from '@/components/features/SavedSearches';
import { QuickFilterChips } from '@/components/filters/QuickFilterChips';
import { SavedFilters } from '@/components/filters/SavedFilters';
import { StickyFilterPanel } from '@/components/filters/StickyFilterPanel';
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
import Card2, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card2';
import { ExportDropdown } from '@/components/ui/ExportDropdown';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import { useBulkUndo } from '@/hooks/useBulkUndo';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import { useRecentSearches } from '@/hooks/useRecentSearches';
import { ApplicationsService, JobsService } from '@/lib/api/client';
import { createJobBulkActions } from '@/lib/bulkActions/jobActions';
import { logger } from '@/lib/logger';
import { AnimatePresence } from '@/lib/motion';
import { JOB_SEARCH_FIELDS } from '@/lib/searchFields';
import { applySearchQuery, countSearchResults, createEmptyQuery, hasSearchCriteria, queryToSearchParams, searchParamsToQuery } from '@/lib/searchUtils';
import type { SearchGroup, SavedSearch } from '@/types/search';

// Type definitions
export interface JobCreate {
  company: string;
  title: string;
  location: string;
  url: string;
  salary_range: string;
  job_type: string;
  description: string;
  remote: boolean;
  tech_stack: string[];
  responsibilities: string;
  source: string;
}

export interface JobResponse extends JobCreate {
  id: number;
  created_at?: string;
  updated_at?: string;
  match_score?: number;
  salary_min?: number;
  salary_max?: number;
}

import { JobComparisonView } from './JobComparisonView';
import { JobListView } from './JobListView';
import { JobTableView } from './JobTableView';

const JOB_TYPES = [
  { value: 'full-time', label: 'Full-time' },
  { value: 'part-time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
];

const JOB_SOURCES = [
  { value: 'manual', label: 'Manual' },
  { value: 'scraped', label: 'Scraped' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'indeed', label: 'Indeed' },
  { value: 'glassdoor', label: 'Glassdoor' },
];

const SORT_OPTIONS = [
  { value: 'created_at_desc', label: 'Newest First' },
  { value: 'created_at_asc', label: 'Oldest First' },
  { value: 'company_asc', label: 'Company A-Z' },
  { value: 'company_desc', label: 'Company Z-A' },
  { value: 'title_asc', label: 'Title A-Z' },
  { value: 'title_desc', label: 'Title Z-A' },
  { value: 'match_score_desc', label: 'Best Match First' },
];

const TECH_SKILLS = [
  'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js',
  'Node.js', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'SQL', 'NoSQL',
  'PostgreSQL', 'MongoDB', 'Redis', 'Machine Learning', 'Data Science',
  'FastAPI', 'Django', 'Flask', 'Spring Boot', 'Go', 'Rust', 'C++', 'C#',
  '.NET', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Flutter', 'React Native',
  'GraphQL', 'REST API', 'Microservices', 'CI/CD', 'Git', 'Linux',
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showJobModal, setShowJobModal] = useState(false);
  const [editingJob, setEditingJob] = useState<JobResponse | null>(null);
  const [sourceFilter, setSourceFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at_desc');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [currentView, setCurrentView] = useState('list'); // 'list' or 'table'
  const [activeQuickFilters, setActiveQuickFilters] = useState<string[]>([]);
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
  const [showComparisonView, setShowComparisonView] = useState(false);
  const [savedFilters, setSavedFilters] = useLocalStorage<any[]>('savedJobFilters', []);
  const [showImportModal, setShowImportModal] = useState(false);

  // Advanced Search state
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [advancedSearchQuery, setAdvancedSearchQuery] = useState<SearchGroup>(createEmptyQuery());
  const { saveSearch } = useSavedSearches('jobs');
  const { addRecentSearch } = useRecentSearches('jobs');

  // Bulk operations state
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmAction, setConfirmAction] = useState<any>(null);
  const [showProgress, setShowProgress] = useState(false);
  const [progressData, setProgressData] = useState({
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

      // Restore jobs to their previous state
      await Promise.all(
        affectedIds.map((jobId) => {
          const prevJob = previousState.find((j: JobResponse) => j.id === jobId);
          if (prevJob) {
            return JobsService.update(jobId as number, prevJob);
          }
          return Promise.resolve();
        }),
      );

      setSuccessMessage('Action undone successfully');
      loadJobs();
    },
  });;

  const handleSaveFilter = (filterName: string) => {
    const currentFilters = {
      searchTerm,
      sourceFilter,
      typeFilter,
      sortBy,
      activeQuickFilters,
    };
    setSavedFilters(prev => [...prev, { name: filterName, filters: currentFilters }]);
  };

  const handleApplyFilter = (filter: any) => {
    setSearchTerm(filter.filters.searchTerm);
    setSourceFilter(filter.filters.sourceFilter);
    setTypeFilter(filter.filters.typeFilter);
    setSortBy(filter.filters.sortBy);
    setActiveQuickFilters(filter.filters.activeQuickFilters || []);
  };

  const handleDeleteFilter = (filterName: string) => {
    setSavedFilters(prev => prev.filter(f => f.name !== filterName));
  };

  const handleSelectJob = (jobId: number) => {
    setSelectedJobIds(prev =>
      prev.includes(jobId) ? prev.filter(id => id !== jobId) : [...prev, jobId],
    );
  };

  // Load jobs function - must be declared before useBulkUndo
  const loadJobs = async () => {
    setIsLoading(true);
    try {
      const response = await JobsService.list();
      setJobs(response.data || []);
    } catch (err) {
      setError('Failed to load jobs');
    } finally {
      setIsLoading(false);
    }
  };

  // Create bulk actions
  const bulkActions = createJobBulkActions({
    jobs,
    onSuccess: (message) => {
      setSuccessMessage(message);
      setSelectedJobIds([]);
      setTimeout(() => setSuccessMessage(''), 3000);
    },
    onError: (message) => {
      setErrorMessage(message);
      setTimeout(() => setErrorMessage(''), 5000);
    },
    onRefresh: loadJobs,
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
      const affectedJobs = jobs.filter(job => job.id && selectedJobIds.includes(job.id));
      storeUndo(action.id, action.label, affectedJobs, selectedJobIds);
    }

    try {
      await action.action(selectedJobIds);
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

  // Handle bulk delete
  const handleBulkDelete = async () => {
    const deleteAction = bulkActions.find(action => action.id === 'delete');
    if (deleteAction) {
      await handleBulkAction(deleteAction);
    }
  };

  const [formData, setFormData] = useState<JobCreate>({
    company: '',
    title: '',
    location: '',
    url: '',
    salary_range: '',
    job_type: 'full-time',
    description: '',
    remote: false,
    tech_stack: [] as string[],
    responsibilities: '',
    source: 'manual',
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadJobs();
  }, []);

  const handleScrapeJobs = async () => {
    setIsScraping(true);
    try {
      await JobsService.scrape();
      alert('Job scraping started successfully!');
      // Refresh jobs list after scraping
      loadJobs();
    } catch (error) {
      logger.error('Error starting job scraping:', error);
      alert('Failed to start job scraping');
    } finally {
      setIsScraping(false);
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.company.trim()) {
      errors.company = 'Company is required';
    }

    if (!formData.title.trim()) {
      errors.title = 'Job title is required';
    }

    if (formData.url && !isValidUrl(formData.url)) {
      errors.url = 'Please enter a valid URL';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const isValidUrl = (string: string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = editingJob
        ? await JobsService.update(editingJob.id, formData)
        : await JobsService.create(formData);

      setShowJobModal(false);
      setEditingJob(null);
      resetForm();
      loadJobs();
    } catch (err) {
      setError('Failed to save job');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await JobsService.delete(jobId);
      loadJobs();
    } catch (err) {
      setError('Failed to delete job');
    }
  };

  const handleApply = async (job: JobResponse) => {
    try {
      await ApplicationsService.create({
        job_id: job.id,
        status: 'interested',
        notes: 'Applied via job management',
      });
      // Show success message or update UI
      alert('Application created successfully!');
    } catch (err) {
      setError('Failed to create application');
    }
  };

  const handleImportJobs = async (data: any[]) => {
    try {
      // Import jobs one by one
      const results = await Promise.allSettled(
        data.map((jobData) =>
          JobsService.create({
            ...jobData,
            tech_stack: jobData.tech_stack ? jobData.tech_stack.split(',').map((s: string) => s.trim()) : [],
          }),
        ),
      );

      const successCount = results.filter((r) => r.status === 'fulfilled').length;
      const failureCount = results.filter((r) => r.status === 'rejected').length;

      if (successCount > 0) {
        setSuccessMessage(`Successfully imported ${successCount} job(s)`);
        setTimeout(() => setSuccessMessage(''), 3000);
        loadJobs();
      }

      if (failureCount > 0) {
        setErrorMessage(`Failed to import ${failureCount} job(s)`);
        setTimeout(() => setErrorMessage(''), 5000);
      }

      setShowImportModal(false);
    } catch (err) {
      setErrorMessage('Import failed. Please try again.');
      setTimeout(() => setErrorMessage(''), 5000);
    }
  };

  const jobImportColumns: DataImportColumn[] = [
    { key: 'company', label: 'Company', required: true, type: 'string' },
    { key: 'title', label: 'Job Title', required: true, type: 'string' },
    { key: 'location', label: 'Location', required: false, type: 'string' },
    { key: 'url', label: 'URL', required: false, type: 'string' },
    { key: 'salary_range', label: 'Salary Range', required: false, type: 'string' },
    { key: 'job_type', label: 'Job Type', required: false, type: 'string' },
    { key: 'description', label: 'Description', required: false, type: 'string' },
    { key: 'remote', label: 'Remote', required: false, type: 'boolean' },
    { key: 'tech_stack', label: 'Tech Stack', required: false, type: 'string' },
    { key: 'responsibilities', label: 'Responsibilities', required: false, type: 'string' },
    { key: 'source', label: 'Source', required: false, type: 'string' },
  ];;

  const resetForm = () => {
    setFormData({
      company: '',
      title: '',
      location: '',
      url: '',
      salary_range: '',
      job_type: 'full-time',
      description: '',
      remote: false,
      tech_stack: [],
      responsibilities: '',
      source: 'manual',
    });
    setFormErrors({});
  };

  const startEdit = (job: JobResponse) => {
    setEditingJob(job);
    const jobCreate: JobCreate = {
      company: job.company,
      title: job.title,
      location: job.location || '',
      url: job.url || '',
      salary_range: job.salary_range || '',
      job_type: job.job_type || 'full-time',
      description: job.description || '',
      remote: job.remote || false,
      tech_stack: job.tech_stack || [],
      responsibilities: job.responsibilities || '',
      source: job.source || 'manual',
    };
    setFormData(jobCreate);
    setFormErrors({});
    setShowJobModal(true);
  };

  const openAddModal = () => {
    setEditingJob(null);
    resetForm();
    setShowJobModal(true);
  };

  const closeModal = () => {
    setShowJobModal(false);
    setEditingJob(null);
    resetForm();
  };

  // Apply advanced search if active
  const handleApplyAdvancedSearch = (query: SearchGroup) => {
    setAdvancedSearchQuery(query);

    // Add to recent searches
    const resultCount = countSearchResults(jobs, query);
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
    return countSearchResults(jobs, query);
  };

  // Memoize filtered and sorted jobs to prevent unnecessary recalculations
  const filteredAndSortedJobs = useMemo(() => {
    let filtered = jobs;

    // Apply advanced search first if active
    if (hasSearchCriteria(advancedSearchQuery)) {
      filtered = applySearchQuery(filtered, advancedSearchQuery);
    } else {
      // Apply basic filters only if no advanced search
      filtered = jobs.filter(job => {
        const matchesSearch =
          job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (job.location && job.location.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (job.tech_stack && job.tech_stack.some(tech =>
            tech.toLowerCase().includes(searchTerm.toLowerCase()),
          ));

        const matchesSource = sourceFilter === 'all' || (job.source && job.source === sourceFilter);
        const matchesType = typeFilter === 'all' || (job.job_type && job.job_type === typeFilter);

        const matchesQuickFilters = activeQuickFilters.every(filter => {
          switch (filter) {
            case 'remote':
              return job.remote || false;
            case 'full-time':
              return job.job_type === 'full-time';
            case 'react':
              return job.tech_stack?.includes('React');
            default:
              return true;
          }
        });

        return matchesSearch && matchesSource && matchesType && matchesQuickFilters;
      });
    }

    // Sort the filtered results
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'created_at_desc':
          return new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime();
        case 'created_at_asc':
          return new Date(a.created_at || '').getTime() - new Date(b.created_at || '').getTime();
        case 'company_asc':
          return a.company.localeCompare(b.company);
        case 'company_desc':
          return b.company.localeCompare(a.company);
        case 'title_asc':
          return a.title.localeCompare(b.title);
        case 'title_desc':
          return b.title.localeCompare(a.title);
        case 'match_score_desc':
          return (b.match_score || 0) - (a.match_score || 0);
        default:
          return 0;
      }
    });
  }, [jobs, searchTerm, sourceFilter, typeFilter, sortBy, activeQuickFilters, advancedSearchQuery]);

  // Create a unique key that changes when filters or sort changes
  // This triggers re-animation of the list
  const listKey = useMemo(() => {
    return `${searchTerm}-${sourceFilter}-${typeFilter}-${sortBy}-${activeQuickFilters.join(',')}`;
  }, [searchTerm, sourceFilter, typeFilter, sortBy, activeQuickFilters]);

  const getSourceBadgeColor = (source: string) => {
    switch (source.toLowerCase()) {
      case 'manual': return 'bg-neutral-100 text-neutral-800';
      case 'scraped': return 'bg-blue-100 text-blue-800';
      case 'linkedin': return 'bg-blue-100 text-blue-800';
      case 'indeed': return 'bg-green-100 text-green-800';
      case 'glassdoor': return 'bg-purple-100 text-purple-800';
      default: return 'bg-neutral-100 text-neutral-800';
    }
  };

  const getMatchScoreColor = (score?: number) => {
    if (!score) return '';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Job Management</h1>
          <p className="text-neutral-600 mt-1">
            Manage your job opportunities and track applications
          </p>
        </div>
        <div className="flex gap-2">
          <ExportDropdown
            data={filteredAndSortedJobs}
            selectedIds={selectedJobIds}
            filename="jobs"
            csvColumns={[
              { key: 'id', header: 'ID' },
              { key: 'title', header: 'Job Title' },
              { key: 'company', header: 'Company' },
              { key: 'location', header: 'Location' },
              { key: 'job_type', header: 'Job Type' },
              { key: 'salary_min', header: 'Min Salary' },
              { key: 'salary_max', header: 'Max Salary' },
              { key: 'source', header: 'Source' },
              { key: 'url', header: 'URL' },
            ]}
            pdfColumns={[
              { key: 'id', header: 'ID', width: 30 },
              { key: 'title', header: 'Job Title' },
              { key: 'company', header: 'Company' },
              { key: 'location', header: 'Location' },
              { key: 'job_type', header: 'Type' },
              {
                key: 'salary_min',
                header: 'Salary Range',
                formatter: (min: any) => {
                  if (min) {
                    return `$${min.toLocaleString()}+`;
                  }
                  return 'Not specified';
                },
              },
            ]}
            pdfOptions={{
              title: 'Job Opportunities',
              subtitle: `Export of ${filteredAndSortedJobs.length} jobs`,
              theme: 'striped',
            }}
            variant="outline"
            onExportStart={(type) => {
              logger.info('Export started', { type });
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
          <Button2
            onClick={handleScrapeJobs}
            disabled={isScraping}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${isScraping ? 'animate-spin' : ''}`} />
            <span>{isScraping ? 'Finding Jobs...' : 'Find Jobs'}</span>
          </Button2>
          <Button2
            onClick={() => setShowImportModal(true)}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <Upload className="h-4 w-4" />
            <span>Import Jobs</span>
          </Button2>
          <Button2 onClick={openAddModal} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Add Job</span>
          </Button2>
        </div>
      </div>

      {error && (
        <Card2 className="border-red-200 bg-red-50">
          <CardContent className="flex items-center p-4">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-800 ml-3">{error}</p>
          </CardContent>
        </Card2>
      )}

      {/* Search and Filters */}
      <Card2>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
                <Input
                  type="text"
                  placeholder="Search jobs by title, company, location, or tech stack..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  disabled={hasSearchCriteria(advancedSearchQuery)}
                />
              </div>
            </div>

            <Select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              options={[
                { value: 'all', label: 'All Sources' },
                ...JOB_SOURCES,
              ]}
              disabled={hasSearchCriteria(advancedSearchQuery)}
            />

            <Select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              options={[
                { value: 'all', label: 'All Types' },
                ...JOB_TYPES,
              ]}
              disabled={hasSearchCriteria(advancedSearchQuery)}
            />
          </div>

          {/* Advanced Search Controls */}
          <div className="mt-4 flex items-center space-x-2">
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
              context="jobs"
            />

            <RecentSearches
              onLoad={handleLoadRecentSearch}
              context="jobs"
            />
          </div>

          {/* Active Filter Chips */}
          {hasSearchCriteria(advancedSearchQuery) && (
            <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
              <FilterChips
                query={advancedSearchQuery}
                onRemoveFilter={handleRemoveFilter}
                onClearAll={handleClearAdvancedSearch}
              />
            </div>
          )}

          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
                checked={selectedJobIds.length === filteredAndSortedJobs.length && filteredAndSortedJobs.length > 0}
                onChange={() => {
                  if (selectedJobIds.length === filteredAndSortedJobs.length) {
                    setSelectedJobIds([]);
                  } else {
                    setSelectedJobIds(filteredAndSortedJobs.map(job => job.id || 0));
                  }
                }}
              />
              <label className="text-sm font-medium text-neutral-700">Select All</label>
            </div>
            {selectedJobIds.length > 0 && (
              <div className="flex space-x-2">
                {selectedJobIds.length >= 2 && (
                  <Button2
                    variant="outline"
                    onClick={() => setShowComparisonView(true)}
                    className="flex items-center space-x-2"
                  >
                    <span>Compare Selected ({selectedJobIds.length})</span>
                  </Button2>
                )}
                <Button2
                  variant="destructive"
                  onClick={handleBulkDelete}
                  className="flex items-center space-x-2"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>Delete Selected ({selectedJobIds.length})</span>
                </Button2>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between mt-4 pt-4 border-t border-neutral-200">              <div className="text-sm text-neutral-600">
            Showing {filteredAndSortedJobs.length} of {jobs.length} jobs
          </div>

            <div className="flex items-center space-x-2">
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                options={SORT_OPTIONS}
                className="w-48"
              />
              <div className="flex rounded-md shadow-sm">
                <button
                  type="button"
                  onClick={() => setCurrentView('list')}
                  className={`
                      px-3 py-2 rounded-l-md border border-neutral-300 bg-background text-sm font-medium
                      ${currentView === 'list' ? 'text-blue-600 bg-blue-50' : 'text-neutral-700 hover:bg-neutral-50'}
                    `}
                  title="List View"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 9a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 13a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentView('table')}
                  className={`
                      px-3 py-2 rounded-r-md border border-neutral-300 bg-background text-sm font-medium
                      ${currentView === 'table' ? 'text-blue-600 bg-blue-50' : 'text-neutral-700 hover:bg-neutral-50'}
                    `}
                  title="Table View"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5 4a1 1 0 00-1 1v4a1 1 0 001 1h10a1 1 0 001-1V5a1 1 0 00-1-1H5zm0 6a1 1 0 00-1 1v4a1 1 0 001 1h10a1 1 0 001-1v-4a1 1 0 00-1-1H5z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card2>

      {showComparisonView && (
        <JobComparisonView
          jobs={jobs.filter(job => job.id && selectedJobIds.includes(job.id))}
          onClose={() => setShowComparisonView(false)}
        />
      )
      }

      {/* Job Form Modal */}
      <LazyModal
        isOpen={showJobModal}
        onClose={closeModal}
        title={editingJob ? 'Edit Job' : 'Add New Job'}
        size="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-1 md:grid-cols-2">
            <Input
              label="Company *"
              value={formData.company}
              onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
              error={formErrors.company}
              placeholder="Enter company name"
              className="min-h-[44px]"
              autoComplete="organization"
            />

            <Input
              label="Job Title *"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              error={formErrors.title}
              placeholder="Enter job title"
              className="min-h-[44px]"
              autoComplete="job-title"
            />

            <Input
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              placeholder="e.g., San Francisco, CA or Remote"
              className="min-h-[44px]"
              autoComplete="address-level2"
            />

            <Select
              label="Job Type"
              value={formData.job_type}
              onChange={(e) => setFormData(prev => ({ ...prev, job_type: e.target.value }))}
              options={JOB_TYPES}
            />

            <Input
              label="Salary Range"
              value={formData.salary_range}
              onChange={(e) => setFormData(prev => ({ ...prev, salary_range: e.target.value }))}
              placeholder="e.g., $80k-$120k"
              className="min-h-[44px]"
              inputMode="numeric"
              pattern="[0-9]*"
            />

            <Input
              label="Job URL"
              type="url"
              value={formData.url}
              onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
              error={formErrors.url}
              placeholder="https://..."
              className="min-h-[44px]"
              inputMode="url"
            />
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.remote}
                onChange={(e) => setFormData(prev => ({ ...prev, remote: e.target.checked }))}
                className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-neutral-700">Remote Position</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Tech Stack
            </label>
            <div className="grid grid-cols-3 md:grid-cols-4 gap-2 max-h-40 overflow-y-auto border border-neutral-300 rounded-md p-3">
              {TECH_SKILLS.map(skill => (
                <label key={skill} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={formData.tech_stack.includes(skill)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData(prev => ({
                          ...prev,
                          tech_stack: [...prev.tech_stack, skill],
                        }));
                      } else {
                        setFormData(prev => ({
                          ...prev,
                          tech_stack: prev.tech_stack.filter(s => s !== skill),
                        }));
                      }
                    }}
                    className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{skill}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-neutral-500 mt-1">
              Selected: {formData.tech_stack.length} skills
            </p>
          </div>

          <Textarea
            label="Responsibilities"
            rows={3}
            value={formData.responsibilities}
            onChange={(e) => setFormData(prev => ({ ...prev, responsibilities: e.target.value }))}
            placeholder="Key responsibilities for this role..."
          />

          <Textarea
            label="Description"
            rows={4}
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Full job description..."
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
              {editingJob ? 'Update Job' : 'Add Job'}
            </Button2>
          </LazyModalFooter>
        </form>
      </LazyModal>

      {/* Import Jobs Modal */}
      <LazyModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        title="Import Jobs from CSV"
        size="xl"
      >
        <DataImport
          onImport={handleImportJobs}
          templateUrl="/templates/jobs-template.csv"
          columns={jobImportColumns}
          title="Import Jobs"
          description="Upload a CSV file to bulk import job listings. Download the template below to see the required format."
          validator={(data) => {
            const errors: string[] = [];

            // Validate job types
            const validJobTypes = ['full-time', 'part-time', 'contract', 'internship'];
            data.forEach((row, index) => {
              if (row.job_type && !validJobTypes.includes(row.job_type.toLowerCase())) {
                errors.push(`Row ${index + 1}: Invalid job type "${row.job_type}". Must be one of: ${validJobTypes.join(', ')}`);
              }
            });

            return {
              valid: errors.length === 0,
              errors,
            };
          }}
        />
      </LazyModal>

      {/* Jobs List */}
      {
        isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Card2 key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="h-4 bg-neutral-200 rounded w-1/4 mb-2"></div>
                  <div className="h-6 bg-neutral-200 rounded w-1/2 mb-4"></div>
                  <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
                </CardContent>
              </Card2>
            ))}
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {currentView === 'list' ? (
              <JobListView
                key={listKey}
                jobs={filteredAndSortedJobs}
                onJobClick={(jobId) => logger.info('View job:', jobId)}
                selectedJobIds={selectedJobIds}
                onSelectJob={handleSelectJob}
              />
            ) : (
              <JobTableView
                key={listKey}
                jobs={filteredAndSortedJobs}
                onJobClick={(jobId) => logger.info('View job:', jobId)}
                selectedJobIds={selectedJobIds}
                onSelectJob={handleSelectJob}
              />
            )}
          </AnimatePresence>
        )
      }

      {/* Advanced Search Panel */}
      <LazyAdvancedSearch
        isOpen={showAdvancedSearch}
        onClose={() => setShowAdvancedSearch(false)}
        onSearch={handleApplyAdvancedSearch}
        fields={JOB_SEARCH_FIELDS}
        initialQuery={advancedSearchQuery}
        onPreview={handlePreviewSearch}
        onSave={saveSearch}
        resultCount={filteredAndSortedJobs.length}
      />

      {/* Bulk Action Bar */}
      {
        selectedJobIds.length > 0 && (
          <LazyBulkActionBar
            selectedCount={selectedJobIds.length}
            selectedIds={selectedJobIds}
            actions={bulkActions.map(action => ({
              ...action,
              action: () => handleBulkAction(action),
            }))}
            onClearSelection={() => setSelectedJobIds([])}
          />
        )
      }

      {/* Confirmation Dialog */}
      <LazyConfirmBulkAction
        isOpen={showConfirmDialog}
        onClose={() => {
          setShowConfirmDialog(false);
          setConfirmAction(null);
        }}
        onConfirm={handleConfirmAction}
        title={`Confirm ${confirmAction?.label}`}
        message={`Are you sure you want to ${confirmAction?.label.toLowerCase()} ${selectedJobIds.length} job${selectedJobIds.length > 1 ? 's' : ''}?`}
        itemCount={selectedJobIds.length}
        itemNames={jobs
          .filter(job => job.id && selectedJobIds.includes(job.id))
          .map(job => `${job.title} at ${job.company}`)
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
        message={`${undoState?.actionName || 'Action'} applied to ${undoState?.affectedIds.length || 0} job${(undoState?.affectedIds.length || 0) > 1 ? 's' : ''}`}
        onUndo={undo}
        onDismiss={clearUndo}
        isUndoing={isUndoing}
      />

      {/* Success/Error Messages */}
      {
        successMessage && (
          <div className="fixed top-4 right-4 z-50">
            <Card2 className="border-green-200 bg-green-50">
              <CardContent className="flex items-center p-4">
                <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                <p className="text-sm text-green-800 ml-3">{successMessage}</p>
              </CardContent>
            </Card2>
          </div>
        )
      }

      {
        errorMessage && (
          <div className="fixed top-4 right-4 z-50">
            <Card2 className="border-red-200 bg-red-50">
              <CardContent className="flex items-center p-4">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-800 ml-3">{errorMessage}</p>
              </CardContent>
            </Card2>
          </div>
        )
      }
    </div >
  );
}