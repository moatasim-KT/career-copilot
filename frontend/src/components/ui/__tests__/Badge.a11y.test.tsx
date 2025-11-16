import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';

import { Badge, NotificationBadge, StatusBadge } from '../Badge';

describe('Badge accessibility', () => {
    it('renders default badge without accessibility violations', async () => {
        const { container } = render(<Badge>New</Badge>);
        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('announces notification counts politely', async () => {
        const { container } = render(<NotificationBadge count={5} />);
        const badge = screen.getByRole('status');
        expect(badge).toHaveAttribute('aria-label', '5 unread notifications');
        expect(badge).toHaveAttribute('aria-live', 'polite');
        expect(badge).toHaveAttribute('aria-atomic', 'true');

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('marks decorative dots as hidden in status badge', async () => {
        const { container } = render(<StatusBadge status="pending" />);
        const badge = screen.getByRole('status', { name: /pending status/i });
        expect(badge.querySelector('[aria-hidden="true"]')).toBeTruthy();

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });
});
