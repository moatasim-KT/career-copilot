/**
 * Accessibility tests for Modal component
 * Tests WCAG 2.1 AA compliance for modal dialogs
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';

expect.extend(toHaveNoViolations);

// Mock Modal component (update path based on actual location)
const Modal = ({ isOpen, onClose, title, children }: {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
}) => {
    if (!isOpen) return null;

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            className="modal-overlay"
        >
            <div className="modal-content">
                <div className="modal-header">
                    <h2 id="modal-title">{title}</h2>
                    <button
                        onClick={onClose}
                        aria-label="Close dialog"
                        className="modal-close"
                    >
                        ×
                    </button>
                </div>
                <div className="modal-body">{children}</div>
            </div>
        </div>
    );
};

describe('Modal Accessibility', () => {
    it('should have no axe violations when open', async () => {
        const { container } = render(
            <Modal isOpen={true} onClose={() => { }} title="Test Modal">
                <p>Modal content</p>
            </Modal>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('should have proper ARIA attributes', () => {
        render(
            <Modal isOpen={true} onClose={() => { }} title="Test Modal">
                <p>Modal content</p>
            </Modal>
        );

        const dialog = screen.getByRole('dialog');
        expect(dialog).toHaveAttribute('aria-modal', 'true');
        expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
    });

    it('should have accessible close button', () => {
        const onClose = jest.fn();
        render(
            <Modal isOpen={true} onClose={onClose} title="Test Modal">
                <p>Modal content</p>
            </Modal>
        );

        const closeButton = screen.getByRole('button', { name: /close dialog/i });
        expect(closeButton).toBeInTheDocument();
        expect(closeButton).toHaveAccessibleName();
    });

    it('should have properly labeled title', () => {
        render(
            <Modal isOpen={true} onClose={() => { }} title="Important Dialog">
                <p>Modal content</p>
            </Modal>
        );

        const title = screen.getByText('Important Dialog');
        expect(title).toHaveAttribute('id', 'modal-title');
    });

    it('should support keyboard navigation', async () => {
        const user = userEvent.setup();
        const onClose = jest.fn();

        render(
            <Modal isOpen={true} onClose={onClose} title="Test Modal">
                <button>Action Button</button>
            </Modal>
        );

        // Tab to close button
        await user.tab();
        expect(screen.getByLabelText(/close dialog/i)).toHaveFocus();

        // Tab to action button
        await user.tab();
        expect(screen.getByText('Action Button')).toHaveFocus();
    });

    it('should not render when closed', () => {
        const { container } = render(
            <Modal isOpen={false} onClose={() => { }} title="Test Modal">
                <p>Modal content</p>
            </Modal>
        );

        expect(container.firstChild).toBeNull();
    });
});

describe('Modal Focus Management', () => {
    it('should trap focus within modal', async () => {
        const user = userEvent.setup();

        render(
            <Modal isOpen={true} onClose={() => { }} title="Test Modal">
                <button>First Button</button>
                <button>Second Button</button>
            </Modal>
        );

        const closeButton = screen.getByLabelText(/close dialog/i);
        const firstButton = screen.getByText('First Button');
        const secondButton = screen.getByText('Second Button');

        // Tab through all elements
        await user.tab();
        expect(closeButton).toHaveFocus();

        await user.tab();
        expect(firstButton).toHaveFocus();

        await user.tab();
        expect(secondButton).toHaveFocus();

        // Tab should wrap back to close button
        await user.tab();
        expect(closeButton).toHaveFocus();
    });

    it('should restore focus to trigger element on close', () => {
        const TriggerButton = () => {
            const [isOpen, setIsOpen] = React.useState(false);

            return (
                <>
                    <button onClick={() => setIsOpen(true)}>Open Modal</button>
                    <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Test">
                        <p>Content</p>
                    </Modal>
                </>
            );
        };

        const { getByText } = render(<TriggerButton />);
        const trigger = getByText('Open Modal');

        // Open modal
        trigger.click();
        expect(screen.getByRole('dialog')).toBeInTheDocument();

        // Close modal
        screen.getByLabelText(/close dialog/i).click();

        // Focus should return to trigger
        expect(trigger).toHaveFocus();
    });
});
