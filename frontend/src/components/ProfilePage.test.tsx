import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProfilePage from './ProfilePage';
import { apiClient } from '@/lib/api';

// Mock the apiClient module
jest.mock('@/lib/api', () => ({
  apiClient: {
    getUserProfile: jest.fn(),
    updateUserProfile: jest.fn(),
  },
}));

// Mock the FileUpload component
jest.mock('./ui/FileUpload', () => {
  return function MockFileUpload({ onUploadSuccess }: { onUploadSuccess: (data: any) => void }) {
    return (
      <div>
        <input type="file" data-testid="file-upload-input" />
        <button onClick={() => onUploadSuccess({ message: 'Upload successful' })}>Upload</button>
      </div>
    );
  };
});

const mockUserProfile = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  experience_level: 'Mid-level',
  location: 'New York, NY',
  skills: ['React', 'Node.js', 'Python'],
};

describe('ProfilePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (apiClient.getUserProfile as jest.Mock).mockResolvedValue({ data: mockUserProfile });
    (apiClient.updateUserProfile as jest.Mock).mockResolvedValue({ data: mockUserProfile });
  });

  it('renders loading state initially', () => {
    (apiClient.getUserProfile as jest.Mock).mockReturnValueOnce(new Promise(() => {})); // Pending promise
    render(<ProfilePage />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders profile data after loading', async () => {
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument();
      expect(screen.getByLabelText(/Full Name/i)).toHaveValue('Test User');
      expect(screen.getByLabelText(/Email/i)).toHaveValue('test@example.com');
      expect(screen.getByLabelText(/Skills \(comma-separated\)/i)).toHaveValue('React, Node.js, Python');
    });
  });

  it('handles profile update successfully', async () => {
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText('Profile')).toBeInTheDocument());

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/Full Name/i), { target: { value: 'Updated Name' } });
      fireEvent.click(screen.getByRole('button', { name: /Save Profile/i }));
    });

    await waitFor(() => {
      expect(apiClient.updateUserProfile).toHaveBeenCalledWith(expect.objectContaining({
        full_name: 'Updated Name',
      }));
      expect(screen.getByText('Profile updated successfully!')).toBeInTheDocument();
    });
  });

  it('displays an error message on profile update failure', async () => {
    (apiClient.updateUserProfile as jest.Mock).mockResolvedValue({ error: 'Failed to update' });
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText('Profile')).toBeInTheDocument());

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Save Profile/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to update/i)).toBeInTheDocument();
    });
  });

  it('handles skill input correctly', async () => {
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText('Profile')).toBeInTheDocument());

    const skillsInput = screen.getByLabelText(/Skills \(comma-separated\)/i);
    await act(async () => {
      fireEvent.change(skillsInput, { target: { value: 'Java, Spring, Microservices' } });
    });

    expect(skillsInput).toHaveValue('Java, Spring, Microservices');
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Save Profile/i }));
    });

    await waitFor(() => {
      expect(apiClient.updateUserProfile).toHaveBeenCalledWith(expect.objectContaining({
        skills: ['Java', 'Spring', 'Microservices'],
      }));
    });
  });
});
