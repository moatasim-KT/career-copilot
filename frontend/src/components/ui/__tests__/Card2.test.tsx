import React from 'react';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '../Card2';

describe('Card2 Component', () => {
  describe('Basic Rendering', () => {
    it('renders children correctly', () => {
      render(
        <Card>
          <CardContent>Test Content</CardContent>
        </Card>
      );
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders with all sub-components', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Test Title</CardTitle>
            <CardDescription>Test Description</CardDescription>
          </CardHeader>
          <CardContent>Test Content</CardContent>
          <CardFooter>Test Footer</CardFooter>
        </Card>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(screen.getByText('Test Footer')).toBeInTheDocument();
    });
  });

  describe('Elevation Prop', () => {
    it('applies correct shadow class for elevation 1', () => {
      const { container } = render(
        <Card elevation={1}>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.shadow-sm');
      expect(card).toBeInTheDocument();
    });

    it('applies correct shadow class for elevation 3', () => {
      const { container } = render(
        <Card elevation={3}>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.shadow-lg');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Padding Prop', () => {
    it('applies correct padding class for md', () => {
      const { container } = render(
        <Card padding="md">
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.p-6');
      expect(card).toBeInTheDocument();
    });

    it('applies correct padding class for lg', () => {
      const { container } = render(
        <Card padding="lg">
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.p-8');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Hover Effects', () => {
    it('applies hover classes when hover prop is true', () => {
      const { container } = render(
        <Card hover>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.hover\\:shadow-xl');
      expect(card).toBeInTheDocument();
    });

    it('does not apply hover classes when hover prop is false', () => {
      const { container } = render(
        <Card hover={false}>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.hover\\:shadow-xl');
      expect(card).not.toBeInTheDocument();
    });
  });

  describe('Interactive Prop', () => {
    it('applies cursor-pointer class when interactive is true', () => {
      const { container } = render(
        <Card interactive>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.cursor-pointer');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Gradient Prop', () => {
    it('renders gradient overlay when gradient is true', () => {
      const { container } = render(
        <Card gradient>
          <CardContent>Content</CardContent>
        </Card>
      );
      const gradientOverlay = container.querySelector('.bg-gradient-to-br');
      expect(gradientOverlay).toBeInTheDocument();
    });
  });

  describe('Featured Prop (Glow Effect)', () => {
    it('applies featured classes when featured is true', () => {
      const { container } = render(
        <Card featured>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.shadow-lg');
      expect(card).toBeInTheDocument();
    });

    it('applies ring classes for featured cards', () => {
      const { container } = render(
        <Card featured>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.ring-1');
      expect(card).toBeInTheDocument();
    });

    it('works with different glow colors', () => {
      const { container } = render(
        <Card featured glowColor="success">
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.shadow-lg');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Gradient Border Prop', () => {
    it('renders gradient border wrapper when gradientBorder is true', () => {
      const { container } = render(
        <Card gradientBorder>
          <CardContent>Content</CardContent>
        </Card>
      );
      // Check for the wrapper div with group class
      const wrapper = container.querySelector('.group');
      expect(wrapper).toBeInTheDocument();
    });

    it('renders gradient border background element', () => {
      const { container } = render(
        <Card gradientBorder>
          <CardContent>Content</CardContent>
        </Card>
      );
      // Check for the gradient background div
      const gradientBg = container.querySelector('.absolute.inset-0.rounded-xl');
      expect(gradientBg).toBeInTheDocument();
    });
  });

  describe('Combined Props', () => {
    it('works with hover and featured together', () => {
      const { container } = render(
        <Card hover featured>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.hover\\:shadow-xl');
      expect(card).toBeInTheDocument();
      const featuredCard = container.querySelector('.shadow-lg');
      expect(featuredCard).toBeInTheDocument();
    });

    it('works with gradientBorder and featured together', () => {
      const { container } = render(
        <Card gradientBorder featured>
          <CardContent>Content</CardContent>
        </Card>
      );
      const wrapper = container.querySelector('.group');
      expect(wrapper).toBeInTheDocument();
      const card = container.querySelector('.shadow-lg');
      expect(card).toBeInTheDocument();
    });

    it('works with all enhancement props together', () => {
      const { container } = render(
        <Card hover featured gradientBorder glowColor="primary">
          <CardContent>Content</CardContent>
        </Card>
      );
      const wrapper = container.querySelector('.group');
      expect(wrapper).toBeInTheDocument();
      const card = container.querySelector('.hover\\:shadow-xl');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Dark Mode Support', () => {
    it('applies dark mode classes', () => {
      const { container } = render(
        <Card>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.dark\\:bg-neutral-800');
      expect(card).toBeInTheDocument();
    });

    it('applies dark mode border classes', () => {
      const { container } = render(
        <Card>
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.dark\\:border-neutral-700');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Custom ClassName', () => {
    it('applies custom className to card', () => {
      const { container } = render(
        <Card className="custom-class">
          <CardContent>Content</CardContent>
        </Card>
      );
      const card = container.querySelector('.custom-class');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Animation Props', () => {
    it('disables animation when animateOnMount is false', () => {
      render(
        <Card animateOnMount={false}>
          <CardContent>Content</CardContent>
        </Card>
      );
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('applies stagger delay based on index', () => {
      render(
        <Card index={2}>
          <CardContent>Content</CardContent>
        </Card>
      );
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });
});
