
import React from 'react';

import { cn } from '@/lib/utils';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Optional label for the textarea field */
  label?: string;
  /** Optional error message to display */
  error?: string;
  /** Visual variant of the textarea field */
  variant?: 'default' | 'ghost';
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, variant = 'default', ...props }, ref) => {
    const baseStyles = 'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';
    const variantStyles = {
      default: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
      ghost: 'border-transparent focus:border-transparent focus:ring-transparent',
    };

    return (
      <div className="grid w-full items-center gap-1.5">
        {label && (
          <label htmlFor={props.id || props.name} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            {label}
          </label>
        )}
        <textarea
          className={cn(baseStyles, variantStyles[variant], className, error && 'border-red-500')}
          ref={ref}
          {...props}
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>
    );
  },
);
Textarea.displayName = 'Textarea';

export default Textarea;
export { Textarea };
