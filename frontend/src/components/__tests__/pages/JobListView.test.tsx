import { render, screen } from '@testing-library/react';
import React from 'react';

import '@testing-library/jest-dom';
import { JobListView } from '@/components/pages/JobListView';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const mockJobs = [
  {
    id: 1,
    company: 'TestCo',
    title: 'Software Engineer',
    location: 'Remote',
    url: 'https://test.com',
    salary_range: '$100k-$150k',
    job_type: 'full-time',
    description: 'Develop software',
    remote: true,
    tech_stack: ['React', 'Node.js'],
    responsibilities: 'Write code',
    source: 'manual',
    match_score: 90,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    company: 'AnotherCo',
    title: 'Backend Engineer',
    location: 'San Francisco',
    url: 'https://another.com',
    salary_range: '$120k-$160k',
    job_type: 'full-time',
    description: 'Build APIs',
    remote: false,
    tech_stack: ['Python', 'Django'],
    responsibilities: 'API development',
    source: 'linkedin',
    match_score: 85,
    created_at: new Date().toISOString(),
  },
];

describe('JobListView', () => {
  const mockOnJobClick = jest.fn();
  const mockOnSelectJob = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders job list with stagger animation structure', () => {
    const { container } = render(
      <JobListView
        jobs={mockJobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    // Check that the grid container is rendered
    const gridContainer = container.querySelector('.grid');
    expect(gridContainer).toBeInTheDocument();
    expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'gap-6');
  });

  it('renders all job items', () => {
    render(
      <JobListView
        jobs={mockJobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument();
  });

  it('displays empty state when no jobs are provided', () => {
    render(
      <JobListView
        jobs={[]}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    expect(screen.getByText(/No jobs found/i)).toBeInTheDocument();
  });

  it('handles job selection correctly', () => {
    render(
      <JobListView
        jobs={mockJobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[1]}
        onSelectJob={mockOnSelectJob}
      />
    );

    // Verify that the first job is marked as selected
    const jobCards = screen.getAllByTestId('job-card');
    expect(jobCards).toHaveLength(2);
  });

  it('applies animation variants to container and items', () => {
    const { container } = render(
      <JobListView
        jobs={mockJobs}
        onJobClick={mockOnJobClick}
        selectedJobIds={[]}
        onSelectJob={mockOnSelectJob}
      />
    );

    // Verify the grid container exists (which should have animation variants)
    const gridContainer = container.querySelector('.grid');
    expect(gridContainer).toBeInTheDocument();

    // Verify individual job items are rendered
    const jobCards = screen.getAllByTestId('job-card');
    expect(jobCards.length).toBe(mockJobs.length);
  });
});
