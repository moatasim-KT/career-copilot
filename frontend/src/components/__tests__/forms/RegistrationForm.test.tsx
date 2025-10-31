import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import React from 'react';

import '@testing-library/jest-dom';
import RegistrationForm from '@/components/forms/RegistrationForm';
import { apiClient } from '@/lib/api';

// Mock the apiClient module
jest.mock('@/lib/api', () => ({
  apiClient: {
    register: jest.fn(),
  },
}));

describe('RegistrationForm', () => {
  const mockOnRegister = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (apiClient.register as jest.Mock).mockResolvedValue({
      data: { id: 1, username: 'newuser', email: 'new@example.com' },
    });
  });

  it('renders the registration form', () => {
    render(<RegistrationForm onRegister={mockOnRegister} />);
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Password', { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm Password', { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument();
  });

  it('handles successful registration', async () => {
    render(<RegistrationForm onRegister={mockOnRegister} />);

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'newuser' } });
      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'new@example.com' } });
      fireEvent.change(screen.getByLabelText('Password', { selector: 'input' }), { target: { value: 'newpassword' } });
      fireEvent.change(screen.getByLabelText('Confirm Password', { selector: 'input' }), { target: { value: 'newpassword' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    });

    await waitFor(() => {
      expect(apiClient.register).toHaveBeenCalledWith('newuser', 'new@example.com', 'newpassword');
      expect(mockOnRegister).toHaveBeenCalledTimes(1);
    });
  });

  it('displays an error message if passwords do not match', async () => {
    render(<RegistrationForm onRegister={mockOnRegister} />);

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'newuser' } });
      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'new@example.com' } });
      fireEvent.change(screen.getByLabelText('Password', { selector: 'input' }), { target: { value: 'newpassword' } });
      fireEvent.change(screen.getByLabelText('Confirm Password', { selector: 'input' }), { target: { value: 'differentpassword' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    });

    await waitFor(() => {
      expect(apiClient.register).not.toHaveBeenCalled();
      expect(mockOnRegister).not.toHaveBeenCalled();
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('displays an error message on failed registration', async () => {
    (apiClient.register as jest.Mock).mockResolvedValue({ error: 'Email already registered' });
    render(<RegistrationForm onRegister={mockOnRegister} />);

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'newuser' } });
      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'new@example.com' } });
      fireEvent.change(screen.getByLabelText('Password', { selector: 'input' }), { target: { value: 'newpassword' } });
      fireEvent.change(screen.getByLabelText('Confirm Password', { selector: 'input' }), { target: { value: 'newpassword' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    });

    await waitFor(() => {
      expect(apiClient.register).toHaveBeenCalledTimes(1);
      expect(mockOnRegister).not.toHaveBeenCalled();
      expect(screen.getByText(/Email already registered/i)).toBeInTheDocument();
    });
  });

  it('toggles password visibility', async () => {
    render(<RegistrationForm onRegister={mockOnRegister} />);

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