/**
 * Unit tests for Footer component
 * Tests dynamic copyright year and layout structure
 */

import { render, screen } from '@testing-library/react';
import Footer from '../Footer';

describe('Footer', () => {
    describe('Dynamic Copyright Year', () => {
        it('renders current year dynamically', () => {
            render(<Footer />);

            const currentYear = new Date().getFullYear();
            const copyrightText = screen.getByText(new RegExp(`© ${currentYear} Career Copilot`, 'i'));

            expect(copyrightText).toBeInTheDocument();
        });

        it('does not have hardcoded year', () => {
            const { container } = render(<Footer />);

            // Check that no hardcoded 2024 or 2025 exists (unless it's actually current year)
            const currentYear = new Date().getFullYear();
            const htmlContent = container.innerHTML;

            if (currentYear !== 2024) {
                expect(htmlContent).not.toMatch(/©\s*2024/);
            }
            if (currentYear !== 2025) {
                expect(htmlContent).not.toMatch(/©\s*2025/);
            }
        });

        it('updates year on re-render', () => {
            // Mock date
            const mockDate = new Date('2026-01-01');
            jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

            render(<Footer />);

            expect(screen.getByText(/© 2026 Career Copilot/i)).toBeInTheDocument();

            jest.restoreAllMocks();
        });
    });

    describe('Layout Structure', () => {
        it('renders Contact Support link', () => {
            render(<Footer />);

            const contactLink = screen.getByText(/Contact Support/i);
            expect(contactLink).toBeInTheDocument();
        });

        it('renders GitHub link', () => {
            render(<Footer />);

            const githubLink = screen.getByText('GitHub');
            expect(githubLink).toBeInTheDocument();
        });

        it('renders Features section header', () => {
            render(<Footer />);

            const featuresHeader = screen.getByText('Features');
            expect(featuresHeader).toBeInTheDocument();
        });

        it('renders Resources section header', () => {
            render(<Footer />);

            const resourcesHeader = screen.getByText('Resources');
            expect(resourcesHeader).toBeInTheDocument();
        });
    });

    describe('Grid Alignment', () => {
        it('uses responsive grid layout', () => {
            const { container } = render(<Footer />);

            const grid = container.querySelector('.grid');
            expect(grid).toHaveClass('grid-cols-1', 'sm:grid-cols-2', 'lg:grid-cols-4');
        });

        it('has consistent spacing', () => {
            const { container } = render(<Footer />);

            const grid = container.querySelector('.grid');
            expect(grid).toHaveClass('gap-8');
        });
    });

    describe('Accessibility', () => {
        it('renders footer landmark', () => {
            const { container } = render(<Footer />);

            const footer = container.querySelector('footer');
            expect(footer).toBeInTheDocument();
        });

        it('has accessible contact links', () => {
            render(<Footer />);

            const mailLink = screen.getByRole('link', { name: /Contact Support/i });
            expect(mailLink).toHaveAttribute('href', 'mailto:support@careercopilot.com');

            const githubLink = screen.getByRole('link', { name: /GitHub/i });
            expect(githubLink).toHaveAttribute('href', 'https://github.com/career-copilot');
            expect(githubLink).toHaveAttribute('target', '_blank');
            expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer');
        });

        it('maintains minimum touch target sizes', () => {
            const { container } = render(<Footer />);

            const links = container.querySelectorAll('a');
            links.forEach(link => {
                // Check for minimum height class
                expect(link).toHaveClass('min-h-[44px]');
            });
        });
    });
});
