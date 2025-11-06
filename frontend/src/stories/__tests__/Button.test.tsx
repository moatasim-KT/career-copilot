import { render, screen } from '@testing-library/react';
import React from 'react';

import '@testing-library/jest-dom';
import { Button } from '../Button';

describe('Button', () => {
  it('renders with primary styling', () => {
    render(<Button primary label="Primary Button" />);
    const button = screen.getByRole('button', { name: /primary button/i });
    expect(button).toHaveClass('storybook-button--primary');
  });

  it('renders with secondary styling', () => {
    render(<Button label="Secondary Button" />);
    const button = screen.getByRole('button', { name: /secondary button/i });
    expect(button).toHaveClass('storybook-button--secondary');
  });

  it('renders with custom background color', () => {
    render(<Button label="Custom Color" backgroundColor="#FF0000" />);
    const button = screen.getByRole('button', { name: /custom color/i });
    expect(button).toHaveStyle('background-color: #FF0000');
  });

  it('renders with large size', () => {
    render(<Button label="Large Button" size="large" />);
    const button = screen.getByRole('button', { name: /large button/i });
    expect(button).toHaveClass('storybook-button--large');
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button label="Click Me" onClick={handleClick} />);
    const button = screen.getByRole('button', { name: /click me/i });
    button.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
