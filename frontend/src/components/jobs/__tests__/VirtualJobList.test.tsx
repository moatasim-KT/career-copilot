/**
 * VirtualJobList Component Tests
 * 
 * Tests for the virtualized job list component including:
 * - Rendering with various job counts
 * - Virtual scrolling behavior
 * - Selection functionality
 * - Empty state handling
 * - Accessibility
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import { VirtualJobList, VirtualJobListGrid } from '../VirtualJobList';

// Mock framer-motion (including the `m` export) to avoid animation issues in tests
jest.mock('framer-motion', () => {
  const Mock: React.FC<React.PropsWithChildren<any>> = ({ children, ...props }) => (
    <div {...props}>{children}</div>
  );

  return {
    motion: {
      div: Mock,
    },
    m: {
      div: Mock,
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
  };
});

// Mock the JobCard component
jest.mock('@/components/ui/JobCard', () => ({
  __esModule: true,
  default: ({ job, isSelected, onSelect }: any) => (
    <div data-testid={`job-card-${job.id}`} className={isSelected ? 'selected' : ''}>
      <h3>{job.title}</h3>
      <p>{job.company}</p>
      <button onClick={onSelect} data-testid={`select-${job.id}`}>
        Select
      </button>
    </div>
  ),
}));

// Mock @tanstack/react-virtual to render all items in tests
jest.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({ count, estimateSize }: any) => {
    // In tests, render all items (no virtualization)
    const items = Array.from({ length: count }, (_, i) => ({
      index: i,
      key: i,
      start: i * estimateSize(),
      size: estimateSize(),
    }));

    return {
      getVirtualItems: () => items,
      getTotalSize: () => count * estimateSize(),
      scrollToIndex: jest.fn(),
      scrollToOffset: jest.fn(),
      measure: jest.fn(),
    };
  },
}));

// Helper function to generate mock jobs
const generateMockJobs = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `Software Engineer ${i + 1}`,
    company: `Company ${i + 1}`,
    location: `City ${i + 1}`,
    type: 'full-time',
    postedAt: '2 days ago',
  }));
};

describe('VirtualJobList', () => {
  const mockOnJobClick = jest.fn();
  const mockOnSelectJob = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render empty state when no jobs are provided', () => {
      render(
        <VirtualJobList
          jobs={[]}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      expect(screen.getByText(/No jobs found/i)).toBeInTheDocument();
      expect(screen.getByText(/Try adjusting your search or filter criteria/i)).toBeInTheDocument();
    });

    it('should render custom empty message', () => {
      const customMessage = 'Custom empty state message';
      render(
        <VirtualJobList
          jobs={[]}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
          emptyMessage={customMessage}
        />
      );

      expect(screen.getByText(customMessage)).toBeInTheDocument();
    });

    it('should render jobs when provided', () => {
      const jobs = generateMockJobs(5);
      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      // Check that at least some jobs are rendered (virtualization may not render all)
      expect(screen.getByText('Software Engineer 1')).toBeInTheDocument();
      expect(screen.getByText('Company 1')).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      const jobs = generateMockJobs(3);
      const { container } = render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
          className="custom-class"
        />
      );

      const scrollContainer = container.querySelector('.custom-class');
      expect(scrollContainer).toBeInTheDocument();
    });

    it('should show scroll indicator for large lists', () => {
      const jobs = generateMockJobs(25);
      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      expect(screen.getByText(/Showing \d+ of 25 jobs/)).toBeInTheDocument();
    });

    it('should not show scroll indicator for small lists', () => {
      const jobs = generateMockJobs(10);
      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      expect(screen.queryByText(/Showing \d+ of \d+ jobs/)).not.toBeInTheDocument();
    });
  });

  describe('Virtualization', () => {
    it('should use custom estimatedSize', () => {
      const jobs = generateMockJobs(10);
      const customSize = 300;

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
          estimatedSize={customSize}
        />
      );

      // Component should render successfully with custom size
      const renderedJobs = screen.queryAllByTestId(/job-card-/);
      expect(renderedJobs.length).toBeGreaterThan(0);
    });

    it('should handle large datasets', () => {
      const jobs = generateMockJobs(100);

      const { container } = render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      // Component should render successfully with large dataset
      const renderedJobs = screen.queryAllByTestId(/job-card-/);
      expect(renderedJobs.length).toBeGreaterThan(0);
      // In real usage, virtualization would limit rendered items
      // but in tests we mock it to render all for easier testing
    });
  });

  describe('Interactions', () => {
    it('should call onJobClick when a job is clicked', async () => {
      const jobs = generateMockJobs(5);
      const user = userEvent.setup();

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      const jobCard = screen.getByTestId('job-card-1').parentElement;
      if (jobCard) {
        await user.click(jobCard);
        expect(mockOnJobClick).toHaveBeenCalledWith(1);
      }
    });

    it('should call onSelectJob when select button is clicked', async () => {
      const jobs = generateMockJobs(5);
      const user = userEvent.setup();

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      const selectButton = screen.getByTestId('select-1');
      await user.click(selectButton);
      expect(mockOnSelectJob).toHaveBeenCalledWith(1);
    });

    it('should handle keyboard navigation', async () => {
      const jobs = generateMockJobs(5);

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      const jobCard = screen.getByTestId('job-card-1').parentElement;
      if (jobCard) {
        fireEvent.keyDown(jobCard, { key: 'Enter' });
        expect(mockOnJobClick).toHaveBeenCalledWith(1);

        mockOnJobClick.mockClear();
        fireEvent.keyDown(jobCard, { key: ' ' });
        expect(mockOnJobClick).toHaveBeenCalledWith(1);
      }
    });

    it('should show selected state for selected jobs', () => {
      const jobs = generateMockJobs(5);
      const selectedIds = [1, 3];

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={selectedIds}
          onSelectJob={mockOnSelectJob}
        />
      );

      const job1 = screen.getByTestId('job-card-1');
      const job2 = screen.getByTestId('job-card-2');
      const job3 = screen.getByTestId('job-card-3');

      expect(job1).toHaveClass('selected');
      expect(job2).not.toHaveClass('selected');
      expect(job3).toHaveClass('selected');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      const jobs = generateMockJobs(3);

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      const jobCard = screen.getByTestId('job-card-1').parentElement;
      expect(jobCard).toHaveAttribute('role', 'button');
      expect(jobCard).toHaveAttribute('aria-label', 'View job: Software Engineer 1 at Company 1');
    });

    it('should be keyboard accessible', () => {
      const jobs = generateMockJobs(3);

      render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      const jobCard = screen.getByTestId('job-card-1').parentElement;
      expect(jobCard).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Performance', () => {
    it('should handle rapid updates efficiently', async () => {
      const jobs = generateMockJobs(100);
      const { rerender } = render(
        <VirtualJobList
          jobs={jobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      // Rapidly update selected jobs
      for (let i = 0; i < 10; i++) {
        rerender(
          <VirtualJobList
            jobs={jobs}
            onJobClick={mockOnJobClick}
            selectedJobIds={[i]}
            onSelectJob={mockOnSelectJob}
          />
        );
      }

      // Component should still be functional
      expect(screen.getByText('Software Engineer 1')).toBeInTheDocument();
    });

    it('should handle job list updates', () => {
      const initialJobs = generateMockJobs(50);
      const { rerender } = render(
        <VirtualJobList
          jobs={initialJobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      // Update with more jobs
      const updatedJobs = generateMockJobs(100);
      rerender(
        <VirtualJobList
          jobs={updatedJobs}
          onJobClick={mockOnJobClick}
          selectedJobIds={[]}
          onSelectJob={mockOnSelectJob}
        />
      );

      expect(screen.getByText(/Showing \d+ of 100 jobs/)).toBeInTheDocument();
    });
  });
});

describe('VirtualJobListGrid', () => {
  const mockOnJobClick = jest.fn();
  const mockOnSelectJob = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render in grid layout', () => {
    const jobs = generateMockJobs(9);

    render(
      <VirtualJobListGrid
        jobs={jobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
        columns={{ sm: 1, md: 2, lg: 3 }}
      />
    );

    expect(screen.getByText('Software Engineer 1')).toBeInTheDocument();
  });

  it('should render empty state', () => {
    render(
      <VirtualJobListGrid
        jobs={[]}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    expect(screen.getByText(/No jobs found/i)).toBeInTheDocument();
  });

  it('should handle job clicks in grid layout', async () => {
    const jobs = generateMockJobs(6);
    const user = userEvent.setup();

    render(
      <VirtualJobListGrid
        jobs={jobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    const jobCard = screen.getByTestId('job-card-1');
    await user.click(jobCard);
    expect(mockOnJobClick).toHaveBeenCalledWith(1);
  });

  it('should show scroll indicator for large grids', () => {
    const jobs = generateMockJobs(30);

    render(
      <VirtualJobListGrid
        jobs={jobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    expect(screen.getByText(/Showing \d+ of 30 jobs/)).toBeInTheDocument();
  });
});
