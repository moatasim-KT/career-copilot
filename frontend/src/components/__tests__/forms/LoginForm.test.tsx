import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import LoginForm from './LoginForm';
import { apiClient } from '@/lib/api';

// Mock the apiClient module
jest.mock('@/lib/api', () => ({
  apiClient: {
    login: jest.fn(),
  },
}));

// Mock next/navigation useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe('LoginForm', () => {
  const mockOnLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (apiClient.login as jest.Mock).mockResolvedValue({
      data: { access_token: 'fake-token', user: { id: 1, username: 'testuser' } },
    });
  });

  it('renders the login form', () => {
    render(<LoginForm onLogin={mockOnLogin} />);
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Password', { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    render(<LoginForm onLogin={mockOnLogin} />);

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByLabelText('Password', { selector: 'input' }), { target: { value: 'testpassword' } });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));
    });

    await waitFor(() => {
      expect(apiClient.login).toHaveBeenCalledWith('testuser', 'testpassword');
      expect(mockOnLogin).toHaveBeenCalledWith('fake-token', { id: 1, username: 'testuser' });
    });
  });

  it('displays an error message on failed login', async () => {
    (apiClient.login as jest.Mock).mockResolvedValue({ error: 'Invalid credentials' });
    render(<LoginForm onLogin={mockOnLogin} />);

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'wronguser' } });
      fireEvent.change(screen.getByLabelText('Password', { selector: 'input' }), { target: { value: 'wrongpass' } });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));
    });

    await waitFor(() => {
      expect(apiClient.login).toHaveBeenCalledWith('wronguser', 'wrongpass');
      expect(mockOnLogin).not.toHaveBeenCalled();
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('toggles password visibility', async () => {
    render(<LoginForm onLogin={mockOnLogin} />);

    const passwordInput = screen.getByLabelText('Password', { selector: 'input' }) as HTMLInputElement;
    const toggleButton = screen.getByRole('button', { name: /Toggle password visibility/i });

    expect(passwordInput.type).toBe('password');

    await act(async () => {
      fireEvent.click(toggleButton);
    });
    expect(passwordInput.type).toBe('text');

    await act(async () => {
      fireEvent.click(toggleButton);
    });
    expect(passwordInput.type).toBe('password');
  });
});