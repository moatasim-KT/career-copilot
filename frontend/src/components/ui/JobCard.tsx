
import { Briefcase, MapPin, Clock } from 'lucide-react';

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  postedAt: string;
}

export interface JobCardProps {
  job: Job;
  variant?: 'default' | 'compact' | 'featured';
}

export default function JobCard({ job, variant = 'default' }: JobCardProps) {
  if (variant === 'compact') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
          <p className="text-sm text-gray-600">{job.company}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">{job.location}</p>
          <p className="text-xs text-gray-500">{job.postedAt}</p>
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
        <p className="text-md text-blue-800 mt-1">{job.company}</p>
        <div className="flex items-center text-sm text-blue-700 mt-4">
          <Briefcase className="w-4 h-4 mr-2" />
          <span>{job.type}</span>
          <MapPin className="w-4 h-4 ml-4 mr-2" />
          <span>{job.location}</span>
        </div>
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-blue-600">{job.postedAt}</p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">Apply Now</button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
      <p className="text-md text-gray-700 mt-1">{job.company}</p>
      <div className="flex items-center text-sm text-gray-600 mt-4">
        <Briefcase className="w-4 h-4 mr-2" />
        <span>{job.type}</span>
        <MapPin className="w-4 h-4 ml-4 mr-2" />
        <span>{job.location}</span>
      </div>
      <div className="flex items-center justify-between mt-4">
        <p className="text-xs text-gray-500">{job.postedAt}</p>
        <button className="px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors">View Details</button>
      </div>
    </div>
  );
}
