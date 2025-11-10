
'use client';



import { motion, AnimatePresence } from 'framer-motion';
import type { MotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { forwardRef, ReactNode, ButtonHTMLAttributes, useRef, useState } from 'react';

import { cn } from '@/lib/utils';

export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, keyof MotionProps>, MotionProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success' | 'link' | 'gradient';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  loadingText?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  success?: boolean; // triggers success animation
  glow?: boolean; // adds glow effect
  pulse?: boolean; // adds pulse animation for critical actions
}

const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 shadow-sm',
  secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 focus-visible:ring-neutral-500 dark:bg-neutral-800 dark:text-neutral-100 dark:hover:bg-neutral-700',
  outline: 'border-2 border-neutral-300 bg-transparent hover:bg-neutral-50 focus-visible:ring-primary-500 dark:border-neutral-600 dark:hover:bg-neutral-800',
  ghost: 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-neutral-100',
  destructive: 'bg-error-600 text-white hover:bg-error-700 focus-visible:ring-error-500 shadow-sm',
  success: 'bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500 shadow-sm',
  link: 'text-primary-600 underline-offset-4 hover:underline dark:text-primary-400',
  gradient: 'bg-gradient-to-r from-primary-500 via-primary-600 to-primary-700 text-white hover:from-primary-600 hover:via-primary-700 hover:to-primary-800 focus-visible:ring-primary-500 shadow-sm bg-[length:200%_100%] bg-left hover:bg-right transition-all duration-500',
};

const sizes = {
  xs: 'h-7 px-2.5 text-xs rounded-md',
  sm: 'h-8 px-3 text-sm rounded-md',
  md: 'h-10 px-4 text-sm rounded-lg',
  lg: 'h-11 px-6 text-base rounded-lg',
  xl: 'h-12 px-8 text-base rounded-xl',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      loading = false,
      loadingText,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      className,
      disabled,
      type = 'button',
      success = false,
      glow = false,
      pulse = false,
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;
    const [ripple, setRipple] = useState<{ x: number; y: number } | null>(null);
    const [rippleActive, setRippleActive] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    const btnRef = useRef<HTMLButtonElement>(null);

    // Determine glow class based on variant
    const getGlowClass = () => {
      if (!glow) return '';
      
      const glowMap = {
        primary: isHovered ? 'glow-primary-hover' : 'glow-primary',
        gradient: isHovered ? 'glow-primary-hover' : 'glow-primary',
        success: isHovered ? 'glow-success-hover' : 'glow-success',
        destructive: isHovered ? 'glow-error-hover' : 'glow-error',
      };
      
      return glowMap[variant as keyof typeof glowMap] || '';
    };

    // Ripple effect handler
    const handleClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
      if (btnRef.current) {
        const rect = btnRef.current.getBoundingClientRect();
        setRipple({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
        });
        setRippleActive(false);
        setTimeout(() => setRippleActive(true), 10);
      }
      if (props.onClick) props.onClick(e);
    };

    return (
      <motion.button
        ref={(node) => {
          btnRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref) (ref as React.MutableRefObject<HTMLButtonElement | null>).current = node;
        }}
        type={type}
        disabled={isDisabled}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium',
          'transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          'relative overflow-hidden',
          variants[variant],
          sizes[size],
          fullWidth && 'w-full',
          'min-w-[44px] min-h-[44px]',
          getGlowClass(),
          pulse && 'pulse-glow',
          className,
        )}
        /* Touch device styles: remove hover, add active/pressed */

        
onClick = { handleClick }
{...props }
      >
  {/* Ripple effect */ }
  <AnimatePresence>
{
  ripple && rippleActive && (
    <motion.span
      key={`${ripple.x}-${ripple.y}`}
      initial={{ opacity: 0.3, scale: 0 }}
      animate={{ opacity: 0.15, scale: 6 }}
      exit={{ opacity: 0, scale: 8 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      style={{
        position: 'absolute',
        left: ripple.x,
        top: ripple.y,
        width: 24,
        height: 24,
        borderRadius: '50%',
        background: 'currentColor',
        pointerEvents: 'none',
        zIndex: 1,
        transform: 'translate(-50%, -50%)',
      }}
      onAnimationComplete={() => setRipple(null)}
    />
  )
}
        </AnimatePresence >
  {/* Success animation (checkmark bounce) */ }
  <AnimatePresence>
{
  success && !loading && (
    <motion.span
      key="success-check"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1.2, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <motion.path
          d="M5 10.5L9 14.5L15 7.5"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3 }}
        />
      </svg>
    </motion.span>
  )
}
        </AnimatePresence >
  {/* Button content */ }
  < span className = { success && !loading ? 'opacity-0' : 'relative z-10 flex items-center gap-2'}>
    { loading && <Loader2 className="h-4 w-4 animate-spin" />}
{ !loading && icon && iconPosition === 'left' && icon }
{ loading && loadingText ? loadingText : children }
{ !loading && icon && iconPosition === 'right' && icon }
        </span >
      </motion.button >
    );
  }
  ,
);

Button.displayName = 'Button';

export default Button;
