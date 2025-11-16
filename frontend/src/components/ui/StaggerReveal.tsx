'use client';

import { ReactNode, forwardRef, HTMLAttributes } from 'react';

import {
  staggerRevealContainer,
  staggerRevealItem,
  fastStaggerContainer,
  fastStaggerItem,
} from '@/lib/animations';
import { m } from '@/lib/motion';
import { cn } from '@/lib/utils';

export interface StaggerRevealProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Items to reveal with stagger animation
   */
  children: ReactNode;

  /**
   * Speed of the stagger animation
   */
  speed?: 'fast' | 'normal';

  /**
   * Whether to animate on mount
   */
  animate?: boolean;

  /**
   * Custom stagger delay between items (in seconds)
   */
  staggerDelay?: number;

  /**
   * Custom delay before starting animation (in seconds)
   */
  initialDelay?: number;
}

/**
 * StaggerReveal - Container for stagger reveal animations
 * 
 * Features:
 * - Reveals children sequentially with smooth animations
 * - Fast and normal speed options
 * - Customizable timing
 * - Accessible
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <StaggerReveal>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </StaggerReveal>
 * 
 * // Fast stagger for list items
 * <StaggerReveal speed="fast">
 *   {items.map(item => (
 *     <StaggerRevealItem key={item.id}>
 *       <ListItem item={item} />
 *     </StaggerRevealItem>
 *   ))}
 * </StaggerReveal>
 * 
 * // Custom timing
 * <StaggerReveal staggerDelay={0.1} initialDelay={0.2}>
 *   <Card>Card 1</Card>
 *   <Card>Card 2</Card>
 * </StaggerReveal>
 * ```
 */
export const StaggerReveal = forwardRef<HTMLDivElement, StaggerRevealProps>(
  (
    {
      children,
      speed = 'normal',
      animate = true,
      staggerDelay,
      initialDelay,
      className,
      ...props
    },
    ref,
  ) => {
    const containerVariants = speed === 'fast' ? fastStaggerContainer : staggerRevealContainer;

    // Create custom variants if custom timing is provided
    const customVariants = (staggerDelay !== undefined || initialDelay !== undefined) ? {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: staggerDelay ?? (speed === 'fast' ? 0.05 : 0.08),
          delayChildren: initialDelay ?? (speed === 'fast' ? 0.05 : 0.1),
        },
      },
    } : containerVariants;

    return (
      <m.div
        ref={ref}
        variants={customVariants}
        initial={animate ? 'hidden' : 'visible'}
        animate="visible"
        className={cn(className)}
        {...(props as any)}
      >
        {children}
      </m.div>
    );
  },
);

StaggerReveal.displayName = 'StaggerReveal';

export interface StaggerRevealItemProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Content to reveal
   */
  children: ReactNode;

  /**
   * Speed of the animation (should match parent)
   */
  speed?: 'fast' | 'normal';

  /**
   * Custom animation duration (in seconds)
   */
  duration?: number;
}

/**
 * StaggerRevealItem - Individual item in a stagger reveal animation
 * 
 * Use this component to wrap each child in a StaggerReveal container
 * for proper animation sequencing.
 * 
 * @example
 * ```tsx
 * <StaggerReveal>
 *   <StaggerRevealItem>
 *     <Card>Card 1</Card>
 *   </StaggerRevealItem>
 *   <StaggerRevealItem>
 *     <Card>Card 2</Card>
 *   </StaggerRevealItem>
 * </StaggerReveal>
 * ```
 */
export const StaggerRevealItem = forwardRef<HTMLDivElement, StaggerRevealItemProps>(
  (
    {
      children,
      speed = 'normal',
      duration,
      className,
      ...props
    },
    ref,
  ) => {
    const itemVariants = speed === 'fast' ? fastStaggerItem : staggerRevealItem;

    // Create custom variants if custom duration is provided
    const customVariants = duration !== undefined ? {
      hidden: itemVariants.hidden,
      visible: {
        ...itemVariants.visible,
        transition: {
          ...(typeof itemVariants.visible === 'object' && 'transition' in itemVariants.visible
            ? itemVariants.visible.transition
            : {}),
          duration,
        },
      },
    } : itemVariants;

    return (
      <m.div
        ref={ref}
        variants={customVariants}
        className={cn(className)}
        {...(props as any)}
      >
        {children}
      </m.div>
    );
  },
);

StaggerRevealItem.displayName = 'StaggerRevealItem';

export default StaggerReveal;
