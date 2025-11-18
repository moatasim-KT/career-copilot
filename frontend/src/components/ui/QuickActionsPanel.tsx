
import { Plus, Upload, TrendingUp, Briefcase } from 'lucide-react';
import { useRouter } from 'next/navigation';

import QuickActionCard from './QuickActionCard';

export default function QuickActionsPanel() {
  const router = useRouter();

  return (
    <div className="grid grid-cols-1 gap-3">
      <QuickActionCard
        title="Add New Job"
        description="Track a new opportunity manually"
        icon={Plus}
        iconColor="text-blue-600 dark:text-blue-400"
        onClick={() => router.push('/jobs?action=add')}
      />
      <QuickActionCard
        title="Upload Resume"
        description="Update your profile & CV"
        icon={Upload}
        iconColor="text-purple-600 dark:text-purple-400"
        onClick={() => router.push('/resume')}
      />
      <QuickActionCard
        title="View Analytics"
        description="See detailed insights & trends"
        icon={TrendingUp}
        iconColor="text-green-600 dark:text-green-400"
        onClick={() => router.push('/analytics')}
      />
      <QuickActionCard
        title="Browse Jobs"
        description="Discover new opportunities"
        icon={Briefcase}
        iconColor="text-amber-600 dark:text-amber-400"
        onClick={() => router.push('/jobs')}
      />
    </div>
  );
}
