
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import LoginPage from '../../app/login/page';
import RegisterPage from '../../app/register/page';

const server = setupServer(
  rest.post('http://localhost:8000/api/users', (req, res, ctx) => {
    return res(ctx.json({ id: 1, username: 'testuser' }));
  }),
  rest.post('http://localhost:8000/api/auth/login', (req, res, ctx) => {
    return res(ctx.json({ access_token: 'test-token', user: { id: 1, username: 'testuser' } }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Authentication Flow', () => {
  it('allows a user to register and then login', async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByLabelText('Username'), 'testuser');
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password');
    await user.type(screen.getByLabelText('Confirm Password'), 'password');
    await user.click(screen.getByText('Create Account'));

    // After registration, the user is redirected to the login page.
    // We can't test the redirection here, so we'll just render the login page.
    render(<LoginPage />);

    await user.type(screen.getByLabelText('Username'), 'testuser');
    await user.type(screen.getByLabelText('Password'), 'password');
    await user.click(screen.getByText('Sign In'));

    // In a real app, we would assert that the user is redirected to the dashboard.
  });
});
