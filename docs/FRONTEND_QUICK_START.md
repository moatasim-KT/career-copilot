# Frontend Upgrade - Quick Start Guide

**Quick Links**: [[docs/index|Documentation Hub]] | [[frontend/README|Frontend README]] | [[frontend/docs/README|Frontend Features Hub]] | [[LOCAL_SETUP]] | [[DEVELOPER_GUIDE]]

**Related**:
- [[career-copilot/README|Project README]] - Project overview
- [[career-copilot/CONTRIBUTING|Contributing Guidelines]] - Contribution guidelines
- [[USER_GUIDE]] - User guide
- [[frontend/docs/README|Frontend Features Hub]] - **Frontend Features & Documentation Hub**
- [[ARCHITECTURE]] - System architecture
- [[code-patterns]] - Code patterns
- [[testing-strategies]] - Testing strategies

**Frontend Features Documented**:
- [[frontend/src/components/lazy/README|Lazy Loading & Code Splitting]]
- [[frontend/src/components/ui/loading/README|Loading States]]
- [[frontend/src/components/ui/DataTable/README|DataTable Component]]
- [[frontend/src/lib/SENTRY_INTEGRATION_GUIDE|Sentry Error Monitoring]]
- [[frontend/src/components/ui/__tests__/DARK_MODE_TEST_REPORT|Dark Mode Tests]]

## 🚀 Start Here: Week 1 Implementation

This guide provides step-by-step instructions to begin the frontend upgrade immediately.

---

## Day 1-2: Design Token System

### Step 1: Update `globals.css`

Replace the current minimal CSS with a comprehensive design system:

