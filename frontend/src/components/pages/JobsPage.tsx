'use client';

import { useState, useEffect } from 'react';
import { apiClient, type Job } from '@/lib/api';
import Modal, { ModalFooter } from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
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
  StarOff
} from 'lucide-react';

const JOB_TYPES = [
  { value: 'full-time', label: 'Full-time' },
  { value: 'part-time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' }
];

const JOB_SOURCES = [
  { value: 'manual', label: 'Manual' },
  { value: 'scraped', label: 'Scraped' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'indeed', label: 'Indeed' },
  { value: 'glassdoor', label: 'Glassdoor' }
];

const SORT_OPTIONS = [
  { value: 'created_at_desc', label: 'Newest First' },
  { value: 'created_at_asc', label: 'Oldest First' },
  { value: 'company_asc', label: 'Company A-Z' },
  { value: 'company_desc', label: 'Company Z-A' },
  { value: 'title_asc', label: 'Title A-Z' },
  { value: 'title_desc', label: 'Title Z-A' },
  { value: 'match_score_desc', label: 'Best Match First' }
];

const TECH_SKILLS = [
  'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js',
  'Node.js', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'SQL', 'NoSQL',
  'PostgreSQL', 'MongoDB', 'Redis', 'Machine Learning', 'Data Science',
  'FastAPI', 'Django', 'Flask', 'Spring Boot', 'Go', 'Rust', 'C++', 'C#',
  '.NET', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Flutter', 'React Native',
  'GraphQL', 'REST API', 'Microservices', 'CI/CD', 'Git', 'Linux'
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showJobModal, setShowJobModal] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [sourceFilter, setSourceFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at_desc');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
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
    source: 'manual'
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.getJobs();
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setJobs(response.data);
      }
    } catch (err) {
      setError('Failed to load jobs');
    } finally {
      setIsLoading(false);
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
        ? await apiClient.updateJob(editingJob.id, formData)
        : await apiClient.createJob(formData);

      if (response.error) {
        setError(response.error);
      } else {
        setShowJobModal(false);
        setEditingJob(null);
        resetForm();
        loadJobs();
      }
    } catch (err) {
      setError('Failed to save job');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      const response = await apiClient.deleteJob(jobId);
      if (response.error) {
        setError(response.error);
      } else {
        loadJobs();
      }
    } catch (err) {
      setError('Failed to delete job');
    }
  };

  const handleApply = async (job: Job) => {
    try {
      const response = await apiClient.createApplication({
        job_id: job.id,
        status: 'interested',
        notes: 'Applied via job management'
      });

      if (response.error) {
        setError(response.error);
      } else {
        // Show success message or update UI
        alert('Application created successfully!');
      }
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
      source: 'manual'
    });
    setFormErrors({});
  };

  const startEdit = (job: Job) => {
    setEditingJob(job);
    setFormData({
      company: job.company,
      title: job.title,
      location: job.location || '',
      url: job.url || '',
      salary_range: job.salary_range || '',
      job_type: job.job_type,
      description: job.description || '',
      remote: job.remote,
      tech_stack: job.tech_stack || [],
      responsibilities: job.responsibilities || '',
      source: job.source
    });
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

  const filteredAndSortedJobs = jobs
    .filter(job => {
      const matchesSearch = 
        job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (job.location && job.location.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (job.tech_stack && job.tech_stack.some(tech => 
          tech.toLowerCase().includes(searchTerm.toLowerCase())
        ));
      
      const matchesSource = sourceFilter === 'all' || job.source === sourceFilter;
      const matchesType = typeFilter === 'all' || job.job_type === typeFilter;
      
      return matchesSearch && matchesSource && matchesType;
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

  const getSourceBadgeColor = (source: string) => {
    switch (source.toLowerCase()) {
      case 'manual': return 'bg-gray-100 text-gray-800';
      case 'scraped': return 'bg-blue-100 text-blue-800';
      case 'linkedin': return 'bg-blue-100 text-blue-800';
      case 'indeed': return 'bg-green-100 text-green-800';
      case 'glassdoor': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold text-gray-900">Job Management</h1>
          <p className="text-gray-600 mt-1">
            Manage your job opportunities and track applications
          </p>
        </div>
        <Button onClick={openAddModal} className="flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Add Job</span>
        </Button>
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
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
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
                ...JOB_SOURCES
              ]}
            />
            
            <Select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              options={[
                { value: 'all', label: 'All Types' },
                ...JOB_TYPES
              ]}
            />
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              Showing {filteredAndSortedJobs.length} of {jobs.length} jobs
            </div>
            
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              options={SORT_OPTIONS}
              className="w-48"
            />
          </div>
        </CardContent>
      </Card>

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
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Remote Position</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tech Stack
            </label>
            <div className="grid grid-cols-3 md:grid-cols-4 gap-2 max-h-40 overflow-y-auto border border-gray-300 rounded-md p-3">
              {TECH_SKILLS.map(skill => (
                <label key={skill} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={formData.tech_stack.includes(skill)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData(prev => ({
                          ...prev,
                          tech_stack: [...prev.tech_stack, skill]
                        }));
                      } else {
                        setFormData(prev => ({
                          ...prev,
                          tech_stack: prev.tech_stack.filter(s => s !== skill)
                        }));
                      }
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{skill}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
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
            <Button
              type="button"
              variant="outline"
              onClick={closeModal}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting}
            >
              {editingJob ? 'Update Job' : 'Add Job'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Jobs List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredAndSortedJobs.length > 0 ? (
        <div className="space-y-4">
          {filteredAndSortedJobs.map((job) => (
            <Card key={job.id} hover className="transition-all duration-200" data-testid="job-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {job.title}
                      </h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSourceBadgeColor(job.source)}`}>
                        {job.source.toUpperCase()}
                      </span>
                      {job.match_score && (
                        <span className={`text-sm font-medium ${getMatchScoreColor(job.match_score)}`}>
                          {job.match_score.toFixed(0)}% Match
                        </span>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center space-x-1">
                        <Building className="h-4 w-4" />
                        <span>{job.company}</span>
                      </div>
                      {job.location && (
                        <div className="flex items-center space-x-1">
                          <MapPin className="h-4 w-4" />
                          <span>{job.location}</span>
                        </div>
                      )}
                      <div className="flex items-center space-x-1">
                        <Briefcase className="h-4 w-4" />
                        <span className="capitalize">{job.job_type.replace('-', ' ')}</span>
                      </div>
                      {job.remote && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          Remote
                        </span>
                      )}
                      {job.salary_range && (
                        <div className="flex items-center space-x-1">
                          <DollarSign className="h-4 w-4" />
                          <span>{job.salary_range}</span>
                        </div>
                      )}
                    </div>

                    {job.tech_stack && job.tech_stack.length > 0 && (
                      <div className="mb-3">
                        <div className="flex flex-wrap gap-1">
                          {job.tech_stack.slice(0, 8).map((tech) => (
                            <span
                              key={tech}
                              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                            >
                              {tech}
                            </span>
                          ))}
                          {job.tech_stack.length > 8 && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                              +{job.tech_stack.length - 8} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {job.responsibilities && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {job.responsibilities}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {job.url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(job.url, '_blank')}
                        title="View Job Posting"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => startEdit(job)}
                      title="Edit Job"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(job.id)}
                      title="Delete Job"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Clock className="h-4 w-4" />
                    <span>
                      Added {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Recently'}
                    </span>
                  </div>
                  <Button
                    onClick={() => handleApply(job)}
                    size="sm"
                  >
                    Apply
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || sourceFilter !== 'all' || typeFilter !== 'all' 
                ? 'No jobs found' 
                : 'No jobs added yet'
              }
            </h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || sourceFilter !== 'all' || typeFilter !== 'all'
                ? 'Try adjusting your search terms or filters'
                : 'Start by adding your first job opportunity to track your applications'
              }
            </p>
            {!searchTerm && sourceFilter === 'all' && typeFilter === 'all' && (
              <Button onClick={openAddModal}>
                Add Your First Job
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}