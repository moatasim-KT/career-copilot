import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import '@testing-library/jest-dom';
import ApplicationsPage from '@/components/pages/ApplicationsPage';
import * as api from '@/lib/api';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => {
  const Mock = ({ children, ...props }: any) => <div {...props}>{children}</div>;
  return {
    motion: {
      div: Mock,
      h1: ({ children, ...props }: any) => <h1 {...props}>{children}</h1>,
      p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
      span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
    },
    m: {
      div: Mock,
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
  };
});

// Mock the WebSocket hook
jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(() => ({})),
}));

// Mock the logger
jest.mock('@/lib/logger', () => ({
  logger: {
    log: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock the websocket handlers
jest.mock('@/lib/websocket/applications', () => ({
  handleApplicationStatusUpdate: jest.fn(),
}));

// Mock the API module
jest.mock('@/lib/api', () => ({
  apiClient: {
    getApplications: jest.fn(),
    createApplication: jest.fn(),
    updateApplication: jest.fn(),
    deleteApplication: jest.fn(),
  },
}));

const mockApplications = [
  {
    id: 1,
    job_id: 1,
    status: 'applied',
    notes: 'Great opportunity',
    applied_date: '2024-01-15T00:00:00Z',
    interview_date: null,
    response_date: null,
    job: {
      id: 1,
      title: 'Software Engineer',
      company: 'TechCorp',
      location: 'Remote',
      tech_stack: ['React', 'TypeScript', 'Node.js'],
    },
  },
  {
    id: 2,
    job_id: 2,
    status: 'interview',
    notes: 'Interview scheduled',
    applied_date: '2024-01-10T00:00:00Z',
    interview_date: '2024-01-20T00:00:00Z',
    response_date: null,
    job: {
      id: 2,
      title: 'Frontend Developer',
      company: 'StartupXYZ',
      location: 'San Francisco',
      tech_stack: ['Vue.js', 'JavaScript'],
    },
    interview_feedback: {
      questions: ['Tell me about yourself', 'What are your strengths?'],
      skill_areas: ['JavaScript', 'Problem Solving'],
      notes: 'Good interview',
    },
  },
];

describe.skip('ApplicationsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    const { apiClient } = require('@/lib/api');
    // Mock the API client methods
    apiClient.getApplications.mockResolvedValue({
      data: mockApplications as any,
      error: undefined,
    });
  });

  it('renders applications page with animations', async () => {
    render(<ApplicationsPage />);

    // Check for page title
    expect(screen.getByText('Applications')).toBeInTheDocument();
    expect(screen.getByText(/Track your job applications/i)).toBeInTheDocument();

    // Wait for applications to load
    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });
  });

  it('displays application cards with stagger animation structure', async () => {
    const { container } = render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Check that the container with space-y-4 class exists (animation container)
    const animationContainer = container.querySelector('.space-y-4');
    expect(animationContainer).toBeInTheDocument();
  });

  it('renders status badges with animations', async () => {
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Applied')).toBeInTheDocument();
      expect(screen.getByText('Interview')).toBeInTheDocument();
    });

    // Verify status badges are rendered
    const appliedBadge = screen.getByText('Applied');
    expect(appliedBadge).toHaveClass('rounded-full');
  });

  it('displays interview feedback section with animations', async () => {
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Interview Feedback')).toBeInTheDocument();
    });

    // Check for interview questions
    expect(screen.getByText('Tell me about yourself')).toBeInTheDocument();
    expect(screen.getByText('What are your strengths?')).toBeInTheDocument();

    // Check for skill areas
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    expect(screen.getByText('Problem Solving')).toBeInTheDocument();
  });

  it('displays tech stack with animations', async () => {
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument();
    });

    // Check for tech stack items
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
    expect(screen.getByText('Node.js')).toBeInTheDocument();
  });

  it('filters applications by status', async () => {
    const user = userEvent.setup();
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Find and click the status filter
    const statusFilter = screen.getByDisplayValue('all');
    await user.selectOptions(statusFilter, 'applied');

    // Verify filtering works
    await waitFor(() => {
      expect(screen.getByText(/Showing 1 of 2 applications/i)).toBeInTheDocument();
    });
  });

  it('searches applications', async () => {
    const user = userEvent.setup();
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Find and type in search input
    const searchInput = screen.getByPlaceholderText(/Search applications/i);
    await user.type(searchInput, 'TechCorp');

    // Verify search works
    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.queryByText('Frontend Developer')).not.toBeInTheDocument();
    });
  });

  it('displays empty state with animations when no applications', async () => {
    jest.spyOn(api.apiClient, 'getApplications').mockResolvedValue({
      data: [],
      error: undefined,
    });

    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('No applications yet')).toBeInTheDocument();
    });

    expect(screen.getByText(/Start by adding jobs/i)).toBeInTheDocument();
  });

  it('displays error message with animation', async () => {
    jest.spyOn(api.apiClient, 'getApplications').mockResolvedValue({
      data: undefined,
      error: 'Failed to load applications',
    });

    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load applications')).toBeInTheDocument();
    });
  });

  it('opens add application modal', async () => {
    const user = userEvent.setup();
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Click add application button
    const addButton = screen.getByText('Add Application');
    await user.click(addButton);

    // Verify modal opens
    await waitFor(() => {
      expect(screen.getByText('Add New Application')).toBeInTheDocument();
    });
  });

  it('animates status changes', async () => {
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Verify status badge is rendered with animation classes
    const statusBadge = screen.getByText('Applied');
    expect(statusBadge).toHaveClass('rounded-full');
    expect(statusBadge.parentElement).toBeTruthy();
  });
});
