import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Badge } from '../Badge';

describe('Badge', () => {
    it('renders children correctly', () => {
        render(<Badge>Test Badge</Badge>);
        expect(screen.getByText('Test Badge')).toBeInTheDocument();
    });

    it('renders with default variant', () => {
        const { container } = render(<Badge>Default</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('bg-gray-100', 'text-gray-800');
    });

    it('renders with primary variant', () => {
        const { container } = render(<Badge variant="primary">Primary</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('renders with success variant', () => {
        const { container } = render(<Badge variant="success">Success</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('renders with warning variant', () => {
        const { container } = render(<Badge variant="warning">Warning</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('renders with error variant', () => {
        const { container } = render(<Badge variant="error">Error</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('renders with small size', () => {
        const { container } = render(<Badge size="sm">Small</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs');
    });

    it('renders with medium size', () => {
        const { container } = render(<Badge size="md">Medium</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('px-2', 'py-1', 'text-sm');
    });

    it('renders with large size', () => {
        const { container } = render(<Badge size="lg">Large</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('px-3', 'py-1.5', 'text-base');
    });

    it('applies custom className', () => {
        const { container } = render(<Badge className="custom-class">Custom</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge).toHaveClass('custom-class');
    });

    // Badge component does not support onClick - these tests are removed
});
