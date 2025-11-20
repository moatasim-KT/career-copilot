
import Skeleton from './Skeleton2';

export default function JobCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <Skeleton className="h-6 w-3/4 mb-4" />
      <Skeleton className="h-4 w-1/2 mb-4" />
      <div className="flex items-center text-sm text-gray-600 mt-4">
        <Skeleton className="h-4 w-4 mr-2" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-4 ml-4 mr-2" />
        <Skeleton className="h-4 w-1/4" />
      </div>
      <div className="flex items-center justify-between mt-4">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-10 w-24" />
      </div>
    </div>
  );
}
