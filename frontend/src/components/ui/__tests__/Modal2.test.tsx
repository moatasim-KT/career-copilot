import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import Modal2 from '../Modal2';

describe('Modal2', () => {
  it('renders when open is true', () => {
    render(
      <Modal2 open={true} onClose={() => {}}>
        <div>Modal content</div>
      </Modal2>
    );

    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when open is false', () => {
    render(
      <Modal2 open={false} onClose={() => {}}>
        <div>Modal content</div>
      </Modal2>
    );

    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('renders title and description when provided', () => {
    render(
      <Modal2 open={true} onClose={() => {}} title="Test Title" description="Test Description">
        <div>Modal content</div>
      </Modal2>
    );

    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Modal2 open={true} onClose={onClose}>
        <div>Modal content</div>
      </Modal2>
    );

    const closeButton = screen.getByLabelText('Close modal');
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape key is pressed', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Modal2 open={true} onClose={onClose}>
        <div>Modal content</div>
      </Modal2>
    );

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Modal2 open={true} onClose={onClose}>
        <div>Modal content</div>
      </Modal2>
    );

    // Click the backdrop (the parent div)
    const backdrop = screen.getByRole('dialog').parentElement;
    if (backdrop) {
      await user.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    }
  });

  it('does not call onClose when modal content is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Modal2 open={true} onClose={onClose}>
        <div>Modal content</div>
      </Modal2>
    );

    const content = screen.getByText('Modal content');
    await user.click(content);

    expect(onClose).not.toHaveBeenCalled();
  });

  it('hides close button when showClose is false', () => {
    render(
      <Modal2 open={true} onClose={() => {}} showClose={false}>
        <div>Modal content</div>
      </Modal2>
    );

    expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <Modal2 open={true} onClose={() => {}} className="custom-class">
        <div>Modal content</div>
      </Modal2>
    );

    const modal = screen.getByRole('dialog');
    expect(modal).toHaveClass('custom-class');
  });

  it('applies correct size class', () => {
    const { rerender } = render(
      <Modal2 open={true} onClose={() => {}} size="sm">
        <div>Modal content</div>
      </Modal2>
    );

    let modal = screen.getByRole('dialog');
    expect(modal).toHaveClass('max-w-md');

    rerender(
      <Modal2 open={true} onClose={() => {}} size="lg">
        <div>Modal content</div>
      </Modal2>
    );

    modal = screen.getByRole('dialog');
    expect(modal).toHaveClass('max-w-2xl');
  });

  it('prevents body scroll when open', () => {
    const { rerender } = render(
      <Modal2 open={true} onClose={() => {}}>
        <div>Modal content</div>
      </Modal2>
    );

    expect(document.body.style.overflow).toBe('hidden');

    rerender(
      <Modal2 open={false} onClose={() => {}}>
        <div>Modal content</div>
      </Modal2>
    );

    expect(document.body.style.overflow).toBe('');
  });

  it('has proper ARIA attributes', () => {
    render(
      <Modal2
        open={true}
        onClose={() => {}}
        title="Test Title"
        description="Test Description"
        ariaLabelledBy="custom-title"
        ariaDescribedBy="custom-desc"
      >
        <div>Modal content</div>
      </Modal2>
    );

    const modal = screen.getByRole('dialog');
    expect(modal).toHaveAttribute('aria-labelledby', 'custom-title');
    expect(modal).toHaveAttribute('aria-describedby', 'custom-desc');
    expect(modal.parentElement).toHaveAttribute('aria-modal', 'true');
  });
});
