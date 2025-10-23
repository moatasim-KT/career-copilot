'use client';

import { useState, useEffect } from 'react';
import { apiClient, type Job } from '@/lib/api';
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
  X
} from 'lucide-react';

const JOB_TYPES = ['full-time', 'part-time', 'contract', 'internship'];
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
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);

  const [formData, setFormData] = useState({
    company: '',
    title: '',
    location: '',
    url: '',
    salary_range: '',
    job_type: 'full-time' as const,
    description: '',
    remote: false,
    tech_stack: [] as string[],
    responsibilities: '',
    source: 'manual'
  });

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.company || !formData.title) {
      setError('Company and Job Title are required');
      return;
    }

    try {
      const response = editingJob
        ? await apiClient.updateJob(editingJob.id, formData)
        : await apiClient.createJob(formData);

      if (response.error) {
        setError(response.error);
      } else {
        setShowAddForm(false);
        setEditingJob(null);
        resetForm();
        loadJobs();
      }
    } catch (err) {
      setError('Failed to save job');
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
  };

  const startEdit = (job: Job) => {
    setEditingJob(job);
    setFormData({
      company: job.company,
      title: job.title,
      location: job.location || '',
      url: job.url || '',
      salary_range: job.salary_range || '',
      job_type: job.job_type as any,
      description: job.description || '',
      remote: job.remote,
      tech_stack: job.tech_stack || [],
      responsibilities: job.responsibilities || '',
      source: job.source
    });
    setShowAddForm(true);
  };

  const filteredJobs = jobs.filter(job =>
    job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (job.location && job.location.toLowerCase().includes(searchTerm.toLowerCase()))
  );

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
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Job Management</h1>
        <button
          onClick={() => {
            setShowAddForm(true);
            setEditingJob(null);
            resetForm();
          }}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Job</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search jobs by title, company, or location..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Add/Edit Job Form */}
      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editingJob ? 'Edit Job' : 'Add New Job'}
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false);
                setEditingJob(null);
                resetForm();
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company *
                </label>
                <input
                  type="text"
                  required
                  value={formData.company}
                  onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Type
                </label>
                <select
                  value={formData.job_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, job_type: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {JOB_TYPES.map(type => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Salary Range
                </label>
                <input
                  type="text"
                  placeholder="e.g., $80k-$120k"
                  value={formData.salary_range}
                  onChange={(e) => setFormData(prev => ({ ...prev, salary_range: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job URL
                </label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tech Stack
              </label>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2 max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
                {TECH_SKILLS.map(skill => (
                  <label key={skill} className="flex items-center space-x-1 text-xs">
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
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Responsibilities
              </label>
              <textarea
                rows={3}
                value={formData.responsibilities}
                onChange={(e) => setFormData(prev => ({ ...prev, responsibilities: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Key responsibilities for this role..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Full job description..."
              />
            </div>

            <div className="flex space-x-3">
              <button
                type="submit"
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <CheckCircle className="h-4 w-4" />
                <span>{editingJob ? 'Update Job' : 'Add Job'}</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingJob(null);
                  resetForm();
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Jobs List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white p-6 rounded-lg shadow-sm border animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
              <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : filteredJobs.length > 0 ? (
        <div className="space-y-4">
          {filteredJobs.map((job) => (
            <div key={job.id} className="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow">
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
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
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
                      <span className="capitalize">{job.job_type}</span>
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
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                      title="View Job Posting"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                  <button
                    onClick={() => startEdit(job)}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Edit Job"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete Job"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Clock className="h-4 w-4" />
                  <span>
                    Added {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Recently'}
                  </span>
                </div>
                <button
                  onClick={() => handleApply(job)}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">
            {searchTerm ? 'No jobs found matching your search' : 'No jobs added yet'}
          </p>
          <p className="text-sm text-gray-500 mb-4">
            {searchTerm ? 'Try adjusting your search terms' : 'Start by adding your first job opportunity'}
          </p>
          {!searchTerm && (
            <button
              onClick={() => {
                setShowAddForm(true);
                setEditingJob(null);
                resetForm();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add Your First Job
            </button>
          )}
        </div>
      )}
    </div>
  );
}