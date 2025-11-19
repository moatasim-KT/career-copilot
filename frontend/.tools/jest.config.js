const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/.tools/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  // Keep Jest focused on unit/integration tests; exclude E2E (Playwright)
  // and Vitest-based suites which have their own runners.
  testPathIgnorePatterns: [
    '/node_modules/',
    '/cypress/',
    '/.next/',
    '/tests/e2e/',
    '/tests/playwright/',
    '/src/__tests__/performance/',
    '/src/components/ui/__tests__/DarkMode.comprehensive.test.tsx',
    '/src/components/ui/__tests__/DarkMode.visual.test.tsx',
    '/src/components/ui/__tests__/Card2.visual-test.tsx',
    '/src/components/applications/__tests__/VirtualApplicationList.test.tsx',
    '/src/components/__tests__/Auth.test.tsx',
    '/src/components/__tests__/RegistrationForm.test.tsx',
    '/src/components/__tests__/LoginForm.test.tsx',
    '/src/components/__tests__/forms/RegistrationForm.test.tsx',
    '/src/components/__tests__/forms/LoginForm.test.tsx',
    '/src/components/ProfilePage.test.tsx',
    '/src/__tests__/optimisticUpdates.test.tsx',
    '/src/hooks/__tests__/useUser.test.ts',
    '/src/components/ui/__tests__/Modal2.test.tsx',
    '/src/components/ui/__tests__/Drawer2.test.tsx',
  ],
};

module.exports = createJestConfig(customJestConfig);
