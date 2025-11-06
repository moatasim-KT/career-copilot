# Coding Standards

Enterprise-grade coding standards for the Career Copilot frontend application.

## Table of Contents

- [General Principles](#general-principles)
- [TypeScript](#typescript)
- [React](#react)
- [Styling](#styling)
- [Testing](#testing)
- [File Organization](#file-organization)
- [Git Workflow](#git-workflow)
- [Documentation](#documentation)

## General Principles

### Code Quality
- **DRY (Don't Repeat Yourself)**: Extract reusable logic into functions/components
- **SOLID Principles**: Follow SOLID design principles
- **KISS (Keep It Simple)**: Prefer simple solutions over complex ones
- **YAGNI (You Aren't Gonna Need It)**: Don't implement features you don't need yet
- **Clean Code**: Write self-documenting code with meaningful names

### Performance
- **Lazy Loading**: Use dynamic imports for route-based code splitting
- **Memoization**: Use `useMemo`, `useCallback`, and `React.memo` appropriately
- **Virtual Scrolling**: Use virtual scrolling for large lists (>100 items)
- **Image Optimization**: Use Next.js Image component with proper sizing
- **Bundle Size**: Keep initial bundle <200KB gzipped

## TypeScript

### Type Safety
```typescript
// ✅ Good - Explicit types
interface User {
  id: string;
  name: string;
  email: string;
}

function getUser(id: string): Promise<User> {
  return fetch(`/api/users/${id}`).then(res => res.json());
}

// ❌ Bad - Implicit any
function getUser(id) {
  return fetch(`/api/users/${id}`).then(res => res.json());
}
```

### Interfaces vs Types
```typescript
// ✅ Use interfaces for objects that can be extended
interface BaseUser {
  id: string;
  name: string;
}

interface AdminUser extends BaseUser {
  permissions: string[];
}

// ✅ Use types for unions, primitives, and utility types
type Status = 'pending' | 'approved' | 'rejected';
type UserResponse = User | { error: string };
```

### Generics
```typescript
// ✅ Good - Reusable generic component
function useFetch<T>(url: string): {
  data: T | null;
  loading: boolean;
  error: Error | null;
} {
  // Implementation
}

// Usage
const { data } = useFetch<User>('/api/user');
```

### Utility Types
```typescript
// ✅ Use built-in utility types
type PartialUser = Partial<User>; // All properties optional
type ReadonlyUser = Readonly<User>; // All properties readonly
type UserKeys = keyof User; // 'id' | 'name' | 'email'
type UserName = Pick<User, 'name'>; // { name: string }
type UserWithoutId = Omit<User, 'id'>; // { name: string; email: string }
```

## React

### Component Structure
```typescript
/**
 * User Profile Component
 * 
 * Displays user information with edit capabilities.
 * 
 * @example
 * ```tsx
 * <UserProfile userId="123" onUpdate={handleUpdate} />
 * ```
 */
export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // 1. Hooks at the top
  const [user, setUser] = useState<User | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  // 2. Effects
  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);
  
  // 3. Event handlers
  const handleSave = useCallback(() => {
    if (user) {
      onUpdate(user);
      setIsEditing(false);
    }
  }, [user, onUpdate]);
  
  // 4. Render logic
  if (!user) return <Skeleton />;
  
  return (
    <div className="user-profile">
      {/* JSX */}
    </div>
  );
}
```

### Hooks Best Practices
```typescript
// ✅ Good - Dependencies array complete
useEffect(() => {
  fetchData(userId, filter);
}, [userId, filter]);

// ❌ Bad - Missing dependencies
useEffect(() => {
  fetchData(userId, filter);
}, [userId]); // ESLint will warn about missing 'filter'

// ✅ Good - Memoize callbacks
const handleClick = useCallback(() => {
  doSomething(value);
}, [value]);

// ✅ Good - Memoize expensive computations
const filteredData = useMemo(() => {
  return data.filter(item => item.status === 'active');
}, [data]);
```

### Component Patterns
```typescript
// ✅ Good - Compound components
export function Select({ children, value, onChange }: SelectProps) {
  return (
    <SelectContext.Provider value={{ value, onChange }}>
      {children}
    </SelectContext.Provider>
  );
}

Select.Option = SelectOption;
Select.Group = SelectGroup;

// Usage
<Select value={value} onChange={setValue}>
  <Select.Option value="1">Option 1</Select.Option>
  <Select.Option value="2">Option 2</Select.Option>
</Select>
```

### Error Boundaries
```typescript
// ✅ Always wrap features in error boundaries
import { ErrorBoundary } from '@sentry/nextjs';

<ErrorBoundary fallback={<ErrorFallback />}>
  <MyFeature />
</ErrorBoundary>
```

## Styling

### Tailwind CSS
```tsx
// ✅ Good - Semantic class ordering
<div className="flex items-center justify-between gap-4 rounded-lg bg-white p-6 shadow-md">
  {/* Layout → Spacing → Typography → Colors → Effects */}
</div>

// ✅ Good - Extract repeated patterns
const cardStyles = 'rounded-lg bg-white p-6 shadow-md';

// ✅ Good - Use design tokens
import { tokens } from '@/lib/designTokens';
<div style={{ color: tokens.colors.primary[600] }} />
```

### Responsive Design
```tsx
// ✅ Good - Mobile-first approach
<div className="flex flex-col gap-4 md:flex-row md:gap-6 lg:gap-8">
  {/* Content */}
</div>

// ✅ Good - Container queries (when needed)
<div className="@container">
  <div className="@lg:grid-cols-3">
    {/* Content */}
  </div>
</div>
```

## Testing

### Unit Tests
```typescript
// ✅ Good - AAA pattern (Arrange, Act, Assert)
describe('UserProfile', () => {
  it('should display user information', () => {
    // Arrange
    const user = { id: '1', name: 'John', email: 'john@example.com' };
    
    // Act
    render(<UserProfile user={user} />);
    
    // Assert
    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
```

### Integration Tests
```typescript
// ✅ Good - Test user flows
describe('Job Application Flow', () => {
  it('should allow user to submit application', async () => {
    const user = userEvent.setup();
    
    render(<JobApplicationForm />);
    
    await user.type(screen.getByLabelText('Company'), 'Acme Corp');
    await user.type(screen.getByLabelText('Position'), 'Engineer');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Application submitted')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests
```typescript
// ✅ Good - Test critical paths
test('user can complete job application', async ({ page }) => {
  await page.goto('/jobs/new');
  
  await page.fill('[name="company"]', 'Acme Corp');
  await page.fill('[name="position"]', 'Software Engineer');
  await page.click('button:has-text("Submit")');
  
  await expect(page.locator('text=Application submitted')).toBeVisible();
});
```

### Test Coverage
- Minimum 80% coverage for critical paths
- 100% coverage for utility functions
- Integration tests for user flows
- E2E tests for critical features

## File Organization

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth routes group
│   ├── (dashboard)/       # Dashboard routes group
│   └── api/               # API routes
├── components/            # React components
│   ├── common/           # Shared components
│   ├── features/         # Feature-specific components
│   └── layout/           # Layout components
├── hooks/                # Custom React hooks
├── lib/                  # Utility libraries
│   ├── api/             # API clients
│   ├── utils/           # Helper functions
│   └── constants/       # Constants
├── types/               # TypeScript type definitions
└── styles/              # Global styles
```

### Naming Conventions
- **Components**: PascalCase (`UserProfile.tsx`)
- **Hooks**: camelCase with 'use' prefix (`useUserData.ts`)
- **Utils**: camelCase (`formatDate.ts`)
- **Constants**: SCREAMING_SNAKE_CASE (`API_ENDPOINTS.ts`)
- **Types**: PascalCase (`UserTypes.ts`)

## Git Workflow

### Commit Messages
```bash
# ✅ Good - Conventional commits
feat(auth): add OAuth login support
fix(dashboard): resolve chart rendering issue
docs(readme): update installation steps
refactor(api): simplify error handling
test(jobs): add integration tests for job flow
perf(list): implement virtual scrolling

# ❌ Bad
update code
fix bug
wip
```

### Branch Naming
```bash
# ✅ Good
feature/oauth-login
fix/chart-rendering
refactor/error-handling
docs/api-documentation

# ❌ Bad
my-feature
updates
test
```

### Pull Requests
- Clear title and description
- Link related issues
- Include screenshots for UI changes
- Ensure CI passes
- Request reviews from relevant team members
- Keep PRs small (<500 lines when possible)

## Documentation

### JSDoc Comments
```typescript
/**
 * Fetches user data from the API
 * 
 * @param userId - The unique identifier of the user
 * @param options - Optional fetch configuration
 * @returns Promise resolving to user data
 * @throws {ApiError} When the API request fails
 * 
 * @example
 * ```ts
 * const user = await fetchUser('123');
 * console.log(user.name);
 * ```
 */
async function fetchUser(
  userId: string,
  options?: FetchOptions
): Promise<User> {
  // Implementation
}
```

### Component Documentation
```typescript
/**
 * User Profile Card
 * 
 * Displays user information in a card format with edit and delete actions.
 * 
 * @component
 * @example
 * ```tsx
 * <UserProfileCard
 *   user={user}
 *   onEdit={() => console.log('Edit')}
 *   onDelete={() => console.log('Delete')}
 * />
 * ```
 */
export function UserProfileCard(props: UserProfileCardProps) {
  // Implementation
}
```

### README Files
- Every major feature should have a README
- Include usage examples
- Document configuration options
- List dependencies
- Provide troubleshooting tips

## Code Review Checklist

- [ ] Code follows TypeScript best practices
- [ ] Components are properly typed
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No console.log statements
- [ ] Error handling is implemented
- [ ] Accessibility standards met (WCAG 2.1 AA)
- [ ] Performance considerations addressed
- [ ] Security best practices followed
- [ ] Code is self-documenting with clear names

## Performance Budgets

- **Initial Bundle**: <200KB gzipped
- **Route Chunks**: <100KB gzipped
- **Images**: <200KB, properly sized
- **Lighthouse Score**: >90
- **FCP**: <1.8s
- **LCP**: <2.5s
- **CLS**: <0.1
- **FID**: <100ms

## Security Guidelines

- Never commit secrets or API keys
- Sanitize user input
- Use parameterized queries (SQL injection prevention)
- Implement CSRF protection
- Set secure HTTP headers (CSP, HSTS)
- Validate data on both client and server
- Use HTTPS in production
- Implement rate limiting
- Regular dependency updates

## Accessibility Requirements

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus management
- Color contrast ratios (WCAG AA: 4.5:1)
- Screen reader testing
- Skip links for navigation
- Form validation accessible

---

**Last Updated**: 2025-11-06  
**Version**: 1.0.0  
**Maintainer**: Engineering Team
