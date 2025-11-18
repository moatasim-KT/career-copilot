
import { Briefcase, MapPin, DollarSign, TrendingUp, Code, Award, Globe, CheckCircle } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import type { Job } from '@/types/job';

interface JobCardProps {
  job: Job;
  variant?: 'default' | 'compact' | 'featured';
  onSelect?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  isSelected?: boolean;
}

export default function JobCard({ job, variant = 'default', isSelected = false, onSelect }: JobCardProps) {
  const companyName = typeof job.company === 'string' ? job.company : job.company.name;

  if (variant === 'compact') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
          <p className="text-sm text-gray-600">{companyName}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">{job.location}</p>
          <p className="text-xs text-gray-500">{job.postedAt || 'Recently posted'}</p>
        </div>
      </div>
    );
  }

  if (variant === 'featured') {
    return (
      <div className="bg-blue-50 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-blue-900">{job.title}</h3>
          <span className="bg-blue-200 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">Featured</span>
        </div>
        <p className="text-md text-blue-800 mt-1">{companyName}</p>
        <div className="flex items-center text-sm text-blue-700 mt-4">
          <Briefcase className="w-4 h-4 mr-2" />
          <span>{job.type || 'Full-time'}</span>
          <MapPin className="w-4 h-4 ml-4 mr-2" />
          <span>{job.location}</span>
        </div>
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-blue-600">{job.postedAt || 'Recently posted'}</p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">Apply Now</button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 relative hover:shadow-md transition-shadow ${isSelected ? 'ring-2 ring-blue-500' : ''}`}>
      {onSelect && (
        <input
          type="checkbox"
          className="absolute top-3 right-3 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          checked={isSelected}
          onChange={onSelect}
        />
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
            {job.company_verified && (
              <CheckCircle className="w-5 h-5 text-blue-500" aria-label="Verified Company" />
            )}
          </div>
          <p className="text-md text-gray-700 mt-1">{companyName}</p>
        </div>
        {job.source && (
          <Badge variant="info" size="sm" className="ml-2">
            {job.source}
          </Badge>
        )}
      </div>

      {/* Main Info */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mt-4">
        <div className="flex items-center">
          <Briefcase className="w-4 h-4 mr-1.5" />
          <span>{job.type || 'Full-time'}</span>
        </div>
        <div className="flex items-center">
          <MapPin className="w-4 h-4 mr-1.5" />
          <span>{job.location}</span>
        </div>
        {job.experience_level && (
          <div className="flex items-center">
            <Award className="w-4 h-4 mr-1.5" />
            <span>{job.experience_level}</span>
          </div>
        )}
        {job.job_language && job.job_language !== 'en' && (
          <div className="flex items-center">
            <Globe className="w-4 h-4 mr-1.5" />
            <span>{job.job_language.toUpperCase()}</span>
          </div>
        )}
      </div>

      {/* Salary & Equity */}
      {(job.salary_range || job.equity_range) && (
        <div className="flex flex-wrap gap-3 mt-3">
          {job.salary_range && (
            <div className="flex items-center text-sm text-green-700 bg-green-50 px-3 py-1 rounded-full">
              <DollarSign className="w-4 h-4 mr-1" />
              <span className="font-medium">{job.salary_range}</span>
            </div>
          )}
          {job.equity_range && (
            <div className="flex items-center text-sm text-purple-700 bg-purple-50 px-3 py-1 rounded-full">
              <TrendingUp className="w-4 h-4 mr-1" />
              <span className="font-medium">{job.equity_range}</span>
            </div>
          )}
        </div>
      )}

      {/* Funding Stage */}
      {job.funding_stage && (
        <div className="mt-3">
          <Badge variant="primary" size="sm">
            {job.funding_stage}
          </Badge>
        </div>
      )}

      {/* Tech Stack */}
      {job.tech_stack && job.tech_stack.length > 0 && (
        <div className="mt-3">
          <div className="flex items-center gap-2 flex-wrap">
            <Code className="w-4 h-4 text-gray-500" />
            {job.tech_stack.slice(0, 5).map((tech, idx) => (
              <Badge key={idx} variant="default" size="sm">
                {tech}
              </Badge>
            ))}
            {job.tech_stack.length > 5 && (
              <span className="text-xs text-gray-500">+{job.tech_stack.length - 5} more</span>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
        <p className="text-xs text-gray-500">{job.postedAt || 'Recently posted'}</p>
        <button className="px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium">
          View Details
        </button>
      </div>
    </div>
  );
}
