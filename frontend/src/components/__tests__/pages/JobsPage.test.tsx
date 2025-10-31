import { render, screen, waitFor, fireEvent, act, within } from '@testing-library/react';
import React from 'react';

import '@testing-library/jest-dom';
import JobsPage from '@/components/pages/JobsPage';
import { apiClient } from '@/lib/api';

// Mock the apiClient module
jest.mock('@/lib/api', () => ({
  apiClient: {
    getJobs: jest.fn(),
    createJob: jest.fn(),
    updateJob: jest.fn(),
    deleteJob: jest.fn(),
    createApplication: jest.fn(),
  },
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
];

describe('JobsPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    // Default mock for getJobs
    (apiClient.getJobs as jest.Mock).mockResolvedValue({ data: mockJobs });
    (apiClient.createJob as jest.Mock).mockResolvedValue({ data: { ...mockJobs[0], id: 2 } });
    (apiClient.updateJob as jest.Mock).mockResolvedValue({ data: mockJobs[0] });
    (apiClient.deleteJob as jest.Mock).mockResolvedValue({ data: undefined });
    (apiClient.createApplication as jest.Mock).mockResolvedValue({ data: undefined });
  });

  it('renders the JobsPage component and displays job management heading', async () => {
    await act(async () => {
      render(<JobsPage />);
    });
    expect(screen.getByText('Job Management')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Add Job/i })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());
  });

  it('displays jobs loaded from the API', async () => {
    await act(async () => {
      render(<JobsPage />);
    });
    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('TestCo')).toBeInTheDocument();
    });
  });

  it('opens and closes the add job modal', async () => {
    await act(async () => {
      render(<JobsPage />);
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Add Job/i }));
    });
    expect(screen.getByText('Add New Job')).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
    });
    await waitFor(() => expect(screen.queryByText('Add New Job')).not.toBeInTheDocument());
  });

  it('submits a new job successfully', async () => {
    await act(async () => {
      render(<JobsPage />);
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Add Job/i }));
    });

    const modal = screen.getByRole('dialog', { name: /Add New Job/i });

    await act(async () => {
      fireEvent.change(within(modal).getByPlaceholderText('Enter company name'), { target: { value: 'NewCo' } });
      fireEvent.change(within(modal).getByPlaceholderText('Enter job title'), { target: { value: 'Frontend Dev' } });
    });
    
    (apiClient.getJobs as jest.Mock).mockResolvedValueOnce({ data: [...mockJobs, { ...mockJobs[0], id: 2, company: 'NewCo', title: 'Frontend Dev' }] });

    await act(async () => {
      fireEvent.click(within(modal).getByRole('button', { name: 'Add Job' })); // Submit button in modal
    });

    await waitFor(() => {
      expect(apiClient.createJob).toHaveBeenCalledWith(expect.objectContaining({ company: 'NewCo', title: 'Frontend Dev' }));
      expect(screen.queryByText('Add New Job')).not.toBeInTheDocument(); // Modal closes
    });
  });

  it('edits an existing job successfully', async () => {
    await act(async () => {
      render(<JobsPage />);
    });
    await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());



    // Find the job card and click its edit button
    const jobCard = screen.getByTestId('job-card');
    await act(async () => {
      fireEvent.click(within(jobCard).getByTitle('Edit Job'));
    });
    expect(screen.getByText('Edit Job')).toBeInTheDocument();

    const modal = screen.getByRole('dialog', { name: /Edit Job/i });

    await act(async () => {
      fireEvent.change(within(modal).getByPlaceholderText('Enter job title'), { target: { value: 'Updated Software Engineer' } });
    });

    (apiClient.getJobs as jest.Mock).mockResolvedValueOnce({ data: [{ ...mockJobs[0], title: 'Updated Software Engineer' }] });

    await act(async () => {
      fireEvent.click(within(modal).getByRole('button', { name: /Update Job/i }));
    });

    await waitFor(() => {
      expect(apiClient.updateJob).toHaveBeenCalledWith(mockJobs[0].id, expect.objectContaining({ title: 'Updated Software Engineer' }));
      expect(screen.queryByText('Edit Job')).not.toBeInTheDocument();
    });
  });

  it('deletes a job successfully', async () => {
    await act(async () => {
      render(<JobsPage />);
    });
    await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());

    window.confirm = jest.fn(() => true); // Mock confirm dialog
    
    (apiClient.getJobs as jest.Mock).mockResolvedValueOnce({ data: [] }); // Mock empty jobs after delete

    // Find the job card and click its delete button
    const jobCard = screen.getByTestId('job-card');
    await act(async () => {
      fireEvent.click(within(jobCard).getByTitle('Delete Job'));
    });

    await waitFor(() => {
      expect(apiClient.deleteJob).toHaveBeenCalledWith(mockJobs[0].id);
      expect(screen.queryByText('Software Engineer')).not.toBeInTheDocument();
    });
  });
});
