
import React from 'react';

import { cn } from '@/lib/utils';

export interface WidgetProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export default function Widget({ title, children, className }: WidgetProps) {
  return (
    <div className={cn('bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl rounded-2xl shadow-sm border border-white/20 dark:border-neutral-800 h-full flex flex-col transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/5', className)}>
      <div className="px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
        <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">{title}</h2>
      </div>
      <div className="p-6 flex-1">
        {children}
      </div>
    </div>
  );
}
