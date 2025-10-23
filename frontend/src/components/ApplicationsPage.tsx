'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, type Application } from '@/lib/api';
import { useApplicationStatusUpdates } from '@/hooks/useWebSocket';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Select from '@/components/ui/Select';
import Modal, { ModalFooter } from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
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
  Filter,
  Search,
  SortAsc,
  SortDesc
} from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'interested', label: 'Interested' },
  { value: 'applied', label: 'Applied' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'declined', label: 'Declined' }
];

const SORT_OPTIONS = [
  { value: 'created_at_desc', label: 'Newest First' },
  { value: 'created_at_asc', label: 'Oldest First' },
  { value: 'applied_date_desc', label: 'Recently Applied' },
  { value: 'applied_date_asc', label: 'Oldest Applied' },
  { value: 'status_asc', label: 'Status A-Z' },
  { value: 'company_asc', label: 'Company A-Z' }
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

  // Handle real-time application status updates
  const handleApplicationUpdate = useCallback((data: any) => {
    console.log('Application update received:', data);
    if (data.application) {
      setApplications(prev => 
        prev.map(app => 
          app.id === data.application.id 
            ? { ...app, ...data.application }
            : app
        )
      );
      setLastUpdated(new Date());
    }
  }, []);

  // Set up WebSocket listener for application updates
  useApplicationStatusUpdates(handleApplicationUpdate);

  const [formData, setFormData] = useState({
    job_id: 0,
    status: 'interested' as Application['status'],
    notes: '',
    applied_date: '',
    interview_date: '',
    response_date: ''
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
    } catch (err) {
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
    } catch (err) {
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
    } catch (err) {
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
      response_date: ''
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
      response_date: application.response_date ? application.response_date.split('T')[0] : ''
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
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
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
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredAndSortedApplications = applications
    .filter(app => {
      const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
      const matchesSearch = 
        (app.job?.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (app.job?.company || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (app.notes || '').toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesStatus && matchesSearch;
    })
    .sort((a, b) => {
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Applications</h1>
          <p className="text-gray-600 mt-1">
            Track your job applications and their progress
          </p>
          {lastUpdated && (
            <p className="text-sm text-gray-500 mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <Button 
            variant="outline" 
            onClick={loadApplications}
            disabled={isLoading}
            className="flex items-center space-x-2"
          >
            <FileText className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Loading...' : 'Refresh'}</span>
          </Button>
          <Button onClick={openAddModal} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Add Application</span>
          </Button>
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
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search applications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              options={[
                { value: 'all', label: 'All Status' },
                ...STATUS_OPTIONS
              ]}
            />
            
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              options={SORT_OPTIONS}
            />
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              Showing {filteredAndSortedApplications.length} of {applications.length} applications
              {statusFilter !== 'all' && ` with status: ${statusFilter}`}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Application Form Modal */}
      <Modal
        isOpen={showApplicationModal}
        onClose={closeModal}
        title={editingApplication ? 'Edit Application' : 'Add New Application'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <Select
            label="Job *"
            value={formData.job_id.toString()}
            onChange={(e) => setFormData(prev => ({ ...prev, job_id: parseInt(e.target.value) || 0 }))}
            options={[
              { value: '0', label: 'Select a job...' },
              // Note: In a real implementation, you'd fetch available jobs
              // For now, this is a placeholder
            ]}
          />

          <Select
            label="Status"
            value={formData.status}
            onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as Application['status'] }))}
            options={STATUS_OPTIONS}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Applied Date"
              type="date"
              value={formData.applied_date}
              onChange={(e) => setFormData(prev => ({ ...prev, applied_date: e.target.value }))}
            />

            <Input
              label="Interview Date"
              type="date"
              value={formData.interview_date}
              onChange={(e) => setFormData(prev => ({ ...prev, interview_date: e.target.value }))}
            />

            <Input
              label="Response Date"
              type="date"
              value={formData.response_date}
              onChange={(e) => setFormData(prev => ({ ...prev, response_date: e.target.value }))}
            />
          </div>

          <Textarea
            label="Notes"
            rows={4}
            value={formData.notes}
            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
            placeholder="Add any notes about this application..."
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
              {editingApplication ? 'Update Application' : 'Add Application'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {filteredAndSortedApplications.length > 0 ? (
        <div className="space-y-4">
          {filteredAndSortedApplications.map((application) => (
            <Card key={application.id} hover className="transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {application.job?.title || 'Unknown Position'}
                      </h3>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(application.status)}
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(application.status)}`}>
                          {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3">
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
                      <p className="text-sm text-gray-600 mb-3">
                        <strong>Notes:</strong> {application.notes}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                      {application.interview_date && (
                        <span>Interview: {new Date(application.interview_date).toLocaleDateString()}</span>
                      )}
                      {application.response_date && (
                        <span>Response: {new Date(application.response_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => startEdit(application)}
                      title="Edit Application"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    
                    <Select
                      value={application.status}
                      onChange={(e) => updateApplicationStatus(application.id, e.target.value)}
                      options={STATUS_OPTIONS}
                      className="w-32"
                    />
                  </div>
                </div>

                {/* Interview Feedback Section */}
                {application.interview_feedback && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Interview Feedback</h4>
                    
                    {application.interview_feedback.questions && application.interview_feedback.questions.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-medium text-gray-700">Questions Asked:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {application.interview_feedback.questions.map((question, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              {question}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {application.interview_feedback.skill_areas && application.interview_feedback.skill_areas.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-medium text-gray-700">Skill Areas Discussed:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {application.interview_feedback.skill_areas.map((skill, idx) => (
                            <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {application.interview_feedback.notes && (
                      <div>
                        <p className="text-xs font-medium text-gray-700">Notes:</p>
                        <p className="text-sm text-gray-600 mt-1">{application.interview_feedback.notes}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Job Tech Stack */}
                {application.job?.tech_stack && application.job.tech_stack.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-xs font-medium text-gray-700 mb-2">Required Tech Stack:</p>
                    <div className="flex flex-wrap gap-1">
                      {application.job.tech_stack.slice(0, 10).map((tech) => (
                        <span key={tech} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                          {tech}
                        </span>
                      ))}
                      {application.job.tech_stack.length > 10 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          +{application.job.tech_stack.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || statusFilter !== 'all'
                ? 'No applications found'
                : 'No applications yet'
              }
            </h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || statusFilter !== 'all'
                ? 'Try adjusting your search terms or filters'
                : 'Start by adding jobs and creating applications to track your progress'
              }
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Button onClick={openAddModal}>
                Add Your First Application
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}