/**
 * Accessibility tests for Navigation components
 * Tests WCAG 2.1 AA compliance for navigation, skip links, and landmarks
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';

expect.extend(toHaveNoViolations);

// Mock Navigation component
const Navigation = ({ items }: { items: Array<{ href: string; label: string; current?: boolean }> }) => (
    <nav aria-label="Main navigation">
        <ul role="list">
            {items.map(item => (
                <li key={item.href}>
                    <a
                        href={item.href}
                        aria-current={item.current ? 'page' : undefined}
                    >
                        {item.label}
                    </a>
                </li>
            ))}
        </ul>
    </nav>
);

// Mock Skip Link component
const SkipLink = () => (
    <a href="#main-content" className="skip-link">
        Skip to main content
    </a>
);

// Mock Breadcrumb component
const Breadcrumb = ({ items }: { items: Array<{ href?: string; label: string }> }) => (
    <nav aria-label="Breadcrumb">
        <ol>
            {items.map((item, index) => (
                <li key={index}>
                    {item.href ? (
                        <a href={item.href}>{item.label}</a>
                    ) : (
                        <span aria-current="page">{item.label}</span>
                    )}
                </li>
            ))}
        </ol>
    </nav>
);

// Mock Page Layout with landmarks
const PageLayout = ({ children }: { children: React.ReactNode }) => (
    <div>
        <SkipLink />
        <header role="banner">
            <h1>Career Copilot</h1>
            <Navigation items={[
                { href: '/', label: 'Dashboard', current: true },
                { href: '/jobs', label: 'Jobs' },
                { href: '/applications', label: 'Applications' },
            ]} />
        </header>
        <main id="main-content" role="main">
            {children}
        </main>
        <footer role="contentinfo">
            <p>&copy; 2025 Career Copilot</p>
        </footer>
    </div>
);

describe('Navigation Accessibility', () => {
    const navItems = [
        { href: '/', label: 'Home', current: true },
        { href: '/about', label: 'About' },
        { href: '/contact', label: 'Contact' },
    ];

    it('should have no axe violations', async () => {
        const { container } = render(<Navigation items={navItems} />);

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have accessible navigation landmark', () => {
        render(<Navigation items={navItems} />);

        const nav = screen.getByRole('navigation');
        expect(nav).toHaveAccessibleName('Main navigation');
    });

    it('should mark current page with aria-current', () => {
        render(<Navigation items={navItems} />);

        const currentLink = screen.getByRole('link', { name: 'Home' });
        expect(currentLink).toHaveAttribute('aria-current', 'page');

        const otherLink = screen.getByRole('link', { name: 'About' });
        expect(otherLink).not.toHaveAttribute('aria-current');
    });

    it('should have list semantics', () => {
        render(<Navigation items={navItems} />);

        const list = screen.getByRole('list');
        expect(list).toBeInTheDocument();

        const listItems = screen.getAllByRole('listitem');
        expect(listItems).toHaveLength(3);
    });

    it('should support keyboard navigation', async () => {
        const user = userEvent.setup();
        render(<Navigation items={navItems} />);

        const links = screen.getAllByRole('link');

        // Tab to first link
        await user.tab();
        expect(links[0]).toHaveFocus();

        // Tab to second link
        await user.tab();
        expect(links[1]).toHaveFocus();

        // Tab to third link
        await user.tab();
        expect(links[2]).toHaveFocus();
    });
});

describe('Skip Link Accessibility', () => {
    it('should have no axe violations', async () => {
        const { container } = render(<SkipLink />);

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have descriptive link text', () => {
        render(<SkipLink />);

        const skipLink = screen.getByRole('link', { name: /skip to main content/i });
        expect(skipLink).toBeInTheDocument();
        expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    it('should be keyboard accessible', async () => {
        const user = userEvent.setup();
        render(<SkipLink />);

        const skipLink = screen.getByRole('link', { name: /skip to main content/i });

        // Tab to skip link (should be first focusable element)
        await user.tab();
        expect(skipLink).toHaveFocus();
    });
});

describe('Breadcrumb Accessibility', () => {
    const breadcrumbItems = [
        { href: '/', label: 'Home' },
        { href: '/jobs', label: 'Jobs' },
        { label: 'Software Engineer' }, // Current page (no href)
    ];

    it('should have no axe violations', async () => {
        const { container } = render(<Breadcrumb items={breadcrumbItems} />);

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have accessible breadcrumb navigation', () => {
        render(<Breadcrumb items={breadcrumbItems} />);

        const nav = screen.getByRole('navigation');
        expect(nav).toHaveAccessibleName('Breadcrumb');
    });

    it('should use ordered list for breadcrumb items', () => {
        render(<Breadcrumb items={breadcrumbItems} />);

        const list = screen.getByRole('list');
        expect(list.tagName).toBe('OL');

        const listItems = screen.getAllByRole('listitem');
        expect(listItems).toHaveLength(3);
    });

    it('should mark current page with aria-current', () => {
        render(<Breadcrumb items={breadcrumbItems} />);

        const currentPage = screen.getByText('Software Engineer');
        expect(currentPage).toHaveAttribute('aria-current', 'page');
    });

    it('should have clickable links for previous pages', () => {
        render(<Breadcrumb items={breadcrumbItems} />);

        const homeLink = screen.getByRole('link', { name: 'Home' });
        expect(homeLink).toHaveAttribute('href', '/');

        const jobsLink = screen.getByRole('link', { name: 'Jobs' });
        expect(jobsLink).toHaveAttribute('href', '/jobs');
    });
});

describe('Page Layout Landmarks', () => {
    it('should have no axe violations', async () => {
        const { container } = render(
            <PageLayout>
                <h2>Dashboard Content</h2>
                <p>Welcome to your dashboard</p>
            </PageLayout>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have banner landmark (header)', () => {
        render(
            <PageLayout>
                <p>Content</p>
            </PageLayout>
        );

        const banner = screen.getByRole('banner');
        expect(banner).toBeInTheDocument();
    });

    it('should have main landmark', () => {
        render(
            <PageLayout>
                <p>Content</p>
            </PageLayout>
        );

        const main = screen.getByRole('main');
        expect(main).toBeInTheDocument();
        expect(main).toHaveAttribute('id', 'main-content');
    });

    it('should have contentinfo landmark (footer)', () => {
        render(
            <PageLayout>
                <p>Content</p>
            </PageLayout>
        );

        const footer = screen.getByRole('contentinfo');
        expect(footer).toBeInTheDocument();
    });

    it('should have navigation landmark', () => {
        render(
            <PageLayout>
                <p>Content</p>
            </PageLayout>
        );

        const nav = screen.getByRole('navigation');
        expect(nav).toBeInTheDocument();
    });

    it('should have skip link as first focusable element', async () => {
        const user = userEvent.setup();
        render(
            <PageLayout>
                <p>Content</p>
            </PageLayout>
        );

        // Tab to first element
        await user.tab();

        const skipLink = screen.getByRole('link', { name: /skip to main content/i });
        expect(skipLink).toHaveFocus();
    });

    it('should have proper heading hierarchy', () => {
        render(
            <PageLayout>
                <h2>Section Heading</h2>
                <p>Content</p>
            </PageLayout>
        );

        // h1 in header
        const mainHeading = screen.getByRole('heading', { level: 1 });
        expect(mainHeading).toHaveTextContent('Career Copilot');

        // h2 in main content
        const sectionHeading = screen.getByRole('heading', { level: 2 });
        expect(sectionHeading).toHaveTextContent('Section Heading');
    });
});

describe('Responsive Navigation', () => {
    const MobileNav = ({ isOpen, onToggle }: { isOpen: boolean; onToggle: () => void }) => (
        <nav aria-label="Mobile navigation">
            <button
                onClick={onToggle}
                aria-expanded={isOpen}
                aria-controls="mobile-menu"
                aria-label="Toggle navigation menu"
            >
                Menu
            </button>
            {isOpen && (
                <ul id="mobile-menu" role="menu">
                    <li role="none">
                        <a href="/" role="menuitem">Home</a>
                    </li>
                    <li role="none">
                        <a href="/about" role="menuitem">About</a>
                    </li>
                </ul>
            )}
        </nav>
    );

    it('should have no axe violations', async () => {
        const { container } = render(
            <MobileNav isOpen={false} onToggle={() => { }} />
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have accessible toggle button', () => {
        render(<MobileNav isOpen={false} onToggle={() => { }} />);

        const button = screen.getByRole('button', { name: /toggle navigation menu/i });
        expect(button).toBeInTheDocument();
        expect(button).toHaveAttribute('aria-expanded', 'false');
        expect(button).toHaveAttribute('aria-controls', 'mobile-menu');
    });

    it('should update aria-expanded when menu opens', () => {
        render(<MobileNav isOpen={true} onToggle={() => { }} />);

        const button = screen.getByRole('button');
        expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('should show menu items when open', () => {
        render(<MobileNav isOpen={true} onToggle={() => { }} />);

        const menu = screen.getByRole('menu');
        expect(menu).toHaveAttribute('id', 'mobile-menu');

        const menuItems = screen.getAllByRole('menuitem');
        expect(menuItems).toHaveLength(2);
    });

    it('should support keyboard interaction', async () => {
        const user = userEvent.setup();
        const onToggle = jest.fn();

        render(<MobileNav isOpen={false} onToggle={onToggle} />);

        const button = screen.getByRole('button');

        // Activate with Enter
        button.focus();
        await user.keyboard('{Enter}');
        expect(onToggle).toHaveBeenCalled();
    });
});
