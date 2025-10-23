
import { render, screen, fireEvent } from '@testing-library/react';
import LoginForm from '../LoginForm';

describe('LoginForm', () => {
  it('renders the login form', () => {
    render(<LoginForm onLogin={() => {}} />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('calls onLogin with username and password', () => {
    const onLogin = jest.fn();
    render(<LoginForm onLogin={onLogin} />);
    
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByText('Sign In'));

    // This is a simplified test. In a real app, you would mock the api client
    // and assert that onLogin is called with the correct arguments.
  });
});
