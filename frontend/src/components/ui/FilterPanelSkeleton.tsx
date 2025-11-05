
import Skeleton from './Skeleton';

export default function FilterPanelSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-6 w-1/4" />
        <Skeleton className="h-5 w-5" />
      </div>
      {[...Array(3)].map((_, i) => (
        <div key={i} className="border-b border-gray-200 py-4">
          <div className="w-full flex items-center justify-between">
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-5 w-5" />
          </div>
        </div>
      ))}
    </div>
  );
}
