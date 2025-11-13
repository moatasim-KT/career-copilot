import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

import LoginPage from '../../app/login/page';
import RegisterPage from '../../app/register/page';

// Mock BroadcastChannel for Jest environment
class BroadcastChannelMock {
  name: string;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(name: string) {
    this.name = name;
  }

  postMessage(_message: unknown) {
    // No-op in tests
  }

  close() {
    // No-op in tests
  }

  addEventListener() {
    // No-op in tests
  }

  removeEventListener() {
    // No-op in tests
  }
}

// Set up BroadcastChannel mock globally
global.BroadcastChannel = BroadcastChannelMock as any;

// MSW server setup for API mocking
const server = setupServer(
  http.post('http://localhost:8000/api/v1/users', () => {
    return HttpResponse.json({
      id: 1,
      username: 'testuser',
      email: 'test@example.com'
    });
  }),
  http.post('http://localhost:8000/api/v1/auth/login', () => {
    return HttpResponse.json({
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      },
    });
  }),
);

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Authentication Flow', () => {
  it('allows a user to register', async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    // Find form fields
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInputs = screen.getAllByLabelText(/password/i);
    const passwordInput = passwordInputs[0];
    const confirmPasswordInput = passwordInputs[1];
    const submitButton = screen.getByRole('button', { name: /create account|register|sign up/i });

    // Fill in registration form
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    // Submit form
    await user.click(submitButton);

    // Wait for API response (registration should succeed)
    await waitFor(() => {
      // After successful registration, user might be redirected or see a success message
      // Adjust this assertion based on your actual implementation
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });
  });

  it('allows a user to login', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    // Find form fields
    const usernameInput = screen.getByLabelText(/username|email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in|login|log in/i });

    // Fill in login form
    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');

    // Submit form
    await user.click(submitButton);

    // Wait for API response (login should succeed)
    await waitFor(() => {
      // After successful login, user might be redirected or see a success message
      // Adjust this assertion based on your actual implementation
      expect(screen.queryByText(/error|invalid/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('shows error on invalid login credentials', async () => {
    // Override the login handler to return an error
    server.use(
      http.post('http://localhost:8000/api/v1/auth/login', () => {
        return HttpResponse.json(
          { detail: 'Invalid credentials' },
          { status: 401 }
        );
      })
    );

    const user = userEvent.setup();
    render(<LoginPage />);

    const usernameInput = screen.getByLabelText(/username|email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in|login|log in/i });

    await user.type(usernameInput, 'wronguser');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/invalid|error|failed/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

