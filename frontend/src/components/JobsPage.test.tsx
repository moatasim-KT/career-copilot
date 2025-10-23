import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import JobsPage from './JobsPage';
import { apiClient } from '@/lib/api';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Mock the API client to control responses
const handlers = [
  http.get('http://localhost:8002/api/v1/jobs', () => {
    return HttpResponse.json([
      {
        id: 1,
        company: 'TestCo',
        title: 'Software Engineer',
        location: 'Remote',
        job_type: 'full-time',
        remote: true,
        tech_stack: ['React', 'Node.js'],
        source: 'manual',
        created_at: new Date().toISOString(),
      },
    ]);
  }),
  http.post('http://localhost:8002/api/v1/jobs', async ({ request }) => {
    const newJob = await request.json();
    return HttpResponse.json({ ...newJob, id: 2, created_at: new Date().toISOString() }, { status: 200 });
  }),
  http.put('http://localhost:8002/api/v1/jobs/1', async ({ request }) => {
    const updatedJob = await request.json();
    return HttpResponse.json({ ...updatedJob, id: 1 }, { status: 200 });
  }),
  http.delete('http://localhost:8002/api/v1/jobs/1', () => {
    return HttpResponse.json({ message: 'Job deleted successfully' }, { status: 200 });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('JobsPage', () => {
  it('renders the JobsPage component and displays job management heading', async () => {
    render(<JobsPage />);
    expect(screen.getByText('Job Management')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Add Job/i })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());
  });

  it('displays jobs loaded from the API', async () => {
    render(<JobsPage />);
    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('TestCo')).toBeInTheDocument();
      expect(screen.getByText('Remote')).toBeInTheDocument();
    });
  });

  it('opens and closes the add job modal', async () => {
    render(<JobsPage />);
    fireEvent.click(screen.getByRole('button', { name: /Add Job/i }));
    expect(screen.getByText('Add New Job')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
    await waitFor(() => expect(screen.queryByText('Add New Job')).not.toBeInTheDocument());
  });

  it('submits a new job successfully', async () => {
    render(<JobsPage />);
    fireEvent.click(screen.getByRole('button', { name: /Add Job/i }));

    fireEvent.change(screen.getByLabelText(/Company \*/i), { target: { value: 'NewCo' } });
    fireEvent.change(screen.getByLabelText(/Job Title \*/i), { target: { value: 'Frontend Dev' } });
    fireEvent.click(screen.getByRole('button', { name: /Add Job/i })); // Submit button

    await waitFor(() => {
      expect(screen.queryByText('Add New Job')).not.toBeInTheDocument(); // Modal closes
    });
    // Optionally, re-fetch jobs to see the new one, or check for a success message
  });

  it('edits an existing job successfully', async () => {
    render(<JobsPage />);
    await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /Edit Job/i }));
    expect(screen.getByText('Edit Job')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Job Title \*/i), { target: { value: 'Updated Software Engineer' } });
    fireEvent.click(screen.getByRole('button', { name: /Update Job/i }));

    await waitFor(() => {
      expect(screen.queryByText('Edit Job')).not.toBeInTheDocument();
    });
    // Optionally, re-fetch jobs to see the updated one
  });

  it('deletes a job successfully', async () => {
    render(<JobsPage />);
    await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());

    window.confirm = jest.fn(() => true); // Mock confirm dialog
    fireEvent.click(screen.getByRole('button', { name: /Delete Job/i }));

    await waitFor(() => {
      expect(screen.queryByText('Software Engineer')).not.toBeInTheDocument();
    });
  });
});
