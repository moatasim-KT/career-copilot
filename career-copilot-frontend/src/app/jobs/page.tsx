'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getJobs, createJob, updateJob, deleteJob } from '@/lib/jobs';
import { allPossibleSkills } from '@/lib/constants';
import Cookies from 'js-cookie';

interface JobData {
  id: number;
  user_id: number;
  company: string;
  title: string;
  location?: string;
  description?: string;
  requirements?: string;
  responsibilities?: string;
  salary_range?: string;
  job_type?: string;
  remote_option?: string;
  tech_stack?: string[];
  documents_required?: string[];
  link?: string;
  source?: string;
  status: string;
  date_applied?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export default function JobsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddJobForm, setShowAddJobForm] = useState(false);
  const [editingJob, setEditingJob] = useState<JobData | null>(null);

  // Form states
  const [company, setCompany] = useState('');
  const [title, setTitle] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [requirements, setRequirements] = useState('');
  const [responsibilities, setResponsibilities] = useState('');
  const [salaryRange, setSalaryRange] = useState('');
  const [jobType, setJobType] = useState('full-time');
  const [remoteOption, setRemoteOption] = useState('onsite');
  const [techStack, setTechStack] = useState<string[]>([]);
  const [documentsRequired, setDocumentsRequired] = useState<string[]>([]);
  const [link, setLink] = useState('');
  const [source, setSource] = useState('manual');
  const [status, setStatus] = useState('not_applied');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    const storedToken = Cookies.get('auth_token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  useEffect(() => {
    if (token) {
      fetchJobs();
    }
  }, [token]);

  const fetchJobs = async () => {
    setLoading(true);
    const response = await getJobs(token!); // token is guaranteed to be non-null here
    if (response.error) {
      setError(response.error);
      if (response.error.includes('Authentication required')) {
        Cookies.remove('auth_token');
        router.push('/login');
      }
    } else if (response.data) {
      setJobs(response.data);
    }
    setLoading(false);
  };

  const resetForm = () => {
    setCompany('');
    setTitle('');
    setLocation('');
    setDescription('');
    setRequirements('');
    setResponsibilities('');
    setSalaryRange('');
    setJobType('full-time');
    setRemoteOption('onsite');
    setTechStack([]);
    setDocumentsRequired([]);
    setLink('');
    setSource('manual');
    setStatus('not_applied');
    setNotes('');
    setEditingJob(null);
  };

  const handleAddJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const jobData = {
      company,
      title,
      location,
      description,
      requirements,
      responsibilities,
      salary_range: salaryRange,
      job_type: jobType,
      remote_option: remoteOption,
      tech_stack: techStack,
      documents_required: documentsRequired,
      link,
      source,
      notes,
    };

    const response = await createJob(token!, jobData);
    if (response.error) {
      setError(response.error);
    } else {
      resetForm();
      setShowAddJobForm(false);
      fetchJobs();
    }
    setLoading(false);
  };

  const handleEditClick = (job: JobData) => {
    setEditingJob(job);
    setCompany(job.company);
    setTitle(job.title);
    setLocation(job.location || '');
    setDescription(job.description || '');
    setRequirements(job.requirements || '');
    setResponsibilities(job.responsibilities || '');
    setSalaryRange(job.salary_range || '');
    setJobType(job.job_type || 'full-time');
    setRemoteOption(job.remote_option || 'onsite');
    setTechStack(job.tech_stack || []);
    setDocumentsRequired(job.documents_required || []);
    setLink(job.link || '');
    setSource(job.source || 'manual');
    setStatus(job.status);
    setNotes(job.notes || '');
    setShowAddJobForm(true);
  };

  const handleUpdateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingJob) return;

    setLoading(true);
    setError(null);

    const jobData = {
      company,
      title,
      location,
      description,
      requirements,
      responsibilities,
      salary_range: salaryRange,
      job_type: jobType,
      remote_option: remoteOption,
      tech_stack: techStack,
      documents_required: documentsRequired,
      link,
      source,
      status,
      notes,
    };

    const response = await updateJob(token!, editingJob.id, jobData);
    if (response.error) {
      setError(response.error);
    } else {
      resetForm();
      setShowAddJobForm(false);
      fetchJobs();
    }
    setLoading(false);
  };

  const handleDeleteJob = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    setLoading(true);
    setError(null);

    const response = await deleteJob(token!, jobId);
    if (response.error) {
      setError(response.error);
    } else {
      fetchJobs();
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading jobs...</div>;
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Job Management</h1>

      <button
        onClick={() => {
          resetForm();
          setShowAddJobForm(true);
        }}
        className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mb-6"
      >
        Add New Job
      </button>

      {showAddJobForm && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{editingJob ? 'Edit Job' : 'Add New Job'}</h2>
          <form onSubmit={editingJob ? handleUpdateJob : handleAddJob}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label htmlFor="company" className="block text-gray-700 text-sm font-bold mb-2">Company</label>
                <input type="text" id="company" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={company} onChange={(e) => setCompany(e.target.value)} required />
              </div>
              <div>
                <label htmlFor="title" className="block text-gray-700 text-sm font-bold mb-2">Job Title</label>
                <input type="text" id="title" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={title} onChange={(e) => setTitle(e.target.value)} required />
              </div>
              <div>
                <label htmlFor="location" className="block text-gray-700 text-sm font-bold mb-2">Location</label>
                <input type="text" id="location" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={location} onChange={(e) => setLocation(e.target.value)} />
              </div>
              <div>
                <label htmlFor="link" className="block text-gray-700 text-sm font-bold mb-2">Job Link</label>
                <input type="url" id="link" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={link} onChange={(e) => setLink(e.target.value)} />
              </div>
              <div>
                <label htmlFor="salaryRange" className="block text-gray-700 text-sm font-bold mb-2">Salary Range</label>
                <input type="text" id="salaryRange" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={salaryRange} onChange={(e) => setSalaryRange(e.target.value)} />
              </div>
              <div>
                <label htmlFor="jobType" className="block text-gray-700 text-sm font-bold mb-2">Job Type</label>
                <select id="jobType" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={jobType} onChange={(e) => setJobType(e.target.value)}>
                  <option value="full-time">Full-time</option>
                  <option value="part-time">Part-time</option>
                  <option value="contract">Contract</option>
                  <option value="internship">Internship</option>
                </select>
              </div>
              <div>
                <label htmlFor="remoteOption" className="block text-gray-700 text-sm font-bold mb-2">Remote Option</label>
                <select id="remoteOption" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={remoteOption} onChange={(e) => setRemoteOption(e.target.value)}>
                  <option value="onsite">Onsite</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </div>
              <div>
                <label htmlFor="source" className="block text-gray-700 text-sm font-bold mb-2">Source</label>
                <input type="text" id="source" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={source} onChange={(e) => setSource(e.target.value)} />
              </div>
              <div>
                <label htmlFor="status" className="block text-gray-700 text-sm font-bold mb-2">Status</label>
                <select id="status" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" value={status} onChange={(e) => setStatus(e.target.value)}>
                  <option value="not_applied">Not Applied</option>
                  <option value="applied">Applied</option>
                  <option value="interviewing">Interviewing</option>
                  <option value="offer">Offer</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <div>
                <label htmlFor="techStack" className="block text-gray-700 text-sm font-bold mb-2">Tech Stack</label>
                <select
                  id="techStack"
                  multiple
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32"
                  value={techStack}
                  onChange={(e) => setTechStack(Array.from(e.target.options).filter(option => option.selected).map(option => option.value))}
                >
                  {allPossibleSkills.map((skill) => (
                    <option key={skill} value={skill}>{skill}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="documentsRequired" className="block text-gray-700 text-sm font-bold mb-2">Documents Required</label>
                <select
                  id="documentsRequired"
                  multiple
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32"
                  value={documentsRequired}
                  onChange={(e) => setDocumentsRequired(Array.from(e.target.options).filter(option => option.selected).map(option => option.value))}
                >
                  <option value="resume">Resume</option>
                  <option value="cover_letter">Cover Letter</option>
                  <option value="portfolio">Portfolio</option>
                  <option value="references">References</option>
                </select>
              </div>
            </div>
            <div className="mb-4">
              <label htmlFor="responsibilities" className="block text-gray-700 text-sm font-bold mb-2">Responsibilities</label>
              <textarea id="responsibilities" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32" value={responsibilities} onChange={(e) => setResponsibilities(e.target.value)}></textarea>
            </div>
            <div className="mb-6">
              <label htmlFor="description" className="block text-gray-700 text-sm font-bold mb-2">Description</label>
              <textarea id="description" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32" value={description} onChange={(e) => setDescription(e.target.value)}></textarea>
            </div>
            <div className="mb-6">
              <label htmlFor="notes" className="block text-gray-700 text-sm font-bold mb-2">Notes</label>
              <textarea id="notes" className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32" value={notes} onChange={(e) => setNotes(e.target.value)}></textarea>
            </div>
            {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowAddJobForm(false)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                disabled={loading}
              >
                {loading ? (editingJob ? 'Saving...' : 'Adding...') : (editingJob ? 'Save Changes' : 'Add Job')}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Your Tracked Jobs</h2>
        {jobs.length === 0 ? (
          <p>No jobs tracked yet. Add a new job to get started!</p>
        ) : (
          <ul>
            {jobs.map((job) => (
              <li key={job.id} className="border-b py-4 flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold">{job.title} at {job.company}</h3>
                  <p className="text-gray-600">{job.location} - {job.status}</p>
                  {job.tech_stack && job.tech_stack.length > 0 && (
                    <p className="text-sm text-gray-500">Tech Stack: {job.tech_stack.join(', ')}</p>
                  )}
                  {job.documents_required && job.documents_required.length > 0 && (
                    <p className="text-sm text-gray-500">Documents: {job.documents_required.join(', ')}</p>
                  )}
                </div>
                <div className="space-x-2">
                  <button
                    onClick={() => handleEditClick(job)}
                    className="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-3 rounded text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteJob(job.id)}
                    className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-3 rounded text-sm"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
