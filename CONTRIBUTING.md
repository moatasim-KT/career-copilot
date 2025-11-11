# Contributing to Career Copilot

Thank you for your interest in contributing to Career Copilot! We welcome contributions from the community, whether you're fixing bugs, adding features, improving documentation, or reporting issues.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [AI Agent Contributors](#ai-agent-contributors)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:
- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/moatasim-KT/career-copilot/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details (OS, browser, versions)

### Suggesting Features

1. Check if the feature has been suggested in [Issues](https://github.com/moatasim-KT/career-copilot/issues)
2. If not, create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach
   - Any relevant examples or mockups

### Contributing Code

1. **Fork the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/career-copilot.git
   cd career-copilot
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   # or
   git checkout -b fix/bug-description
   ```

3. **Make Your Changes**
   - Write clean, documented code
   - Follow the code style guidelines below
   - Add tests for new features
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests
   cd frontend && npm test
   
   # Linting
   npm run lint
   
   # Type checking
   npm run type-check
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/amazing-feature
   ```

## Development Setup

### Prerequisites

- Docker & Docker Compose (recommended)
- OR:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 14+
  - Redis 7+

### Quick Start

```bash
# Clone repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Start with Docker
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Code Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guide
- Use `ruff` for linting: `ruff check .`
- Use type hints for function parameters and returns
- Maximum line length: 100 characters
- Use docstrings for classes and functions

**Example:**
```python
from typing import Optional
from app.models import Application
from app.schemas import ApplicationStatus

def process_application(
    application_id: int,
    status: ApplicationStatus,
    notes: Optional[str] = None
) -> Application:
    """
    Update application status and send notifications.
    
    Args:
        application_id: The application ID
        status: New status to set
        notes: Optional notes about the status change
        
    Returns:
        Updated application object
        
    Raises:
        ValueError: If application_id is invalid
        NotFoundError: If application doesn't exist
    """
    # Implementation
    pass
```

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `ApplicationService`)
- Functions/methods: `snake_case` (e.g., `get_user_applications`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private methods: `_leading_underscore` (e.g., `_validate_data`)

### TypeScript/React (Frontend)

- Follow project ESLint configuration
- Use TypeScript for all new code
- Use functional components with hooks
- Use proper prop typing with interfaces
- Maximum line length: 100 characters

**Example:**
```typescript
import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function Button({ 
  variant = 'primary', 
  size = 'md',
  disabled = false,
  onClick, 
  children,
  className
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-lg font-medium transition-colors',
        variant === 'primary' && 'bg-primary text-white hover:bg-primary-600',
        variant === 'secondary' && 'bg-secondary text-white hover:bg-secondary-600',
        size === 'sm' && 'px-3 py-1.5 text-sm',
        size === 'md' && 'px-4 py-2 text-base',
        size === 'lg' && 'px-6 py-3 text-lg',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

**Naming Conventions:**
- Components: `PascalCase` (e.g., `Button`, `JobCard`)
- Hooks: `camelCase` with "use" prefix (e.g., `useAuth`, `useJobs`)
- Utilities: `camelCase` (e.g., `formatDate`, `validateEmail`)
- Types/Interfaces: `PascalCase` (e.g., `User`, `JobListing`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_URL`, `MAX_RETRIES`)

**Import Order:**
```typescript
// 1. React & Next.js
import React from 'react';
import { useRouter } from 'next/navigation';

// 2. External libraries
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';

// 3. Internal components
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 4. Hooks & utilities
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

// 5. Types
import type { User } from '@/types';

// 6. Styles (if any)
import styles from './Component.module.css';
```

### Design System

- Use design tokens from `frontend/src/app/globals.css`
- Follow Button2/Card2 component patterns
- Ensure WCAG 2.1 AA accessibility compliance
- Test in both light and dark modes
- Use semantic HTML elements
- Add proper ARIA labels and roles

### Git Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config, etc.)
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```bash
feat(auth): add two-factor authentication

fix(api): resolve race condition in job scraping

docs(readme): update installation instructions

refactor(components): extract common button logic

test(applications): add unit tests for status updates
```

## Testing Requirements

### Backend Tests

- Maintain >80% test coverage
- Write unit tests for business logic
- Write integration tests for API endpoints
- Use pytest fixtures for common setup

```python
# tests/test_applications.py
import pytest
from app.services import ApplicationService

def test_create_application(db_session, test_user):
    """Test creating a new application."""
    service = ApplicationService(db_session)
    application = service.create_application(
        user_id=test_user.id,
        job_id=1,
        status="applied"
    )
    assert application.id is not None
    assert application.status == "applied"
```

### Frontend Tests

- Test critical user flows
- Write component tests with React Testing Library
- Write E2E tests with Playwright for main workflows
- Test accessibility with axe-core

```typescript
// components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });
});
```

### Running Tests

```bash
# Backend
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov              # With coverage
pytest tests/test_api.py  # Specific file

# Frontend
cd frontend
npm test                  # Run all tests
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage
npm run test:e2e          # E2E tests
```

## Pull Request Process

1. **Before Submitting**
   - Ensure all tests pass
   - Run linting and fix any issues
   - Update documentation if needed
   - Add/update tests for your changes
   - Rebase on latest main branch

2. **PR Description**
   Include:
   - Clear description of changes
   - Link to related issues (e.g., "Fixes #123")
   - Screenshots for UI changes
   - Breaking changes (if any)
   - Migration notes (if needed)

3. **Review Process**
   - At least one approval required
   - All CI/CD checks must pass
   - Address reviewer feedback
   - Keep PR focused and reasonably sized

4. **After Approval**
   - Squash commits if requested
   - Maintainer will merge the PR
   - Delete your feature branch

### PR Template

```markdown
## Description
Brief description of changes

## Related Issues
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
```

## AI Agent Contributors

For AI agents working on this project:

1. **Read Documentation**
   - [.agents/START_HERE.md](.agents/START_HERE.md) - Quick start guide
   - [.agents/coordination-rules.md](.agents/coordination-rules.md) - Coordination rules
   - [.agents/task-partition-plan.md](.agents/task-partition-plan.md) - Task assignments

2. **Check Task Assignments**
   - Review [.agents/task-assignments.json](.agents/task-assignments.json)
   - Ensure your assigned tasks are clear
   - Avoid working on tasks assigned to other agents

3. **Follow Agent-Specific Instructions**
   - Gemini agents: See `.agents/gemini/`
   - Copilot agents: See `.agents/copilot/`

4. **Use Designated Branches**
   - Gemini: `agent/gemini/*`
   - Copilot: `agent/copilot/*`

5. **Run Sync Checks**
   ```bash
   .agents/shared/sync-check.sh
   ```

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/moatasim-KT/career-copilot/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/moatasim-KT/career-copilot/issues)
- **Security**: Email moatasimfarooque@gmail.com
- **Documentation**: Check [docs/](docs/) directory

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Career Copilot! 🚀
