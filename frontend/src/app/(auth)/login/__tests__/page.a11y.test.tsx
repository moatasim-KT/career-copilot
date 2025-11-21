/**
 * Accessibility tests for Login Page
 * Tests color contrast, layout, and WCAG compliance
 */

import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import LoginPage from '../page';

// Mock Next.js router
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: jest.fn(),
        replace: jest.fn(),
    }),
}));

// Mock Auth Context
jest.mock('@/contexts/AuthContext', () => ({
    useAuth: () => ({
        login: jest.fn(),
        isAuthenticated: false,
    }),
}));

expect.extend(toHaveNoViolations);

describe('LoginPage Accessibility', () => {
    describe('Color Contrast Compliance', () => {
        it('should have no axe violations', async () => {
            const { container } = render(<LoginPage />);

            const results = await axe(container);
            expect(results).toHaveNoViolations();
        });

        it('uses accessible text color for "Or continue with"', () => {
            const { container } = render(<LoginPage />);

            const dividerText = screen.getByText(/Or continue with/i);

            // Should use text-slate-600 (not text-slate-500) for sufficient contrast
            expect(dividerText).toHaveClass('text-slate-600');
        });

        it('uses accessible colors in dark mode', () => {
            const { container } = render(<LoginPage />);

            const dividerText = screen.getByText(/Or continue with/i);

            // Should have dark mode variant
            expect(dividerText).toHaveClass('dark:text-slate-400');
        });
    });

    describe('Layout Structure', () => {
        it('renders hero section on large screens', () => {
            const { container } = render(<LoginPage />);

            // Hero section should have class for lg:flex
            const heroSection = container.querySelector('.lg\\:flex.lg\\:w-1\\/2');
            expect(heroSection).toBeInTheDocument();
        });

        it('renders login form section', () => {
            render(<LoginPage />);

            expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/Email or Username/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
        });

        it('uses proper flex layout to prevent overlay', () => {
            const { container } = render(<LoginPage />);

            const mainContainer = container.querySelector('.min-h-screen');
            expect(mainContainer).toHaveClass('flex', 'flex-row');
        });

        it('assigns correct z-index layers', () => {
            const { container } = render(<LoginPage />);

            // Login form should have z-30
            const loginForm = container.querySelector('.lg\\:w-1\\/2.relative.z-30');
            expect(loginForm).toBeInTheDocument();
        });
    });

    describe('Form Spacing Improvements', () => {
        it('has increased vertical spacing between inputs', () => {
            const { container } = render(<LoginPage />);

            const inputContainer = container.querySelector('[class*="space-y-6"]');
            expect(inputContainer).toBeInTheDocument();
        });

        it('has adequate margin on labels', () => {
            const { container } = render(<LoginPage />);

            const label = screen.getByText(/Email or Username/i);
            expect(label).toHaveClass('mb-2');
        });

        it('has larger gap between social buttons', () => {
            const { container } = render(<LoginPage />);

            const socialButtonGrid = container.querySelector('.grid.grid-cols-2');
            expect(socialButtonGrid).toHaveClass('gap-4');
        });

        it('has increased divider margin', () => {
            const { container } = render(<LoginPage />);

            const divider = container.querySelector('.relative.my-10');
            expect(divider).toBeInTheDocument();
        });
    });

    describe('Form Accessibility', () => {
        it('has accessible form labels', () => {
            render(<LoginPage />);

            const emailInput = screen.getByLabelText(/Email or Username/i);
            const passwordInput = screen.getByLabelText(/^Password$/i);

            expect(emailInput).toHaveAttribute('id', 'identifier');
            expect(passwordInput).toHaveAttribute('id', 'password');
        });

        it('requires both email and password', () => {
            render(<LoginPage />);

            const emailInput = screen.getByLabelText(/Email or Username/i);
            const passwordInput = screen.getByLabelText(/^Password$/i);

            expect(emailInput).toBeRequired();
            expect(passwordInput).toBeRequired();
        });

        it('has accessible sign in button', () => {
            render(<LoginPage />);

            const signInButton = screen.getByRole('button', { name: /Sign in/i });
            expect(signInButton).toBeInTheDocument();
        });

        it('has accessible OAuth buttons', () => {
            render(<LoginPage />);

            const githubButton = screen.getByRole('button', { name: /GitHub/i });
            const googleButton = screen.getByRole('button', { name: /Google/i });

            expect(githubButton).toBeInTheDocument();
            expect(googleButton).toBeInTheDocument();
        });

        it('OAuth buttons have adequate touch targets', () => {
            const { container } = render(<LoginPage />);

            const socialButtons = container.querySelectorAll('.btn-secondary');
            socialButtons.forEach(button => {
                expect(button).toHaveClass('py-3');
            });
        });
    });

    describe('Copyright Display', () => {
        it('shows dynamic copyright year in hero section', () => {
            render(<LoginPage />);

            const currentYear = new Date().getFullYear();
            const copyrightText = screen.getByText(new RegExp(`© ${currentYear} Career Copilot`, 'i'));

            expect(copyrightText).toBeInTheDocument();
        });
    });

    describe('Responsive Behavior', () => {
        it('hides hero section on mobile', () => {
            const { container } = render(<LoginPage />);

            const heroSection = container.querySelector('.hidden.lg\\:flex');
            expect(heroSection).toBeInTheDocument();
        });

        it('shows mobile logo', () => {
            const { container } = render(<LoginPage />);

            const mobileLogo = container.querySelector('.lg\\:hidden');
            expect(mobileLogo).toBeInTheDocument();
        });
    });
});