```css
/* frontend/src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* ============================================
       COLORS - Professional Blue/Gray Palette
       ============================================ */
    
    /* Primary Colors (Blue) */
    --color-primary-50: 239 246 255;   /* rgb(239 246 255) */
    --color-primary-100: 219 234 254;
    --color-primary-200: 191 219 254;
    --color-primary-300: 147 197 253;
    --color-primary-400: 96 165 250;
    --color-primary-500: 59 130 246;   /* Main brand color */
    --color-primary-600: 37 99 235;
    --color-primary-700: 29 78 216;
    --color-primary-800: 30 64 175;
    --color-primary-900: 30 58 138;
    --color-primary-950: 23 37 84;

    /* Neutral Colors (Blue-Gray) */
    --color-neutral-50: 248 250 252;
    --color-neutral-100: 241 245 249;
    --color-neutral-200: 226 232 240;
    --color-neutral-300: 203 213 225;
    --color-neutral-400: 148 163 184;
    --color-neutral-500: 100 116 139;
    --color-neutral-600: 71 85 105;
    --color-neutral-700: 51 65 85;
    --color-neutral-800: 30 41 59;
    --color-neutral-900: 15 23 42;
    --color-neutral-950: 2 6 23;

    /* Semantic Colors */
    --color-success-50: 240 253 244;
    --color-success-500: 34 197 94;
    --color-success-600: 22 163 74;
    --color-success-700: 21 128 61;

    --color-warning-50: 255 247 237;
    --color-warning-500: 251 146 60;
    --color-warning-600: 234 88 12;
    --color-warning-700: 194 65 12;

    --color-error-50: 254 242 242;
    --color-error-500: 239 68 68;
    --color-error-600: 220 38 38;
    --color-error-700: 185 28 28;

    --color-info-50: 239 246 255;
    --color-info-500: 59 130 246;
    --color-info-600: 37 99 235;
    --color-info-700: 29 78 216;

    /* Surface Colors */
    --background: 255 255 255;
    --foreground: 15 23 42;
    --card: 255 255 255;
    --card-foreground: 15 23 42;
    --popover: 255 255 255;
    --popover-foreground: 15 23 42;
    --muted: 241 245 249;
    --muted-foreground: 100 116 139;
    --border: 226 232 240;
    --input: 226 232 240;
    --ring: 59 130 246;

    /* ============================================
       SPACING SCALE (8px base)
       ============================================ */
    --space-0: 0;
    --space-1: 0.25rem;  /* 4px */
    --space-2: 0.5rem;   /* 8px */
    --space-3: 0.75rem;  /* 12px */
    --space-4: 1rem;     /* 16px */
    --space-5: 1.25rem;  /* 20px */
    --space-6: 1.5rem;   /* 24px */
    --space-8: 2rem;     /* 32px */
    --space-10: 2.5rem;  /* 40px */
    --space-12: 3rem;    /* 48px */
    --space-16: 4rem;    /* 64px */
    --space-20: 5rem;    /* 80px */
    --space-24: 6rem;    /* 96px */

    /* ============================================
       TYPOGRAPHY SCALE
       ============================================ */
    --font-size-xs: 0.75rem;      /* 12px */
    --font-size-sm: 0.875rem;     /* 14px */
    --font-size-base: 1rem;       /* 16px */
    --font-size-lg: 1.125rem;     /* 18px */
    --font-size-xl: 1.25rem;      /* 20px */
    --font-size-2xl: 1.5rem;      /* 24px */
    --font-size-3xl: 1.875rem;    /* 30px */
    --font-size-4xl: 2.25rem;     /* 36px */
    --font-size-5xl: 3rem;        /* 48px */
    --font-size-6xl: 3.75rem;     /* 60px */
    --font-size-7xl: 4.5rem;      /* 72px */

    /* Line Heights */
    --line-height-tight: 1.25;
    --line-height-normal: 1.5;
    --line-height-relaxed: 1.75;
    --line-height-loose: 2;

    /* ============================================
       SHADOWS (5 Elevation Levels)
       ============================================ */
    --shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
    --shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);

    /* Colored Shadows */
    --shadow-primary: 0 10px 15px -3px rgb(59 130 246 / 0.2);
    --shadow-success: 0 10px 15px -3px rgb(34 197 94 / 0.2);
    --shadow-error: 0 10px 15px -3px rgb(239 68 68 / 0.2);

    /* ============================================
       BORDER RADIUS
       ============================================ */
    --radius-none: 0;
    --radius-sm: 0.25rem;   /* 4px */
    --radius-base: 0.5rem;  /* 8px */
    --radius-md: 0.75rem;   /* 12px */
    --radius-lg: 1rem;      /* 16px */
    --radius-xl: 1.5rem;    /* 24px */
    --radius-2xl: 2rem;     /* 32px */
    --radius-full: 9999px;

    /* ============================================
       TRANSITIONS
       ============================================ */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slower: 500ms cubic-bezier(0.4, 0, 0.2, 1);

    /* ============================================
       Z-INDEX SCALE
       ============================================ */
    --z-index-dropdown: 1000;
    --z-index-sticky: 1020;
    --z-index-fixed: 1030;
    --z-index-modal-backdrop: 1040;
    --z-index-modal: 1050;
    --z-index-popover: 1060;
    --z-index-tooltip: 1070;
  }

  /* Dark Mode */
  .dark {
    --background: 15 23 42;
    --foreground: 248 250 252;
    --card: 30 41 59;
    --card-foreground: 248 250 252;
    --popover: 30 41 59;
    --popover-foreground: 248 250 252;
    --muted: 51 65 85;
    --muted-foreground: 148 163 184;
    --border: 51 65 85;
    --input: 51 65 85;
    --ring: 147 197 253;
  }

  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }

  /* ============================================
     UTILITY CLASSES
     ============================================ */
  .gradient-primary {
    background: linear-gradient(135deg, rgb(var(--color-primary-500)) 0%, rgb(var(--color-primary-600)) 100%);
  }

  .gradient-mesh {
    background: 
      radial-gradient(at 40% 20%, rgb(var(--color-primary-200)) 0px, transparent 50%),
      radial-gradient(at 80% 0%, rgb(var(--color-primary-300)) 0px, transparent 50%),
      radial-gradient(at 0% 50%, rgb(var(--color-primary-100)) 0px, transparent 50%),
      radial-gradient(at 80% 50%, rgb(var(--color-primary-200)) 0px, transparent 50%),
      radial-gradient(at 0% 100%, rgb(var(--color-primary-300)) 0px, transparent 50%),
      radial-gradient(at 80% 100%, rgb(var(--color-primary-200)) 0px, transparent 50%),
      radial-gradient(at 0% 0%, rgb(var(--color-primary-200)) 0px, transparent 50%);
  }

  .glass {
    @apply backdrop-blur-lg bg-white/70 dark:bg-neutral-900/70 border border-white/20;
  }

  .card-hover {
    @apply transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5;
  }
}

```

