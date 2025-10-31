'use client';

import { ReactNode, memo } from 'react';

import { cn } from '@/lib/utils';

interface CardProps {
	children: ReactNode;
	className?: string;
	padding?: 'sm' | 'md' | 'lg';
	hover?: boolean;
}

const paddingClasses = {
	sm: 'p-4',
	md: 'p-6',
	lg: 'p-8',
};

const Card = memo(({
  children,
  className,
  padding = 'md',
  hover = false,
  ...rest
}: CardProps) => {
  return (
    <div
      className={cn(
        'bg-white rounded-lg border border-gray-200 shadow-sm',
        paddingClasses[padding],
        hover && 'hover:shadow-md transition-shadow duration-200',
        className,
      )}
      {...rest}
    >      {children}
		</div>
	);
});

export default Card;

export function CardHeader({ 
  children, 
  className, 
}: { 
  children: ReactNode; 
  className?: string; 
}) {
  return (
    <div className={cn('mb-4', className)}>
      {children}
    </div>
  );
}

export function CardTitle({ 
  children, 
  className, 
}: { 
  children: ReactNode; 
  className?: string; 
}) {
  return (
    <h3 className={cn('text-lg font-semibold text-gray-900', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ 
  children, 
  className, 
}: { 
  children: ReactNode; 
  className?: string; 
}) {
  return (
    <div className={cn(className)}>
      {children}
    </div>
  );
}