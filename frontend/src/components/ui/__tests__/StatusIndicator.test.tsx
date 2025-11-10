import { render, screen } from '@testing-library/react';

import StatusIndicator from '../StatusIndicator';

describe('StatusIndicator', () => {
  describe('Rendering', () => {
    it('renders dot only by default when no label provided', () => {
      const { container } = render(<StatusIndicator variant="success" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toBeInTheDocument();
      expect(dot).toHaveClass('status-dot-success');
    });

    it('renders with label when provided', () => {
      render(<StatusIndicator variant="success" label="Active" />);
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders dot only when dotOnly prop is true', () => {
      const { container } = render(
        <StatusIndicator variant="success" label="Active" dotOnly />
      );
      expect(screen.queryByText('Active')).not.toBeInTheDocument();
      const dot = container.querySelector('.status-dot');
      expect(dot).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('applies success variant classes', () => {
      const { container } = render(<StatusIndicator variant="success" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-success');
    });

    it('applies warning variant classes', () => {
      const { container } = render(<StatusIndicator variant="warning" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-warning');
    });

    it('applies error variant classes', () => {
      const { container } = render(<StatusIndicator variant="error" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-error');
    });

    it('applies info variant classes', () => {
      const { container } = render(<StatusIndicator variant="info" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-info');
    });

    it('applies neutral variant classes', () => {
      const { container } = render(<StatusIndicator variant="neutral" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-neutral');
    });

    it('applies default neutral variant when no variant specified', () => {
      const { container } = render(<StatusIndicator />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-neutral');
    });
  });

  describe('Sizes', () => {
    it('applies small size classes', () => {
      const { container } = render(<StatusIndicator size="sm" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('w-2', 'h-2');
    });

    it('applies medium size classes by default', () => {
      const { container } = render(<StatusIndicator />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('w-2.5', 'h-2.5');
    });

    it('applies large size classes', () => {
      const { container } = render(<StatusIndicator size="lg" />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('w-3', 'h-3');
    });

    it('applies correct text size for labeled indicators', () => {
      const { container } = render(
        <StatusIndicator label="Test" size="sm" />
      );
      const indicator = container.querySelector('.status-indicator');
      expect(indicator).toHaveClass('text-xs');
    });
  });

  describe('Pulse Animation', () => {
    it('applies pulse animation when pulse prop is true', () => {
      const { container } = render(<StatusIndicator pulse />);
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('status-dot-pulse');
    });

    it('does not apply pulse animation by default', () => {
      const { container } = render(<StatusIndicator />);
      const dot = container.querySelector('.status-dot');
      expect(dot).not.toHaveClass('status-dot-pulse');
    });

    it('applies pulse animation to labeled indicators', () => {
      const { container } = render(
        <StatusIndicator label="Test" pulse />
      );
      const indicator = container.querySelector('.status-indicator');
      expect(indicator).toHaveClass('status-dot-pulse');
    });
  });

  describe('Accessibility', () => {
    it('has role="status"', () => {
      render(<StatusIndicator variant="success" />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has default aria-label for dot only', () => {
      render(<StatusIndicator variant="success" />);
      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-label', 'Status: success');
    });

    it('has aria-label with label text', () => {
      render(<StatusIndicator variant="success" label="Active" />);
      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-label', 'Status: Active');
    });

    it('accepts custom aria-label', () => {
      render(
        <StatusIndicator
          variant="success"
          ariaLabel="Custom status label"
        />
      );
      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-label', 'Custom status label');
    });

    it('hides decorative dot from screen readers in labeled mode', () => {
      const { container } = render(
        <StatusIndicator variant="success" label="Active" />
      );
      const dots = container.querySelectorAll('.status-dot');
      const decorativeDot = Array.from(dots).find(
        (dot) => dot.getAttribute('aria-hidden') === 'true'
      );
      expect(decorativeDot).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <StatusIndicator className="custom-class" />
      );
      const dot = container.querySelector('.status-dot');
      expect(dot).toHaveClass('custom-class');
    });

    it('applies custom className to labeled indicator', () => {
      const { container } = render(
        <StatusIndicator label="Test" className="custom-class" />
      );
      const indicator = container.querySelector('.status-indicator');
      expect(indicator).toHaveClass('custom-class');
    });
  });

  describe('Variant with Label Combinations', () => {
    it('renders success indicator with label correctly', () => {
      const { container } = render(
        <StatusIndicator variant="success" label="Online" />
      );
      expect(screen.getByText('Online')).toBeInTheDocument();
      const indicator = container.querySelector('.status-indicator');
      expect(indicator).toHaveClass('status-indicator-success');
    });

    it('renders warning indicator with label correctly', () => {
      const { container } = render(
        <StatusIndicator variant="warning" label="Pending" />
      );
      expect(screen.getByText('Pending')).toBeInTheDocument();
      const indicator = container.querySelector('.status-indicator');
      expect(indicator).toHaveClass('status-indicator-warning');
    });

    it('renders error indicator with label correctly', () => {
      const { container } = render(
        <StatusIndicator variant="error" label="Failed" />
      );
      expect(screen.getByText('Failed')).toBeInTheDocument();
      const indicator = container.querySelector('.status-indicator');
      expect(indicator).toHaveClass('status-indicator-error');
    });
  });
});