### Step 2: Update `tailwind.config.ts`

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'rgb(var(--color-primary-50) / <alpha-value>)',
          100: 'rgb(var(--color-primary-100) / <alpha-value>)',
          200: 'rgb(var(--color-primary-200) / <alpha-value>)',
          300: 'rgb(var(--color-primary-300) / <alpha-value>)',
          400: 'rgb(var(--color-primary-400) / <alpha-value>)',
          500: 'rgb(var(--color-primary-500) / <alpha-value>)',
          600: 'rgb(var(--color-primary-600) / <alpha-value>)',
          700: 'rgb(var(--color-primary-700) / <alpha-value>)',
          800: 'rgb(var(--color-primary-800) / <alpha-value>)',
          900: 'rgb(var(--color-primary-900) / <alpha-value>)',
          950: 'rgb(var(--color-primary-950) / <alpha-value>)',
        },
        neutral: {
          50: 'rgb(var(--color-neutral-50) / <alpha-value>)',
          100: 'rgb(var(--color-neutral-100) / <alpha-value>)',
          200: 'rgb(var(--color-neutral-200) / <alpha-value>)',
          300: 'rgb(var(--color-neutral-300) / <alpha-value>)',
          400: 'rgb(var(--color-neutral-400) / <alpha-value>)',
          500: 'rgb(var(--color-neutral-500) / <alpha-value>)',
          600: 'rgb(var(--color-neutral-600) / <alpha-value>)',
          700: 'rgb(var(--color-neutral-700) / <alpha-value>)',
          800: 'rgb(var(--color-neutral-800) / <alpha-value>)',
          900: 'rgb(var(--color-neutral-900) / <alpha-value>)',
          950: 'rgb(var(--color-neutral-950) / <alpha-value>)',
        },
        success: {
          50: 'rgb(var(--color-success-50) / <alpha-value>)',
          500: 'rgb(var(--color-success-500) / <alpha-value>)',
          600: 'rgb(var(--color-success-600) / <alpha-value>)',
          700: 'rgb(var(--color-success-700) / <alpha-value>)',
        },
        warning: {
          50: 'rgb(var(--color-warning-50) / <alpha-value>)',
          500: 'rgb(var(--color-warning-500) / <alpha-value>)',
          600: 'rgb(var(--color-warning-600) / <alpha-value>)',
          700: 'rgb(var(--color-warning-700) / <alpha-value>)',
        },
        error: {
          50: 'rgb(var(--color-error-50) / <alpha-value>)',
          500: 'rgb(var(--color-error-500) / <alpha-value>)',
          600: 'rgb(var(--color-error-600) / <alpha-value>)',
          700: 'rgb(var(--color-error-700) / <alpha-value>)',
        },
        background: 'rgb(var(--background) / <alpha-value>)',
        foreground: 'rgb(var(--foreground) / <alpha-value>)',
        border: 'rgb(var(--border) / <alpha-value>)',
        input: 'rgb(var(--input) / <alpha-value>)',
        ring: 'rgb(var(--ring) / <alpha-value>)',
        muted: {
          DEFAULT: 'rgb(var(--muted) / <alpha-value>)',
          foreground: 'rgb(var(--muted-foreground) / <alpha-value>)',
        },
      },
      boxShadow: {
        xs: 'var(--shadow-xs)',
        sm: 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow-md)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        xl: 'var(--shadow-xl)',
        '2xl': 'var(--shadow-2xl)',
        inner: 'var(--shadow-inner)',
        primary: 'var(--shadow-primary)',
        success: 'var(--shadow-success)',
        error: 'var(--shadow-error)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        DEFAULT: 'var(--radius-base)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
        full: 'var(--radius-full)',
      },
      transitionDuration: {
        fast: '150ms',
        DEFAULT: '200ms',
        slow: '300ms',
        slower: '500ms',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## Day 3-4: Upgrade Core Components

### Step 3: Enhanced Button Component

Create `frontend/src/components/ui/Button2.tsx` (we'll migrate later):

```typescript
'use client';

import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { forwardRef, ReactNode, ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  loadingText?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 shadow-sm',
  secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 focus-visible:ring-neutral-500',
  outline: 'border-2 border-neutral-300 bg-transparent hover:bg-neutral-50 focus-visible:ring-primary-500',
  ghost: 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900',
  destructive: 'bg-error-600 text-white hover:bg-error-700 focus-visible:ring-error-500 shadow-sm',
  success: 'bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500 shadow-sm',
  link: 'text-primary-600 underline-offset-4 hover:underline',
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
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium',
          'transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          variants[variant],
          sizes[size],
          fullWidth && 'w-full',
          className
        )}
        whileHover={!isDisabled ? { scale: 1.02 } : undefined}
        whileTap={!isDisabled ? { scale: 0.98 } : undefined}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {!loading && icon && iconPosition === 'left' && icon}
        {loading && loadingText ? loadingText : children}
        {!loading && icon && iconPosition === 'right' && icon}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
```

### Step 4: Enhanced Card Component

Create `frontend/src/components/ui/Card2.tsx`:

```typescript
'use client';

import { motion } from 'framer-motion';
import { ReactNode, forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  elevation?: 0 | 1 | 2 | 3 | 4 | 5;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  interactive?: boolean;
  gradient?: boolean;
}

const elevations = {
  0: '',
  1: 'shadow-sm',
  2: 'shadow-md',
  3: 'shadow-lg',
  4: 'shadow-xl',
  5: 'shadow-2xl',
};

const paddings = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
  xl: 'p-10',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      elevation = 1,
      padding = 'md',
      hover = false,
      interactive = false,
      gradient = false,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          'bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700',
          'transition-all duration-200',
          elevations[elevation],
          paddings[padding],
          hover && 'hover:shadow-lg hover:-translate-y-0.5',
          interactive && 'cursor-pointer',
          gradient && 'relative overflow-hidden',
          className
        )}
        whileHover={hover ? { y: -2 } : undefined}
        {...props}
      >
        {gradient && (
          <div className="absolute inset-0 bg-gradient-to-br from-primary-50 to-transparent opacity-50 pointer-events-none" />
        )}
        <div className="relative">{children}</div>
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('mb-4 space-y-1.5', className)}>{children}</div>
);

export const CardTitle = ({ children, className }: { children: ReactNode; className?: string }) => (
  <h3 className={cn('text-xl font-semibold text-neutral-900 dark:text-neutral-100', className)}>
    {children}
  </h3>
);

export const CardDescription = ({ children, className }: { children: ReactNode; className?: string }) => (
  <p className={cn('text-sm text-neutral-600 dark:text-neutral-400', className)}>{children}</p>
);

export const CardContent = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('space-y-4', className)}>{children}</div>
);

export const CardFooter = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('mt-6 flex items-center justify-between', className)}>{children}</div>
);

export default Card;
```

---

## Day 5: Install New Dependencies

```bash
cd frontend

# Data tables
npm install @tanstack/react-table

# Command palette
npm install cmdk

# Form management (if not already installed)
npm install react-hook-form @hookform/resolvers

# Additional utilities
npm install @formkit/auto-animate
```

---

## Testing Your Changes

1. **Start the dev server**:
```bash
npm run dev
```

2. **Create a test page** (`frontend/src/app/design-system/page.tsx`):
```tsx
import Button from '@/components/ui/Button2';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card2';

export default function DesignSystemTest() {
  return (
    <div className="p-8 space-y-8">
      <h1 className="text-4xl font-bold">Design System Test</h1>
      
      {/* Test Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Buttons</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="success">Success</Button>
            <Button loading>Loading</Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card elevation={1} hover>
          <CardHeader>
            <CardTitle>Card 1</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Elevation 1 with hover effect</p>
          </CardContent>
        </Card>
        <Card elevation={2} gradient>
          <CardHeader>
            <CardTitle>Card 2</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Elevation 2 with gradient</p>
          </CardContent>
        </Card>
        <Card elevation={3} interactive>
          <CardHeader>
            <CardTitle>Card 3</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Elevation 3 and interactive</p>
          </CardContent>
        </Card>
      </div>

      {/* Test Colors */}
      <Card>
        <CardHeader>
          <CardTitle>Color Palette</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            <div className="space-y-2">
              <div className="h-12 bg-primary-500 rounded"></div>
              <p className="text-xs">Primary</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-success-500 rounded"></div>
              <p className="text-xs">Success</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-warning-500 rounded"></div>
              <p className="text-xs">Warning</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-error-500 rounded"></div>
              <p className="text-xs">Error</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-neutral-500 rounded"></div>
              <p className="text-xs">Neutral</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

3. **Visit**: `http://localhost:3000/design-system`

---

## Next Steps

After completing Week 1:
1. ✅ Migrate existing components to use new design tokens
2. ✅ Replace all `bg-gray-*` with `bg-neutral-*`
3. ✅ Replace all `text-gray-*` with `text-neutral-*`
4. ✅ Add loading skeletons to all data-fetching components
5. ✅ Begin implementing command palette

---

## Troubleshooting

### Colors not working?
- Check that `globals.css` is imported in `layout.tsx`
- Verify Tailwind content paths in `tailwind.config.ts`
- Clear `.next` cache and restart dev server

### TypeScript errors?
- Run `npm run type-check` to see all errors
- Update `@types/node` and `@types/react` if needed

### Build errors?
- Run `npm run build` to test production build
- Check for unused imports
- Verify all components are exported correctly

---

**Status**: Ready to implement  
**Estimated Time**: 5 days
**Next**: Begin Day 1 tasks
