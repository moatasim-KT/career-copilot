/**
 * HelpIcon Component
 * 
 * A small "?" icon that displays helpful information in a popover.
 * Used next to complex features to provide contextual help.
 * 
 * Features:
 * - Hover or click to show popover
 * - Link to full documentation
 * - Consistent styling across the app
 * - Accessible with keyboard navigation
 * 
 * Usage:
 * ```tsx
 * <HelpIcon
 *   title="Advanced Search"
 *   content="Build complex queries with AND/OR logic..."
 *   docsLink="/help#advanced-search"
 * />
 * ```
 */

'use client';

import { HelpCircle, ExternalLink } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect, useCallback } from 'react';

import { logger } from '@/lib/logger';
import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

import { Popover, PopoverTrigger, PopoverContent } from './Popover';


export interface HelpIconProps {
  /**
   * Title of the help content
   */
  title?: string;

  /**
   * Main help content (can be string or React node)
   */
  content: React.ReactNode;

  /**
   * Optional link to full documentation
   */
  docsLink?: string;

  /**
   * Size of the icon
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Position of the popover
   */
  position?: 'top' | 'bottom' | 'left' | 'right';

  /**
   * Custom className for the icon button
   */
  className?: string;

  /**
   * Custom className for the popover content
   */
  contentClassName?: string;

  /**
   * Trigger on hover (default: true)
   */
  triggerOnHover?: boolean;

  /**
   * Aria label for accessibility
   */
  ariaLabel?: string;

  /**
   * Notifies parent when the popover open state changes
   */
  onOpenChange?: (open: boolean) => void;
}

const sizeStyles = {
  sm: 'h-3.5 w-3.5',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
};

const positionStyles = {
  top: 'bottom-full mb-2',
  bottom: 'top-full mt-2',
  left: 'right-full mr-2',
  right: 'left-full ml-2',
};

export function HelpIcon({
  title,
  content,
  docsLink,
  size = 'md',
  position = 'bottom',
  className,
  contentClassName,
  triggerOnHover = true,
  ariaLabel = 'Help',
  onOpenChange,
}: HelpIconProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const updateOpenState = useCallback((open: boolean) => {
    setIsOpen(open);
    onOpenChange?.(open);
  }, [onOpenChange]);

  const handleMouseEnter = () => {
    if (triggerOnHover) {
      setIsHovered(true);
      updateOpenState(true);
    }
  };

  const handleMouseLeave = () => {
    if (triggerOnHover) {
      setIsHovered(false);
      // Delay closing to allow moving to popover
      setTimeout(() => {
        if (!isHovered) {
          updateOpenState(false);
        }
      }, 100);
    }
  };

  const handleClick = () => {
    updateOpenState(!isOpen);
  };

  return (
    <Popover open={isOpen} onOpenChange={updateOpenState}>
      <PopoverTrigger asChild>
        <button
          type="button"
          onClick={handleClick}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className={cn(
            'inline-flex items-center justify-center',
            'rounded-full transition-colors',
            'text-neutral-500 hover:text-neutral-700',
            'dark:text-neutral-400 dark:hover:text-neutral-200',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            'dark:focus:ring-offset-neutral-900',
            className,
          )}
          aria-label={ariaLabel}
          aria-expanded={isOpen}
          aria-haspopup="dialog"
        >
          <HelpCircle className={cn(sizeStyles[size])} />
        </button>
      </PopoverTrigger>

      <PopoverContent
        className={cn(
          'w-80 p-0',
          positionStyles[position],
          contentClassName,
        )}
      >
        <div
          className="p-4"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => {
            setIsHovered(false);
            if (triggerOnHover) {
              updateOpenState(false);
            }
          }}
        >
          {/* Title */}
          {title && (
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
              {title}
            </h3>
          )}

          {/* Content */}
          <div className="text-sm text-neutral-600 dark:text-neutral-400 space-y-2">
            {typeof content === 'string' ? (
              <p>{content}</p>
            ) : (
              content
            )}
          </div>

          {/* Documentation Link */}
          {docsLink && (
            <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
              <Link
                href={docsLink}
                className={cn(
                  'inline-flex items-center gap-1.5',
                  'text-sm font-medium',
                  'text-primary-600 hover:text-primary-700',
                  'dark:text-primary-400 dark:hover:text-primary-300',
                  'transition-colors',
                )}
                onClick={() => setIsOpen(false)}
              >
                Learn more
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Inline Help Text Component
 * 
 * Displays help text inline without a popover.
 * Useful for form fields and simple explanations.
 */
export interface InlineHelpProps {
  children: React.ReactNode;
  className?: string;
}

export function InlineHelp({ children, className }: InlineHelpProps) {
  return (
    <p
      className={cn(
        'text-sm text-neutral-600 dark:text-neutral-400',
        'mt-1',
        className,
      )}
    >
      {children}
    </p>
  );
}

/**
 * Help Tooltip Component
 * 
 * A simpler tooltip-style help component for brief hints.
 * Uses native browser tooltip for better performance.
 */
export interface HelpTooltipProps {
  content: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function HelpTooltip({ content, size = 'md', className }: HelpTooltipProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center',
        'text-neutral-500 hover:text-neutral-700',
        'dark:text-neutral-400 dark:hover:text-neutral-200',
        'cursor-help transition-colors',
        className,
      )}
      title={content}
      aria-label={content}
    >
      <HelpCircle className={cn(sizeStyles[size])} />
    </span>
  );
}

/**
 * Feature Hint Component
 * 
 * Combines HelpIcon with first-time hint functionality.
 * Shows a pulsing indicator for features the user hasn't seen yet.
 */
export interface FeatureHintProps extends Omit<HelpIconProps, 'className'> {
  featureId: string;
  showPulse?: boolean;
  className?: string;
}

export function FeatureHint({
  featureId,
  showPulse = true,
  className,
  ...helpIconProps
}: FeatureHintProps) {
  const [hasBeenSeen, setHasBeenSeen] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const hints = localStorage.getItem('first-time-hints');
      if (hints) {
        const parsed = JSON.parse(hints);
        setHasBeenSeen(Boolean(parsed[featureId]?.seen));
      }
    } catch (error) {
      logger.error('Failed to check feature hint:', error);
    }
  }, [featureId]);

  const handleOpen = useCallback(() => {
    if (hasBeenSeen || typeof window === 'undefined') return;
    try {
      const hints = localStorage.getItem('first-time-hints');
      const parsed = hints ? JSON.parse(hints) : {};
      parsed[featureId] = {
        seen: true,
        dismissedAt: new Date().toISOString(),
      };
      localStorage.setItem('first-time-hints', JSON.stringify(parsed));
      setHasBeenSeen(true);
    } catch (error) {
      logger.error('Failed to mark feature hint as seen:', error);
    }
  }, [featureId, hasBeenSeen]);

  return (
    <div className={cn('relative inline-flex', className)}>
      <HelpIcon
        {...helpIconProps}
        onOpenChange={(open) => {
          if (open) handleOpen();
        }}
      />

      {/* Pulse indicator for unseen features */}
      {!hasBeenSeen && showPulse && (
        <m.span
          className="absolute -top-0.5 -right-0.5 flex h-2 w-2"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        >
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500" />
        </m.span>
      )}
    </div>
  );
}
