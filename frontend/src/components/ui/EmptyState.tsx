
import { Inbox } from 'lucide-react';

export interface EmptyStateProps {
  title: string;
  message: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <Inbox className="mx-auto h-12 w-12 text-gray-400" />
      <h3 className="mt-2 text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-600">{message}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
