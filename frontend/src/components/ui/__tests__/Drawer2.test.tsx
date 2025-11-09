import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import Drawer2 from '../Drawer2';

describe('Drawer2', () => {
  it('renders when open is true', () => {
    render(
      <Drawer2 open={true} onClose={() => {}}>
        <div>Drawer content</div>
      </Drawer2>
    );

    expect(screen.getByText('Drawer content')).toBeInTheDocument();
  });

  it('does not render when open is false', () => {
    render(
      <Drawer2 open={false} onClose={() => {}}>
        <div>Drawer content</div>
      </Drawer2>
    );

    expect(screen.queryByText('Drawer content')).not.toBeInTheDocument();
  });

  it('renders title and description when provided', () => {
    render(
      <Drawer2 open={true} onClose={() => {}} title="Test Title" description="Test Description">
        <div>Drawer content</div>
      </Drawer2>
    );

    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Drawer2 open={true} onClose={onClose}>
        <div>Drawer content</div>
      </Drawer2>
    );

    const closeButton = screen.getByLabelText('Close drawer');
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape key is pressed', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Drawer2 open={true} onClose={onClose}>
        <div>Drawer content</div>
      </Drawer2>
    );

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Drawer2 open={true} onClose={onClose}>
        <div>Drawer content</div>
      </Drawer2>
    );

    // Click the backdrop (the parent div)
    const backdrop = screen.getByRole('dialog').parentElement;
    if (backdrop) {
      await user.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    }
  });

  it('does not call onClose when drawer content is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <Drawer2 open={true} onClose={onClose}>
        <div>Drawer content</div>
      </Drawer2>
    );

    const content = screen.getByText('Drawer content');
    await user.click(content);

    expect(onClose).not.toHaveBeenCalled();
  });

  it('hides close button when showClose is false', () => {
    render(
      <Drawer2 open={true} onClose={() => {}} showClose={false}>
        <div>Drawer content</div>
      </Drawer2>
    );

    expect(screen.queryByLabelText('Close drawer')).not.toBeInTheDocument();
  });

  it('applies correct side positioning', () => {
    const { rerender } = render(
      <Drawer2 open={true} onClose={() => {}} side="left">
        <div>Drawer content</div>
      </Drawer2>
    );

    let drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('left-0');

    rerender(
      <Drawer2 open={true} onClose={() => {}} side="right">
        <div>Drawer content</div>
      </Drawer2>
    );

    drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('right-0');

    rerender(
      <Drawer2 open={true} onClose={() => {}} side="bottom">
        <div>Drawer content</div>
      </Drawer2>
    );

    drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('bottom-0');
  });

  it('applies correct size class', () => {
    const { rerender } = render(
      <Drawer2 open={true} onClose={() => {}} size="sm">
        <div>Drawer content</div>
      </Drawer2>
    );

    let drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-64');

    rerender(
      <Drawer2 open={true} onClose={() => {}} size="lg">
        <div>Drawer content</div>
      </Drawer2>
    );

    drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('w-[32rem]');
  });

  it('applies custom className', () => {
    render(
      <Drawer2 open={true} onClose={() => {}} className="custom-class">
        <div>Drawer content</div>
      </Drawer2>
    );

    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('custom-class');
  });

  it('prevents body scroll when open', () => {
    const { rerender } = render(
      <Drawer2 open={true} onClose={() => {}}>
        <div>Drawer content</div>
      </Drawer2>
    );

    expect(document.body.style.overflow).toBe('hidden');

    rerender(
      <Drawer2 open={false} onClose={() => {}}>
        <div>Drawer content</div>
      </Drawer2>
    );

    expect(document.body.style.overflow).toBe('');
  });

  it('has proper ARIA attributes', () => {
    render(
      <Drawer2
        open={true}
        onClose={() => {}}
        title="Test Title"
        description="Test Description"
        ariaLabelledBy="custom-title"
        ariaDescribedBy="custom-desc"
      >
        <div>Drawer content</div>
      </Drawer2>
    );

    const drawer = screen.getByRole('dialog');
    expect(drawer).toHaveAttribute('aria-labelledby', 'custom-title');
    expect(drawer).toHaveAttribute('aria-describedby', 'custom-desc');
    expect(drawer.parentElement).toHaveAttribute('aria-modal', 'true');
  });

  it('applies correct border radius based on side', () => {
    const { rerender } = render(
      <Drawer2 open={true} onClose={() => {}} side="left">
        <div>Drawer content</div>
      </Drawer2>
    );

    let drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('rounded-r-xl');

    rerender(
      <Drawer2 open={true} onClose={() => {}} side="right">
        <div>Drawer content</div>
      </Drawer2>
    );

    drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('rounded-l-xl');

    rerender(
      <Drawer2 open={true} onClose={() => {}} side="bottom">
        <div>Drawer content</div>
      </Drawer2>
    );

    drawer = screen.getByRole('dialog');
    expect(drawer).toHaveClass('rounded-t-xl');
  });
});
