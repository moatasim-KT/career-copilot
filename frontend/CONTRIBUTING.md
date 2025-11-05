# Contributing to Career Copilot Frontend

Thank you for your interest in contributing to the Career Copilot frontend! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Component Development](#component-development)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Design System](#design-system)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Git
- Basic understanding of React, Next.js, and TypeScript

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/career-copilot.git
   cd career-copilot/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

4. **Run Storybook (for component development)**
   ```bash
   npm run storybook
   ```

## Coding Standards

### TypeScript

- Use TypeScript for all new code
- Define proper types/interfaces for all props and functions
- Avoid using `any` type unless absolutely necessary
- Use meaningful variable and function names

### Code Style

We use ESLint and Prettier for code formatting:

```bash
# Check code style
npm run lint:check
npm run format:check

# Auto-fix issues
npm run lint
npm run format
```

Run quality checks before committing:
```bash
npm run quality:check
```

### File Organization

```
src/
├── app/              # Next.js app directory (routes)
├── components/       # React components
│   ├── ui/          # Reusable UI components
│   ├── features/    # Feature-specific components
│   ├── forms/       # Form components
│   ├── layout/      # Layout components
│   └── pages/       # Page components
├── lib/             # Utility functions and helpers
├── hooks/           # Custom React hooks
└── types/           # TypeScript type definitions
```

### Naming Conventions

- **Components**: PascalCase (e.g., `Button.tsx`, `UserProfile.tsx`)
- **Utilities**: camelCase (e.g., `formatDate.ts`, `apiClient.ts`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)
- **Types/Interfaces**: PascalCase (e.g., `UserData`, `ApiResponse`)

## Component Development

### Creating a New Component

1. **Create the component file** in the appropriate directory
2. **Define TypeScript interfaces** for props
3. **Add JSDoc comments** for documentation
4. **Create a Storybook story** in a `.stories.tsx` file
5. **Write tests** for the component

Example component structure:

```tsx
'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * Props for the MyComponent component
 */
interface MyComponentProps {
  /** The content to display */
  children: ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * MyComponent description
 * 
 * @component
 * @example
 * ```tsx
 * <MyComponent className="custom-class">
 *   Content
 * </MyComponent>
 * ```
 */
export default function MyComponent({ 
  children, 
  className 
}: MyComponentProps) {
  return (
    <div className={cn('base-classes', className)}>
      {children}
    </div>
  );
}
```

### Component Guidelines

- **Keep components small and focused** - Each component should have a single responsibility
- **Use composition** - Build complex UIs from simple, reusable components
- **Make components reusable** - Avoid hardcoding values, use props instead
- **Follow the design system** - Use defined colors, spacing, and typography
- **Handle loading and error states** - Provide feedback for async operations
- **Make components accessible** - Use semantic HTML and ARIA attributes

### Styling

- Use Tailwind CSS for styling
- Follow the design system defined in `DESIGN_SYSTEM.md`
- Use the `cn()` utility for conditional classes
- Avoid inline styles unless absolutely necessary

```tsx
// Good
<div className={cn('base-class', isActive && 'active-class', className)} />

// Avoid
<div style={{ color: 'red' }} />
```

### Animations

We use Framer Motion for animations:

```tsx
import { motion } from 'framer-motion';
import { fadeInUp } from '@/lib/animations';

<motion.div
  initial="hidden"
  animate="visible"
  variants={fadeInUp}
>
  Content
</motion.div>
```

Available animation variants are in `src/lib/animations.ts`.

## Testing

### Unit Tests

Write unit tests for all components and utilities using Jest and React Testing Library:

```bash
npm test
npm run test:watch
npm run test:coverage
```

Example test:

```tsx
import { render, screen } from '@testing-library/react';
import Button from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('applies variant classes', () => {
    render(<Button variant="primary">Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600');
  });
});
```

### Test Coverage

- Aim for at least 80% code coverage
- Test all component variants and states
- Test error handling and edge cases
- Test accessibility features

## Pull Request Process

### Before Submitting

1. **Run all quality checks**
   ```bash
   npm run quality:check
   npm test
   ```

2. **Update documentation** if you've made changes to:
   - Component APIs
   - Configuration
   - Build process

3. **Test your changes** thoroughly in the browser

4. **Check bundle size** if you've added new dependencies
   ```bash
   npm run analyze
   ```

### PR Guidelines

1. **Create a descriptive PR title**
   - Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, etc.
   - Example: `feat: add loading state to Button component`

2. **Write a clear description**
   - What changes were made?
   - Why were they made?
   - How to test the changes?
   - Screenshots (for UI changes)

3. **Keep PRs focused**
   - One feature or fix per PR
   - Split large changes into smaller PRs

4. **Request reviews**
   - Tag appropriate reviewers
   - Address review comments promptly

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(button): add loading state
fix(card): resolve hover animation issue
docs(readme): update setup instructions
```

## Design System

Follow the design system guidelines in `DESIGN_SYSTEM.md`:

- Use CSS variables for colors
- Follow spacing scale (4px increments)
- Use defined typography sizes
- Ensure accessibility (WCAG 2.1 AA)
- Support dark mode

### Storybook

View and develop components in isolation:

```bash
npm run storybook
```

All UI components should have corresponding stories that demonstrate:
- All variants
- Different states (loading, disabled, error)
- Interactive examples
- Accessibility features

## Performance Considerations

- Use `dynamic` imports for code splitting
- Optimize images with `next/image`
- Minimize bundle size
- Use `memo` for expensive computations
- Implement proper loading states

## Accessibility

All components must be accessible:

- Use semantic HTML elements
- Add appropriate ARIA attributes
- Ensure keyboard navigation works
- Maintain proper color contrast
- Test with screen readers
- Support reduced motion preferences

```tsx
// Good
<button aria-label="Close modal" onClick={onClose}>
  <X className="h-5 w-5" />
</button>

// Check Storybook's a11y addon for violations
```

## Questions or Need Help?

- Check existing documentation
- Browse Storybook for component examples
- Ask in pull request comments
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to Career Copilot! 🚀
