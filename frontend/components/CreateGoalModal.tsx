import React, { useState } from 'react';
import { Button } from './ui/Button';
import { XMarkIcon, FlagIcon, CalendarIcon, HashtagIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../utils/api';

interface CreateGoalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGoalCreated: () => void;
}

interface GoalFormData {
  goal_type: string;
  title: string;
  description: string;
  target_value: number;
  unit: string;
  start_date: string;
  end_date: string;
  category: string;
  priority: string;
  reminder_frequency: string;
}

const GOAL_TYPES = [
  { value: 'daily_applications', label: 'Daily Applications', unit: 'applications' },
  { value: 'weekly_applications', label: 'Weekly Applications', unit: 'applications' },
  { value: 'monthly_applications', label: 'Monthly Applications', unit: 'applications' },
  { value: 'skill_development', label: 'Skill Development', unit: 'skills' },
  { value: 'interview_preparation', label: 'Interview Preparation', unit: 'sessions' },
  { value: 'networking', label: 'Networking', unit: 'connections' },
  { value: 'portfolio_building', label: 'Portfolio Building', unit: 'projects' },
  { value: 'certification', label: 'Certification', unit: 'certifications' }
];

const PRIORITIES = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' }
];

const REMINDER_FREQUENCIES = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'never', label: 'Never' }
];

const CreateGoalModal: React.FC<CreateGoalModalProps> = ({ 
  isOpen, 
  onClose, 
  onGoalCreated 
}) => {
  const [formData, setFormData] = useState<GoalFormData>({
    goal_type: 'weekly_applications',
    title: '',
    description: '',
    target_value: 5,
    unit: 'applications',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    category: 'job_search',
    priority: 'medium',
    reminder_frequency: 'daily'
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'goal_type') {
      const selectedType = GOAL_TYPES.find(type => type.value === value);
      setFormData(prev => ({
        ...prev,
        [name]: value,
        unit: selectedType?.unit || 'items',
        title: selectedType?.label || ''
      }));
    } else if (name === 'target_value') {
      setFormData(prev => ({
        ...prev,
        [name]: parseInt(value) || 0
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          milestones: generateMilestones(formData.target_value)
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create goal');
      }
      
      onGoalCreated();
      onClose();
      
      // Reset form
      setFormData({
        goal_type: 'weekly_applications',
        title: '',
        description: '',
        target_value: 5,
        unit: 'applications',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        category: 'job_search',
        priority: 'medium',
        reminder_frequency: 'daily'
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create goal');
    } finally {
      setLoading(false);
    }
  };

  const generateMilestones = (targetValue: number) => {
    const milestones = [];
    const quarterMark = Math.floor(targetValue * 0.25);
    const halfMark = Math.floor(targetValue * 0.5);
    const threeQuarterMark = Math.floor(targetValue * 0.75);

    if (quarterMark > 0) {
      milestones.push({
        value: quarterMark,
        message: "Great start! You're making progress!",
        achieved: false
      });
    }

    if (halfMark > quarterMark) {
      milestones.push({
        value: halfMark,
        message: "Halfway there! Keep up the momentum!",
        achieved: false
      });
    }

    if (threeQuarterMark > halfMark) {
      milestones.push({
        value: threeQuarterMark,
        message: "Almost there! The finish line is in sight!",
        achieved: false
      });
    }

    return milestones;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <FlagIcon className="h-5 w-5" />
            Create New Goal
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Goal Type
            </label>
            <select
              name="goal_type"
              value={formData.goal_type}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {GOAL_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Goal Title
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter goal title"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe your goal..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Value
              </label>
              <div className="relative">
                <HashtagIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="number"
                  name="target_value"
                  value={formData.target_value}
                  onChange={handleInputChange}
                  min="1"
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Unit
              </label>
              <input
                type="text"
                name="unit"
                value={formData.unit}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleInputChange}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleInputChange}
                  min={formData.start_date}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {PRIORITIES.map(priority => (
                  <option key={priority.value} value={priority.value}>
                    {priority.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reminders
              </label>
              <select
                name="reminder_frequency"
                value={formData.reminder_frequency}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {REMINDER_FREQUENCIES.map(freq => (
                  <option key={freq.value} value={freq.value}>
                    {freq.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="flex-1"
            >
              {loading ? 'Creating...' : 'Create Goal'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateGoalModal;