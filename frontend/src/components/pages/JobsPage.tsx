





/* eslint-disable @typescript-eslint/no-unused-vars */
'use client';

import { AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';

import { QuickFilterChips } from '@/components/filters/QuickFilterChips';
import { SavedFilters } from '@/components/filters/SavedFilters';
import { StickyFilterPanel } from '@/components/filters/StickyFilterPanel';
import Button2 from '@/components/ui/Button2';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import Modal, { ModalFooter } from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import { ApplicationsService, JobsService, type JobCreate, type JobResponse } from '@/lib/api/client';

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

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${selectedJobIds.length} selected jobs?`)) return;

    try {
      for (const jobId of selectedJobIds) {
        await JobsService.deleteJobApiV1JobsJobIdDelete({ jobId });
      }
      setSelectedJobIds([]);
      loadJobs();
    } catch (err) {
      setError('Failed to delete selected jobs');
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

  const loadJobs = async () => {
    setIsLoading(true);
    try {
      const response = await JobsService.getJobsApiV1JobsGet();
      setJobs(response);
    } catch (err) {
      setError('Failed to load jobs');
    } finally {
      setIsLoading(false);
    }
  };

  const handleScrapeJobs = async () => {
    setIsScraping(true);
    try {
      await JobsService.scrapeJobsApiV1JobsScrapePost();
      alert('Job scraping started successfully!');
      // Refresh jobs list after scraping
      loadJobs();
    } catch (error) {
      console.error('Error starting job scraping:', error);
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
        ? await JobsService.updateJobApiV1JobsJobIdPut({ jobId: editingJob.id, requestBody: formData })
        : await JobsService.createJobApiV1JobsPost({ requestBody: formData });

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
      await JobsService.deleteJobApiV1JobsJobIdDelete({ jobId });
      loadJobs();
    } catch (err) {
      setError('Failed to delete job');
    }
  };

  const handleApply = async (job: JobResponse) => {
    try {
      await ApplicationsService.createApplicationApiV1ApplicationsPost({
        requestBody: {
          job_id: job.id,
          status: 'interested',
          notes: 'Applied via job management',
        },
      });
      // Show success message or update UI
      alert('Application created successfully!');
    } catch (err) {
      setError('Failed to create application');
    }
  };

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

  // Memoize filtered and sorted jobs to prevent unnecessary recalculations
  const filteredAndSortedJobs = useMemo(() => {
    return jobs
      .filter(job => {
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
      })
      .sort((a, b) => {
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
  }, [jobs, searchTerm, sourceFilter, typeFilter, sortBy, activeQuickFilters]);

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
          <Button2
            onClick={handleScrapeJobs}
            disabled={isScraping}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${isScraping ? 'animate-spin' : ''}`} />
            <span>{isScraping ? 'Finding Jobs...' : 'Find Jobs'}</span>
          </Button2>
          <Button2 onClick={openAddModal} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Add Job</span>
          </Button2>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-center p-4">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-800 ml-3">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <StickyFilterPanel>
        <Card>
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
              />

              <Select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                options={[
                  { value: 'all', label: 'All Types' },
                  ...JOB_TYPES,
                ]}
              />
            </div>

            <div className="mt-4">
              <QuickFilterChips
                filters={[
                  { label: 'Remote', value: 'remote' },
                  { label: 'Full-time', value: 'full-time' },
                  { label: 'React', value: 'react' },
                ]}
                activeFilters={activeQuickFilters}
                onFilterChange={(filterValue) => {
                  setActiveQuickFilters(prev =>
                    prev.includes(filterValue)
                      ? prev.filter(f => f !== filterValue)
                      : [...prev, filterValue],
                  );
                }}
              />
            </div>

            <div className="mt-4">
              <SavedFilters
                filters={savedFilters}
                onSave={handleSaveFilter}
                onApply={handleApplyFilter}
                onDelete={handleDeleteFilter}
              />
            </div>

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
        </Card>
      </StickyFilterPanel>

      {showComparisonView && (
        <JobComparisonView
          jobs={jobs.filter(job => job.id && selectedJobIds.includes(job.id))}
          onClose={() => setShowComparisonView(false)}
        />
      )}

      {/* Job Form Modal */}
      <Modal
        isOpen={showJobModal}
        onClose={closeModal}
        title={editingJob ? 'Edit Job' : 'Add New Job'}
        size="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Company *"
              value={formData.company}
              onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
              error={formErrors.company}
              placeholder="Enter company name"
            />

            <Input
              label="Job Title *"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              error={formErrors.title}
              placeholder="Enter job title"
            />

            <Input
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              placeholder="e.g., San Francisco, CA or Remote"
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
            />

            <Input
              label="Job URL"
              type="url"
              value={formData.url}
              onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
              error={formErrors.url}
              placeholder="https://..."
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

          <ModalFooter>
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
          </ModalFooter>
        </form>
      </Modal>

      {/* Jobs List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-neutral-200 rounded w-1/4 mb-2"></div>
                <div className="h-6 bg-neutral-200 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <AnimatePresence mode="wait">
          {currentView === 'list' ? (
            <JobListView
              key={listKey}
              jobs={filteredAndSortedJobs}
              onJobClick={(jobId) => console.log('View job:', jobId)}
              selectedJobIds={selectedJobIds}
              onSelectJob={handleSelectJob}
            />
          ) : (
            <JobTableView
              key={listKey}
              jobs={filteredAndSortedJobs}
              onJobClick={(jobId) => console.log('View job:', jobId)}
              selectedJobIds={selectedJobIds}
              onSelectJob={handleSelectJob}
            />
          )}
        </AnimatePresence>
      )}
    </div>
  );
}