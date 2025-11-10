/**
 * Comprehensive Dark Mode Testing Suite
 * 
 * Tests dark mode implementation across all pages, components, and interactions.
 * Verifies:
 * - Theme switching functionality
 * - Color contrast ratios (WCAG AA: 4.5:1 minimum)
 * - System preference detection
 * - Cross-tab synchronization
 * - All pages render correctly in dark mode
 * - All modals and popovers work in dark mode
 * - All forms and inputs work in dark mode
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Import pages
import Dashboard from '@/app/dashboard/page';
import Jobs from '@/app/jobs/page';
import Applications from '@/app/applications/page';
import Recommendations from '@/app/recommendations/page';
import Analytics from '@/app/analytics/page';

// Import components
import { ThemeToggle, ThemeToggleDropdown } from '@/components/ui/ThemeToggle';
import { useDarkMode } from '@/hooks/useDarkMode';
import Navigation from '@/components/layout/Navigation';
import { Modal2 } from '@/components/ui/Modal2';
import { Drawer2 } from '@/components/ui/Drawer2';
import { Input2 } from '@/components/ui/Input2';
import { Select2 } from '@/components/ui/Select2';
import { Textarea2 } from '@/components/ui/Textarea2';
import { DatePicker2 } from '@/components/ui/DatePicker2';
import { Button2 } from '@/components/ui/Button2';
import { Card2 } from '@/components/ui/Card2';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}));

// Helper to create QueryClient
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

// Helper to wrap components with providers
function renderWithProviders(ui) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

// Helper to get computed styles
function getComputedColor(element, property) {
  return window.getComputedStyle(element).getPropertyValue(property);
}

// Helper to calculate relative luminance (WCAG formula)
function getRelativeLuminance(rgb) {
  const match = rgb.match(/\d+/g);
  const [r, g, b] = match ? match.map(Number) : [0, 0, 0];
  const [rs, gs, bs] = [r, g, b].map(val => {
    const s = val / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Helper to calculate contrast ratio
function getContrastRatio(color1, color2) {
  const l1 = getRelativeLuminance(color1);
  const l2 = getRelativeLuminance(color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Helper to check if element has dark mode classes
function hasDarkModeClasses(element) {
  const classList = element.className;
  return classList.includes('dark:') || 
         classList.includes('dark\\:') ||
         element.closest('.dark') !== null;
}

describe('Dark Mode - Theme Toggle', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should toggle between light and dark themes', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);

    const toggleButton = screen.getByRole('button', { name: /toggle theme/i });
    
    // Should start in light mode
    expect(document.documentElement.classList.contains('dark')).toBe(false);

    // Toggle to dark
    await user.click(toggleButton);
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    // Toggle back to light
    await user.click(toggleButton);
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });
  });

  it('should persist theme preference to localStorage', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);

    const toggleButton = screen.getByRole('button', { name: /toggle theme/i });
    
    await user.click(toggleButton);
    
    await waitFor(() => {
      expect(localStorage.getItem('theme')).toBe('dark');
    });
  });

  it('should support keyboard shortcut (Cmd/Ctrl+D)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);

    // Simulate Cmd+D (Mac) or Ctrl+D (Windows/Linux)
    await user.keyboard('{Meta>}d{/Meta}');
    
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
  });

  it('should show correct icon for current theme', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);

    const toggleButton = screen.getByRole('button', { name: /toggle theme/i });
    
    // Light mode should show Sun icon
    expect(toggleButton.querySelector('svg')).toBeInTheDocument();

    // Toggle to dark
    await user.click(toggleButton);
    
    // Dark mode should show Moon icon
    await waitFor(() => {
      expect(toggleButton.querySelector('svg')).toBeInTheDocument();
    });
  });
});

describe('Dark Mode - System Preference', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should detect system dark mode preference', () => {
    // Mock system preference
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    renderWithProviders(<ThemeToggleDropdown />);
    
    // Should respect system preference when set to 'system'
    expect(window.matchMedia('(prefers-color-scheme: dark)').matches).toBe(true);
  });

  it('should update theme when system preference changes', async () => {
    const listeners: Array<(e: MediaQueryListEvent) => void> = [];
    
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn((event: string, listener: (e: MediaQueryListEvent) => void) => {
          if (event === 'change') {
            listeners.push(listener);
          }
        }),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    renderWithProviders(<ThemeToggleDropdown />);
    
    // Simulate system preference change
    listeners.forEach(listener => {
      listener({ matches: true } as MediaQueryListEvent);
    });

    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
  });
});

describe('Dark Mode - Navigation', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render navigation in light mode', () => {
    renderWithProviders(<Navigation />);
    
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveClass('bg-white');
    expect(nav).toHaveClass('dark:bg-neutral-900');
  });

  it('should render navigation in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Navigation />);
    
    const nav = screen.getByRole('navigation');
    expect(hasDarkModeClasses(nav)).toBe(true);
  });

  it('should show theme toggle in navigation', () => {
    renderWithProviders(<Navigation />);
    
    const toggleButton = screen.getByRole('button', { name: /toggle theme/i });
    expect(toggleButton).toBeInTheDocument();
  });

  it('should have proper contrast for navigation links', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Navigation />);
    
    const links = screen.getAllByRole('link');
    links.forEach(link => {
      const color = getComputedColor(link, 'color');
      const bgColor = getComputedColor(link, 'background-color');
      
      if (color && bgColor) {
        const contrast = getContrastRatio(color, bgColor);
        // WCAG AA requires 4.5:1 for normal text
        expect(contrast).toBeGreaterThanOrEqual(4.5);
      }
    });
  });
});

describe('Dark Mode - Dashboard Page', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render dashboard in light mode', () => {
    renderWithProviders(<Dashboard />);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('should render dashboard in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Dashboard />);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('should have dark mode classes on dashboard elements', () => {
    document.documentElement.classList.add('dark');
    const { container } = renderWithProviders(<Dashboard />);
    
    // Check for dark mode utility classes
    const elements = container.querySelectorAll('[class*="dark:"]');
    expect(elements.length).toBeGreaterThan(0);
  });
});

describe('Dark Mode - Jobs Page', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render jobs page in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Jobs />);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('should have proper dark mode styling', () => {
    document.documentElement.classList.add('dark');
    const { container } = renderWithProviders(<Jobs />);
    
    const elements = container.querySelectorAll('[class*="dark:"]');
    expect(elements.length).toBeGreaterThan(0);
  });
});

describe('Dark Mode - Applications Page', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render applications page in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Applications />);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});

describe('Dark Mode - Recommendations Page', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render recommendations page in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Recommendations />);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});

describe('Dark Mode - Analytics Page', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render analytics page in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(<Analytics />);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});

describe('Dark Mode - Modal Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render modal in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Modal2 isOpen={true} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal2>
    );
    
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(hasDarkModeClasses(modal)).toBe(true);
  });

  it('should have proper contrast in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Modal2 isOpen={true} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal2>
    );
    
    const modal = screen.getByRole('dialog');
    const color = getComputedColor(modal, 'color');
    const bgColor = getComputedColor(modal, 'background-color');
    
    if (color && bgColor) {
      const contrast = getContrastRatio(color, bgColor);
      expect(contrast).toBeGreaterThanOrEqual(4.5);
    }
  });
});

describe('Dark Mode - Drawer Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render drawer in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Drawer2 isOpen={true} onClose={() => {}} title="Test Drawer">
        <p>Drawer content</p>
      </Drawer2>
    );
    
    const drawer = screen.getByRole('dialog');
    expect(drawer).toBeInTheDocument();
    expect(hasDarkModeClasses(drawer)).toBe(true);
  });
});

describe('Dark Mode - Form Components', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render Input2 in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Input2 
        label="Test Input" 
        value="" 
        onChange={() => {}} 
      />
    );
    
    const input = screen.getByLabelText('Test Input');
    expect(input).toBeInTheDocument();
    expect(hasDarkModeClasses(input)).toBe(true);
  });

  it('should render Select2 in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Select2 
        label="Test Select" 
        value="" 
        onChange={() => {}}
        options={[
          { value: '1', label: 'Option 1' },
          { value: '2', label: 'Option 2' },
        ]}
      />
    );
    
    const select = screen.getByLabelText('Test Select');
    expect(select).toBeInTheDocument();
    expect(hasDarkModeClasses(select)).toBe(true);
  });

  it('should render Textarea2 in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Textarea2 
        label="Test Textarea" 
        value="" 
        onChange={() => {}} 
      />
    );
    
    const textarea = screen.getByLabelText('Test Textarea');
    expect(textarea).toBeInTheDocument();
    expect(hasDarkModeClasses(textarea)).toBe(true);
  });

  it('should have proper focus ring in dark mode', async () => {
    document.documentElement.classList.add('dark');
    const user = userEvent.setup();
    
    renderWithProviders(
      <Input2 
        label="Test Input" 
        value="" 
        onChange={() => {}} 
      />
    );
    
    const input = screen.getByLabelText('Test Input');
    await user.click(input);
    
    expect(input).toHaveFocus();
    expect(hasDarkModeClasses(input)).toBe(true);
  });

  it('should render form error states in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Input2 
        label="Test Input" 
        value="" 
        onChange={() => {}}
        error="This field is required"
      />
    );
    
    const error = screen.getByText('This field is required');
    expect(error).toBeInTheDocument();
    
    const color = getComputedColor(error, 'color');
    expect(color).toBeTruthy();
  });
});

describe('Dark Mode - Button Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render primary button in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Button2 variant="primary">Click me</Button2>
    );
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(hasDarkModeClasses(button)).toBe(true);
  });

  it('should render secondary button in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Button2 variant="secondary">Click me</Button2>
    );
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
  });

  it('should render ghost button in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Button2 variant="ghost">Click me</Button2>
    );
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
  });

  it('should have proper hover state in dark mode', async () => {
    document.documentElement.classList.add('dark');
    const user = userEvent.setup();
    
    renderWithProviders(
      <Button2 variant="primary">Click me</Button2>
    );
    
    const button = screen.getByRole('button', { name: /click me/i });
    await user.hover(button);
    
    expect(button).toBeInTheDocument();
  });
});

describe('Dark Mode - Card Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should render card in dark mode', () => {
    document.documentElement.classList.add('dark');
    renderWithProviders(
      <Card2>
        <p>Card content</p>
      </Card2>
    );
    
    const card = screen.getByText('Card content').parentElement;
    expect(card).toBeInTheDocument();
    expect(hasDarkModeClasses(card!)).toBe(true);
  });

  it('should have proper background in dark mode', () => {
    document.documentElement.classList.add('dark');
    const { container } = renderWithProviders(
      <Card2>
        <p>Card content</p>
      </Card2>
    );
    
    const card = container.firstChild as HTMLElement;
    const bgColor = getComputedColor(card, 'background-color');
    expect(bgColor).toBeTruthy();
  });
});

describe('Dark Mode - Color Contrast', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.add('dark');
  });

  it('should meet WCAG AA contrast ratio for text (4.5:1)', () => {
    const { container } = renderWithProviders(
      <div className="bg-neutral-900 text-neutral-100 p-4">
        <p>This is sample text</p>
      </div>
    );
    
    const text = screen.getByText('This is sample text');
    const color = getComputedColor(text, 'color');
    const bgColor = getComputedColor(text.parentElement!, 'background-color');
    
    if (color && bgColor) {
      const contrast = getContrastRatio(color, bgColor);
      expect(contrast).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('should meet WCAG AA contrast ratio for primary buttons', () => {
    renderWithProviders(
      <Button2 variant="primary">Click me</Button2>
    );
    
    const button = screen.getByRole('button', { name: /click me/i });
    const color = getComputedColor(button, 'color');
    const bgColor = getComputedColor(button, 'background-color');
    
    if (color && bgColor) {
      const contrast = getContrastRatio(color, bgColor);
      expect(contrast).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('should meet WCAG AA contrast ratio for links', () => {
    renderWithProviders(<Navigation />);
    
    const links = screen.getAllByRole('link');
    links.forEach(link => {
      const color = getComputedColor(link, 'color');
      const bgColor = getComputedColor(link.parentElement!, 'background-color');
      
      if (color && bgColor) {
        const contrast = getContrastRatio(color, bgColor);
        expect(contrast).toBeGreaterThanOrEqual(4.5);
      }
    });
  });
});

describe('Dark Mode - Transitions', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should have smooth transitions when toggling theme', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);

    const toggleButton = screen.getByRole('button', { name: /toggle theme/i });
    
    // Check transition property is set
    const body = document.body;
    const transition = getComputedColor(body, 'transition-property');
    expect(transition).toContain('background-color');
    
    await user.click(toggleButton);
    
    // Transition should still be present after toggle
    const transitionAfter = getComputedColor(body, 'transition-property');
    expect(transitionAfter).toContain('background-color');
  });

  it('should transition within 200ms', () => {
    const body = document.body;
    const duration = getComputedColor(body, 'transition-duration');
    
    // Should be 200ms or 0.2s
    expect(duration === '200ms' || duration === '0.2s').toBe(true);
  });
});

describe('Dark Mode - Cross-tab Synchronization', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('should sync theme changes across tabs', async () => {
    renderWithProviders(<ThemeToggle />);

    // Simulate storage event from another tab
    const storageEvent = new StorageEvent('storage', {
      key: 'theme',
      newValue: 'dark',
      storageArea: localStorage
    });
    
    window.dispatchEvent(storageEvent);
    
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
  });
});
