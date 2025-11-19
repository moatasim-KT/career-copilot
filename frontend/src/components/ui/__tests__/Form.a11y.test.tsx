/**
 * Accessibility tests for Form components
 * Tests WCAG 2.1 AA compliance for form inputs, labels, and error messages
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';

expect.extend(toHaveNoViolations);

// Mock Input component
const Input = ({
    id,
    label,
    error,
    required = false,
    type = 'text',
    ...props
}: {
    id: string;
    label: string;
    error?: string;
    required?: boolean;
    type?: string;
    [key: string]: any;
}) => (
    <div className="form-group">
        <label htmlFor={id}>
            {label}
            {required && <span aria-label="required"> *</span>}
        </label>
        <input
            id={id}
            type={type}
            aria-required={required}
            aria-invalid={!!error}
            aria-describedby={error ? `${id}-error` : undefined}
            {...props}
        />
        {error && (
            <span id={`${id}-error`} className="error-message" role="alert">
                {error}
            </span>
        )}
    </div>
);

// Mock Select component
const Select = ({
    id,
    label,
    options,
    error,
    required = false,
    ...props
}: {
    id: string;
    label: string;
    options: Array<{ value: string; label: string }>;
    error?: string;
    required?: boolean;
    [key: string]: any;
}) => (
    <div className="form-group">
        <label htmlFor={id}>
            {label}
            {required && <span aria-label="required"> *</span>}
        </label>
        <select
            id={id}
            aria-required={required}
            aria-invalid={!!error}
            aria-describedby={error ? `${id}-error` : undefined}
            {...props}
        >
            <option value="">Select an option</option>
            {options.map(opt => (
                <option key={opt.value} value={opt.value}>
                    {opt.label}
                </option>
            ))}
        </select>
        {error && (
            <span id={`${id}-error`} className="error-message" role="alert">
                {error}
            </span>
        )}
    </div>
);

describe('Input Accessibility', () => {
    it('should have no axe violations', async () => {
        const { container } = render(
            <Input id="username" label="Username" />
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should associate label with input', () => {
        render(<Input id="email" label="Email Address" />);

        const input = screen.getByLabelText('Email Address');
        expect(input).toBeInTheDocument();
        expect(input).toHaveAttribute('id', 'email');
    });

    it('should mark required fields with aria-required', () => {
        render(<Input id="password" label="Password" required />);

        const input = screen.getByLabelText(/password/i);
        expect(input).toHaveAttribute('aria-required', 'true');
    });

    it('should have accessible required indicator', () => {
        render(<Input id="name" label="Full Name" required />);

        const requiredIndicator = screen.getByLabelText('required');
        expect(requiredIndicator).toBeInTheDocument();
    });

    it('should have no axe violations with error', async () => {
        const { container } = render(
            <Input
                id="username"
                label="Username"
                error="Username is required"
            />
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should announce errors with aria-invalid and role=alert', () => {
        render(
            <Input
                id="email"
                label="Email"
                error="Invalid email format"
            />
        );

        const input = screen.getByLabelText('Email');
        expect(input).toHaveAttribute('aria-invalid', 'true');

        const errorMessage = screen.getByText('Invalid email format');
        expect(errorMessage).toHaveAttribute('role', 'alert');
    });

    it('should associate error message with input via aria-describedby', () => {
        render(
            <Input
                id="password"
                label="Password"
                error="Password must be at least 8 characters"
            />
        );

        const input = screen.getByLabelText('Password');
        expect(input).toHaveAttribute('aria-describedby', 'password-error');

        const errorMessage = screen.getByText(/password must be at least 8 characters/i);
        expect(errorMessage).toHaveAttribute('id', 'password-error');
    });

    it('should support keyboard input', async () => {
        const user = userEvent.setup();
        render(<Input id="search" label="Search" />);

        const input = screen.getByLabelText('Search');
        await user.type(input, 'test query');

        expect(input).toHaveValue('test query');
    });
});

describe('Select Accessibility', () => {
    const options = [
        { value: 'option1', label: 'Option 1' },
        { value: 'option2', label: 'Option 2' },
        { value: 'option3', label: 'Option 3' },
    ];

    it('should have no axe violations', async () => {
        const { container } = render(
            <Select id="country" label="Country" options={options} />
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should associate label with select', () => {
        render(<Select id="role" label="Role" options={options} />);

        const select = screen.getByLabelText('Role');
        expect(select).toBeInTheDocument();
        expect(select).toHaveAttribute('id', 'role');
    });

    it('should mark required fields', () => {
        render(<Select id="status" label="Status" options={options} required />);

        const select = screen.getByLabelText(/status/i);
        expect(select).toHaveAttribute('aria-required', 'true');
    });

    it('should announce errors correctly', () => {
        render(
            <Select
                id="country"
                label="Country"
                options={options}
                error="Please select a country"
            />
        );

        const select = screen.getByLabelText('Country');
        expect(select).toHaveAttribute('aria-invalid', 'true');
        expect(select).toHaveAttribute('aria-describedby', 'country-error');

        const errorMessage = screen.getByRole('alert');
        expect(errorMessage).toHaveTextContent('Please select a country');
    });

    it('should support keyboard navigation', async () => {
        const user = userEvent.setup();
        render(<Select id="role" label="Role" options={options} />);

        const select = screen.getByLabelText('Role') as HTMLSelectElement;

        // Focus select
        select.focus();
        expect(select).toHaveFocus();

        // Native select starts with first option selected when no default
        // Arrow down should move to next option
        await user.keyboard('{ArrowDown}');

        // The select element should still have focus
        expect(select).toHaveFocus();
    });
});

describe('Form Accessibility', () => {
    const SimpleForm = () => (
        <form aria-label="Contact form">
            <Input id="name" label="Name" required />
            <Input id="email" label="Email" type="email" required />
            <Select
                id="topic"
                label="Topic"
                options={[
                    { value: 'support', label: 'Support' },
                    { value: 'sales', label: 'Sales' },
                ]}
                required
            />
            <button type="submit">Submit</button>
        </form>
    );

    it('should have no axe violations', async () => {
        const { container } = render(<SimpleForm />);

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have accessible form label', () => {
        render(<SimpleForm />);

        const form = screen.getByRole('form');
        expect(form).toHaveAccessibleName('Contact form');
    });

    it('should have all inputs labeled', () => {
        render(<SimpleForm />);

        expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/topic/i)).toBeInTheDocument();
    });

    it('should support sequential keyboard navigation', async () => {
        const user = userEvent.setup();
        render(<SimpleForm />);

        // Tab through form fields
        await user.tab();
        expect(screen.getByLabelText(/name/i)).toHaveFocus();

        await user.tab();
        expect(screen.getByLabelText(/email/i)).toHaveFocus();

        await user.tab();
        expect(screen.getByLabelText(/topic/i)).toHaveFocus();

        await user.tab();
        expect(screen.getByRole('button', { name: /submit/i })).toHaveFocus();
    });
});

describe('Fieldset and Legend Accessibility', () => {
    const FieldsetForm = () => (
        <form>
            <fieldset>
                <legend>Personal Information</legend>
                <Input id="firstName" label="First Name" />
                <Input id="lastName" label="Last Name" />
            </fieldset>
            <fieldset>
                <legend>Contact Preferences</legend>
                <div role="group" aria-labelledby="contact-methods">
                    <span id="contact-methods">How would you like to be contacted?</span>
                    <label>
                        <input type="checkbox" name="email" /> Email
                    </label>
                    <label>
                        <input type="checkbox" name="phone" /> Phone
                    </label>
                </div>
            </fieldset>
        </form>
    );

    it('should have no axe violations', async () => {
        const { container } = render(<FieldsetForm />);

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have accessible fieldset legends', () => {
        render(<FieldsetForm />);

        expect(screen.getByText('Personal Information')).toBeInTheDocument();
        expect(screen.getByText('Contact Preferences')).toBeInTheDocument();
    });

    it('should group related checkboxes', () => {
        render(<FieldsetForm />);

        const groups = screen.getAllByRole('group', { name: 'How would you like to be contacted?' });
        expect(groups).toHaveLength(1);

        const checkboxes = screen.getAllByRole('checkbox');
        expect(checkboxes).toHaveLength(2);
    });
});
