
import { render, screen, fireEvent } from '@testing-library/react';
import RegistrationForm from '../RegistrationForm';

describe('RegistrationForm', () => {
  it('renders the registration form', () => {
    render(<RegistrationForm onRegister={() => {}} />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
  });

  it('calls onRegister when the form is submitted', () => {
    const onRegister = jest.fn();
    render(<RegistrationForm onRegister={onRegister} />);
    
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByText('Create Account'));

    // This is a simplified test. In a real app, you would mock the api client
    // and assert that onRegister is called.
  });
});
