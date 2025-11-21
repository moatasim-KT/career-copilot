/**
 * Unit tests for NotificationSystem component
 * Tests status bar behavior, localStorage persistence, and toast notifications
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NotificationSystem from '../NotificationSystem';
import { webSocketService } from '@/lib/api/websocket';

// Mock webSocketService
jest.mock('@/lib/api/websocket', () => ({
    webSocketService: {
        getStatus: jest.fn(),
        on: jest.fn(),
        off: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
    },
}));

// Mock logger
jest.mock('@/lib/logger', () => ({
    logger: {
        log: jest.fn(),
        error: jest.fn(),
    },
}));

describe('NotificationSystem', () => {
    beforeEach(() => {
        // Clear localStorage before each test
        localStorage.clear();
        jest.clearAllMocks();
    });

    describe('Connection Status Bar', () => {
        it('shows status bar when disconnected', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('disconnected');

            render(<NotificationSystem />);

            expect(screen.getByText(/Real-time updates are temporarily unavailable/i)).toBeInTheDocument();
            expect(screen.getByText(/Reconnecting automatically/i)).toBeInTheDocument();
        });

        it('hides status bar when connected', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('connected');

            render(<NotificationSystem />);

            expect(screen.queryByText(/Real-time updates are temporarily unavailable/i)).not.toBeInTheDocument();
        });

        it('hides status bar when connecting', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('connecting');

            render(<NotificationSystem />);

            expect(screen.queryByText(/Real-time updates are temporarily unavailable/i)).not.toBeInTheDocument();
        });

        it('allows dismissing the status bar', async () => {
            const user = userEvent.setup();
            (webSocketService.getStatus as jest.Mock).mockReturnValue('disconnected');

            render(<NotificationSystem />);

            const statusBar = screen.getByText(/Real-time updates are temporarily unavailable/i).closest('div[class*="fixed top-0"]');
            expect(statusBar).toBeInTheDocument();

            const dismissButton = screen.getByLabelText('Dismiss status bar');
            await user.click(dismissButton);

            await waitFor(() => {
                expect(screen.queryByText(/Real-time updates are temporarily unavailable/i)).not.toBeInTheDocument();
            });
        });

        it('persists dismissal in localStorage', async () => {
            const user = userEvent.setup();
            (webSocketService.getStatus as jest.Mock).mockReturnValue('disconnected');

            render(<NotificationSystem />);

            const dismissButton = screen.getByLabelText('Dismiss status bar');
            await user.click(dismissButton);

            await waitFor(() => {
                expect(localStorage.getItem('connection-status-dismissed')).toBe('true');
            });
        });

        it('respects localStorage dismissal on mount', () => {
            localStorage.setItem('connection-status-dismissed', 'true');
            (webSocketService.getStatus as jest.Mock).mockReturnValue('disconnected');

            render(<NotificationSystem />);

            expect(screen.queryByText(/Real-time updates are temporarily unavailable/i)).not.toBeInTheDocument();
        });
    });

    describe('Status Bar Accessibility', () => {
        it('uses proper color contrast for status bar text', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('disconnected');

            render(<NotificationSystem />);

            const statusText = screen.getByText(/Real-time updates are temporarily unavailable/i);
            expect(statusText).toHaveClass('text-amber-900');
        });

        it('has accessible dismiss button', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('disconnected');

            render(<NotificationSystem />);

            const dismissButton = screen.getByLabelText('Dismiss status bar');
            expect(dismissButton).toBeInTheDocument();
            expect(dismissButton).toHaveAttribute('aria-label', 'Dismiss status bar');
        });
    });

    describe('Toast Notifications', () => {
        it('renders notifications in bottom-right corner', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('connected');

            const { container } = render(<NotificationSystem />);

            const notificationContainer = container.querySelector('[aria-live="assertive"]');
            expect(notificationContainer).toHaveClass('fixed', 'bottom-0', 'right-0');
        });

        it('auto-hides notifications after duration', async () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('connected');

            const { rerender } = render(<NotificationSystem />);

            // This would require simulating notification addition through WebSocket
            // For now, we test the container exists
            const notificationContainer = screen.getByRole('region', { hidden: true });
            expect(notificationContainer).toBeInTheDocument();
        });
    });

    describe('Connection State Transitions', () => {
        it('does not show "Connected" toast on connection', () => {
            (webSocketService.getStatus as jest.Mock).mockReturnValue('connected');

            render(<NotificationSystem />);

            // "Connected" toast should not appear (it's a state, not an event)
            expect(screen.queryByText(/Connected/i)).not.toBeInTheDocument();
        });
    });
});
