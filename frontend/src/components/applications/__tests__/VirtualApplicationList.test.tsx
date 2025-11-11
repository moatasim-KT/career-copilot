/**
 * VirtualApplicationList Component Tests
 * 
 * Tests for the virtualized application list component including:
 * - Rendering with various data sizes
 * - Selection functionality
 * - Empty state handling
 * - Accessibility
 * - Performance with large datasets
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';

import { VirtualApplicationList, VirtualApplicationListGrid } from '../VirtualApplicationList';
import { Application } from '@/components/ui/ApplicationCard';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock @tanstack/react-virtual
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: vi.fn(() => ({
    getVirtualItems: () => [
      { index: 0, start: 0, size: 220, key: '0' },
      { index: 1, start: 244, size: 220, key: '1' },
      { index: 2, start: 488, size: 220, key: '2' },
    ],
    getTotalSize: () => 732,
  })),
}));

/**
 * Generate mock application data
 */
function generateMockApplication(id: number, overrides?: Partial<Application>): Application {
  return {
    id,
    user_id: 1,
    job_id: id * 10,
    status: 'applied',
    applied_date: new Date(Date.now() - id * 86400000).toISOString(),
    response_date: null,
    interview_date: null,
    offer_date: null,
    notes: `Notes for application ${id}`,
    interview_feedback: null,
    follow_up_date: null,
    created_at: new Date(Date.now() - id * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
    job_title: `Software Engineer ${id}`,
    company_name: `Company ${id}`,
    job_location: 'Remote',
    ...overrides,
  };
}

/**
 * Generate multiple mock applications
 */
function generateMockApplications(count: number): Application[] {
  return Array.from({ length: count }, (_, i) => generateMockApplication(i + 1));
}

describe('VirtualApplicationList', () => {
  const mockOnApplicationClick = vi.fn();
  const mockOnSelectApplication = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders empty state when no applications provided', () => {
      render(
        <VirtualApplicationList
          applications={[]}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      expect(screen.getByText(/No applications found/i)).toBeInTheDocument();
      expect(screen.getByText(/Applications you submit will appear here/i)).toBeInTheDocument();
    });

    it('renders custom empty message', () => {
      const customMessage = 'Custom empty state message';
      render(
        <VirtualApplicationList
          applications={[]}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
          emptyMessage={customMessage}
        />
      );

      expect(screen.getByText(customMessage)).toBeInTheDocument();
    });

    it('renders application cards for provided applications', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      applications.forEach((app) => {
        expect(screen.getByText(app.job_title!)).toBeInTheDocument();
        expect(screen.getByText(app.company_name!)).toBeInTheDocument();
      });
    });

    it('renders scroll indicator for large lists', () => {
      const applications = generateMockApplications(25);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      expect(screen.getByText(/Showing \d+ of 25 applications/)).toBeInTheDocument();
    });

    it('does not render scroll indicator for small lists', () => {
      const applications = generateMockApplications(10);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      expect(screen.queryByText(/Showing \d+ of \d+ applications/)).not.toBeInTheDocument();
    });
  });

  describe('Interaction', () => {
    it('calls onApplicationClick when application card is clicked', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const firstCard = screen.getByText(applications[0].job_title!).closest('[role="button"]');
      fireEvent.click(firstCard!);

      expect(mockOnApplicationClick).toHaveBeenCalledWith(applications[0].id);
    });

    it('calls onApplicationClick when Enter key is pressed', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const firstCard = screen.getByText(applications[0].job_title!).closest('[role="button"]');
      fireEvent.keyDown(firstCard!, { key: 'Enter' });

      expect(mockOnApplicationClick).toHaveBeenCalledWith(applications[0].id);
    });

    it('calls onApplicationClick when Space key is pressed', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const firstCard = screen.getByText(applications[0].job_title!).closest('[role="button"]');
      fireEvent.keyDown(firstCard!, { key: ' ' });

      expect(mockOnApplicationClick).toHaveBeenCalledWith(applications[0].id);
    });

    it('calls onSelectApplication when checkbox is clicked', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);

      expect(mockOnSelectApplication).toHaveBeenCalledWith(applications[0].id);
    });
  });

  describe('Selection State', () => {
    it('renders selected applications with visual indicator', () => {
      const applications = generateMockApplications(3);
      const selectedIds = [applications[0].id, applications[2].id];
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={selectedIds}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes[0]).toBeChecked();
      expect(checkboxes[1]).not.toBeChecked();
      expect(checkboxes[2]).toBeChecked();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for application cards', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      applications.forEach((app) => {
        const ariaLabel = `View application: ${app.job_title} - Status: ${app.status}`;
        expect(screen.getByLabelText(ariaLabel)).toBeInTheDocument();
      });
    });

    it('has proper role attributes', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('has proper tabIndex for keyboard navigation', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const firstCard = screen.getByText(applications[0].job_title!).closest('[role="button"]');
      expect(firstCard).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const applications = generateMockApplications(1000);
      
      const { container } = render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      // With virtualization, only visible items should be rendered
      // The mock returns 3 virtual items
      const renderedCards = container.querySelectorAll('[data-index]');
      expect(renderedCards.length).toBe(3);
    });

    it('uses correct estimated size', () => {
      const applications = generateMockApplications(10);
      const customSize = 300;
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
          estimatedSize={customSize}
        />
      );

      // Component should render without errors
      expect(screen.getByText(applications[0].job_title!)).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('renders with compact variant', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
          variant="compact"
        />
      );

      expect(screen.getByText(applications[0].job_title!)).toBeInTheDocument();
    });

    it('renders with detailed variant', () => {
      const applications = generateMockApplications(3);
      
      render(
        <VirtualApplicationList
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
          variant="detailed"
        />
      );

      expect(screen.getByText(applications[0].job_title!)).toBeInTheDocument();
    });
  });
});

describe('VirtualApplicationListGrid', () => {
  const mockOnApplicationClick = vi.fn();
  const mockOnSelectApplication = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Grid Rendering', () => {
    it('renders applications in grid layout', () => {
      const applications = generateMockApplications(6);
      
      render(
        <VirtualApplicationListGrid
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
          columns={{ sm: 1, md: 2, lg: 3 }}
        />
      );

      applications.forEach((app) => {
        expect(screen.getByText(app.job_title!)).toBeInTheDocument();
      });
    });

    it('renders empty state in grid variant', () => {
      render(
        <VirtualApplicationListGrid
          applications={[]}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      expect(screen.getByText(/No applications found/i)).toBeInTheDocument();
    });

    it('handles grid column configuration', () => {
      const applications = generateMockApplications(9);
      
      render(
        <VirtualApplicationListGrid
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
          columns={{ sm: 1, md: 2, lg: 3, xl: 4 }}
        />
      );

      expect(screen.getByText(applications[0].job_title!)).toBeInTheDocument();
    });
  });

  describe('Grid Interaction', () => {
    it('calls onApplicationClick in grid layout', () => {
      const applications = generateMockApplications(6);
      
      render(
        <VirtualApplicationListGrid
          applications={applications}
          onApplicationClick={mockOnApplicationClick}
          selectedApplicationIds={[]}
          onSelectApplication={mockOnSelectApplication}
        />
      );

      const firstCard = screen.getByText(applications[0].job_title!).closest('[role="button"]');
      fireEvent.click(firstCard!);

      expect(mockOnApplicationClick).toHaveBeenCalledWith(applications[0].id);
    });
  });
});
