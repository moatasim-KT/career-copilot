
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import { Maximize, Download } from 'lucide-react';

interface ChartWrapperProps {
  title: string;
  isLoading: boolean;
  error: boolean;
  children: React.ReactNode;
  onExport?: () => void;
  onFullScreen?: () => void;
}

const ChartWrapper: React.FC<ChartWrapperProps> = ({
  title,
  isLoading,
  error,
  children,
  onExport,
  onFullScreen,
}) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <div className="flex space-x-2">
          {onExport && (
            <Button variant="ghost" size="sm" onClick={onExport}>
              <Download className="h-4 w-4" />
            </Button>
          )}
          {onFullScreen && (
            <Button variant="ghost" size="sm" onClick={onFullScreen}>
              <Maximize className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : error ? (
          <div className="flex h-[300px] w-full items-center justify-center">
            <p className="text-red-500">Error loading chart data.</p>
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
};

export default ChartWrapper;
