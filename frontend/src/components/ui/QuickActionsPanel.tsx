
import { Plus, Upload, TrendingUp, Briefcase } from 'lucide-react';
import { useRouter } from 'next/navigation';
import QuickActionCard from './QuickActionCard';

export default function QuickActionsPanel() {
  const router = useRouter();

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
      <div className="space-y-3">
        <QuickActionCard
          title="Add New Job"
          description="Track a new opportunity"
          icon={Plus}
          iconColor="text-blue-600"
          onClick={() => router.push('/jobs?action=add')}
        />
        <QuickActionCard
          title="Upload Resume"
          description="Update your profile"
          icon={Upload}
          iconColor="text-purple-600"
          onClick={() => router.push('/resume')}
        />
        <QuickActionCard
          title="View Analytics"
          description="See detailed insights"
          icon={TrendingUp}
          iconColor="text-green-600"
          onClick={() => router.push('/analytics')}
        />
        <QuickActionCard
          title="Browse Jobs"
          description="Discover new opportunities"
          icon={Briefcase}
          iconColor="text-yellow-600"
          onClick={() => router.push('/jobs')}
        />
      </div>
    </div>
  );
}
