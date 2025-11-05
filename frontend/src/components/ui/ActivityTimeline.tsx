
import { useState, useEffect } from 'react';
import { apiClient, type Application } from '@/lib/api';
import ActivityTimelineItem from './ActivityTimelineItem';
import { FileText, Calendar, Trophy, CheckCircle, XCircle, Clock } from 'lucide-react';

export default function ActivityTimeline() {
  const [activities, setActivities] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchActivities = async () => {
      setIsLoading(true);
      const response = await apiClient.getApplications();
      if (response.data) {
        setActivities(response.data);
      }
      setIsLoading(false);
    };

    fetchActivities();
  }, []);

  const getActivityIcon = (status: string) => {
    switch (status) {
      case 'applied':
        return FileText;
      case 'interview':
        return Calendar;
      case 'offer':
        return Trophy;
      case 'accepted':
        return CheckCircle;
      case 'rejected':
        return XCircle;
      default:
        return Clock;
    }
  };

  const getActivityColor = (status: string) => {
    switch (status) {
      case 'applied':
        return 'text-blue-600';
      case 'interview':
        return 'text-purple-600';
      case 'offer':
      case 'accepted':
        return 'text-green-600';
      case 'rejected':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="animate-pulse flex items-start space-x-3">
            <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
            <div className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {activities.map((activity) => (
        <ActivityTimelineItem
          key={activity.id}
          title={`Application ${activity.status}`}
          description={`${activity.job?.title || 'Unknown'} at ${activity.job?.company || 'Unknown Company'}`}
          timestamp={new Date(activity.applied_date || '')}
          icon={getActivityIcon(activity.status)}
          iconColor={getActivityColor(activity.status)}
        />
      ))}
    </div>
  );
}
