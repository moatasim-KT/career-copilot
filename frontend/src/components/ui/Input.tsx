
import React from 'react';

import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Optional label for the input field */
  label?: string;
  /** Optional error message to display */
  error?: string;
  /** Visual variant of the input field */
  variant?: 'default' | 'ghost';
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, variant = 'default', type = 'text', ...props }, ref) => {
    const baseStyles = 'flex h-10 w-full rounded-lg border bg-white dark:bg-neutral-900 px-3 py-2 text-sm ring-offset-white dark:ring-offset-neutral-950 file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-neutral-500 dark:placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200';
    const variantStyles = {
      default: 'border-neutral-200 dark:border-neutral-800 focus-visible:border-primary-500 focus-visible:ring-primary-500/20',
      ghost: 'border-transparent bg-transparent shadow-none hover:bg-neutral-100 dark:hover:bg-neutral-800 focus-visible:ring-neutral-500',
    };

    return (
      <div className="grid w-full items-center gap-1.5">
        {label && (
          <label htmlFor={props.id || props.name} className="text-sm font-medium leading-none text-neutral-700 dark:text-neutral-300 peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            {label}
          </label>
        )}
        <input
          type={type}
          className={cn(baseStyles, variantStyles[variant], className, error && 'border-red-500 focus-visible:ring-red-500/20')}
          ref={ref}
          {...props}
        />
        {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
      </div>
    );
  },
);
Input.displayName = 'Input';

export default Input;
export { Input };
