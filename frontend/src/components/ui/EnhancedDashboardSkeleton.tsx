
import Skeleton from './Skeleton2';

export default function EnhancedDashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex items-center space-x-3">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow-sm p-6">
                <Skeleton className="h-6 w-3/4 mb-4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            ))}
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <Skeleton className="h-6 w-1/4 mb-4" />
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4 py-2">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2 mt-1" />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <Skeleton className="h-6 w-1/2 mb-4" />
            {[...Array(4)].map((_, i) => (
              <div key={i} className="py-2">
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <Skeleton className="h-6 w-1/2 mb-4" />
            {[...Array(3)].map((_, i) => (
              <div key={i} className="py-2">
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
