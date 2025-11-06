
import React from 'react';

import { cn } from '@/lib/utils';

export interface WidgetProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export default function Widget({ title, children, className }: WidgetProps) {
  return (
    <div className={cn('bg-white rounded-lg shadow-sm border p-6', className)}>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
      {children}
    </div>
  );
}
