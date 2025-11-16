// ESLint configuration for Career Copilot frontend

import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import importPlugin from 'eslint-plugin-import';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

const eslintConfig = [// Base JavaScript configuration
    // Configuration for TypeScript files
    js.configs.recommended, // Configuration for JavaScript files
    // Test files override: keep test linting lightweight (no typed-parser project)
    {
        files: ['**/*.test.{js,jsx,ts,tsx}', '**/*.spec.{js,jsx,ts,tsx}'],
        languageOptions: {
            parser: typescriptParser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
                ecmaFeatures: { jsx: true },
            },
            globals: {
                ...globals.browser,
                ...globals.jest,
                ...globals.node,
            },
        },
    },
    {
        files: ['src/**/*.{ts,tsx}'],
        languageOptions: {
            parser: typescriptParser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
                ecmaFeatures: {
                    jsx: true,
                },
            },
            globals: {
                ...globals.browser,
                ...globals.node,
                React: 'readonly',
                JSX: 'readonly',
                NodeJS: 'readonly',
            },
        },
        plugins: {
            '@typescript-eslint': typescript,
            react: react,
            'react-hooks': reactHooks,
            'jsx-a11y': jsxA11y,
            import: importPlugin,
        },
        rules: {
            // TypeScript rules
            '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' }],
            '@typescript-eslint/no-explicit-any': 'off', // RELAXED: Allow any type
            '@typescript-eslint/explicit-function-return-type': 'off',
            '@typescript-eslint/explicit-module-boundary-types': 'off',
            '@typescript-eslint/no-non-null-assertion': 'warn',
            '@typescript-eslint/prefer-as-const': 'error',
            '@typescript-eslint/no-var-requires': 'error',

            // React rules
            'react/react-in-jsx-scope': 'off', // Not needed in Next.js
            'react/prop-types': 'off', // Using TypeScript for prop validation
            'react/jsx-uses-react': 'off', // Not needed in Next.js
            'react/jsx-uses-vars': 'error',
            'react/jsx-key': 'error',
            'react/jsx-no-duplicate-props': 'error',
            'react/jsx-no-undef': 'error',
            'react/no-children-prop': 'error',
            'react/no-danger-with-children': 'error',
            'react/no-deprecated': 'error',
            'react/no-direct-mutation-state': 'error',
            'react/no-find-dom-node': 'error',
            'react/no-is-mounted': 'error',
            'react/no-render-return-value': 'error',
            'react/no-string-refs': 'error',
            'react/no-unescaped-entities': 'warn', // RELAXED: Changed to warn
            'react/no-unknown-property': 'error',
            'react/require-render-return': 'error',

            // React Hooks rules
            'react-hooks/rules-of-hooks': 'error',
            'react-hooks/exhaustive-deps': 'warn',

            // Accessibility rules - RELAXED
            'jsx-a11y/alt-text': 'warn',
            'jsx-a11y/anchor-has-content': 'warn',
            'jsx-a11y/anchor-is-valid': 'warn',
            'jsx-a11y/aria-props': 'warn',
            'jsx-a11y/aria-proptypes': 'warn',
            'jsx-a11y/aria-unsupported-elements': 'warn',
            'jsx-a11y/click-events-have-key-events': 'off', // RELAXED: Turned off
            'jsx-a11y/heading-has-content': 'warn',
            'jsx-a11y/img-redundant-alt': 'warn',
            'jsx-a11y/no-access-key': 'warn',

            // Import rules
            'import/order': [
                'warn', // RELAXED: Changed to warn
                {
                    groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
                    'newlines-between': 'always',
                    alphabetize: {
                        order: 'asc',
                        caseInsensitive: true,
                    },
                },
            ],
            'import/no-duplicates': 'warn',
            'import/no-unresolved': 'off', // Handled by TypeScript
            'import/named': 'off', // Handled by TypeScript

            // General rules
            'no-console': 'off', // RELAXED: Allow console statements
            'no-debugger': 'warn', // RELAXED: Changed to warn
            'no-alert': 'off', // RELAXED: Allow alerts
            'no-unused-vars': 'off', // Using @typescript-eslint/no-unused-vars instead
            'no-undef': 'off', // TypeScript handles undefined symbols via type checking
            'no-var': 'error',
            'object-shorthand': 'error',
            'prefer-arrow-callback': 'error',
            'prefer-template': 'error',
            'template-curly-spacing': ['error', 'never'],
            'arrow-spacing': 'error',
            'comma-dangle': ['error', 'always-multiline'],
            semi: ['error', 'always'],
            quotes: ['error', 'single', { avoidEscape: true }],
            'jsx-quotes': ['error', 'prefer-double'],

            // Complexity rules - GREATLY RELAXED for real-world React components
            complexity: 'off', // RELAXED: Turned off
            'max-depth': 'off', // RELAXED: Turned off
            'max-lines': 'off', // RELAXED: Turned off
            'max-lines-per-function': 'off', // RELAXED: Turned off
            'max-params': 'off', // RELAXED: Turned off
        },
        settings: {
            react: {
                version: 'detect',
            },
            'import/resolver': {
                typescript: {
                    alwaysTryTypes: true,
                },
                node: {
                    extensions: ['.js', '.jsx', '.ts', '.tsx'],
                    moduleDirectory: ['node_modules', 'src/'],
                },
            },
        },
    }, // Configuration for Cypress test files
    {
        files: ['**/*.{js,jsx}'],
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            parserOptions: {
                ecmaFeatures: {
                    jsx: true,
                },
            },
            globals: {
                ...globals.browser,
                ...globals.node,
                React: 'readonly',
                JSX: 'readonly',
                NodeJS: 'readonly',
            },
        },
        plugins: {
            react: react,
            'react-hooks': reactHooks,
            'jsx-a11y': jsxA11y,
            import: importPlugin,
        },
        rules: {
            // JavaScript rules
            'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],

            // React rules (same as TypeScript)
            'react/react-in-jsx-scope': 'off',
            'react/prop-types': 'off',
            'react/jsx-uses-react': 'off',
            'react/jsx-uses-vars': 'error',
            'react/jsx-key': 'error',
            'react/jsx-no-duplicate-props': 'error',
            'react/jsx-no-undef': 'error',
            'react/no-children-prop': 'error',
            'react/no-danger-with-children': 'error',
            'react/no-deprecated': 'error',
            'react/no-direct-mutation-state': 'error',
            'react/no-find-dom-node': 'error',
            'react/no-is-mounted': 'error',
            'react/no-render-return-value': 'error',
            'react/no-string-refs': 'error',
            'react/no-unescaped-entities': 'warn',
            'react/no-unknown-property': 'error',
            'react/require-render-return': 'error',

            // React Hooks rules
            'react-hooks/rules-of-hooks': 'error',
            'react-hooks/exhaustive-deps': 'warn',

            // Accessibility rules - RELAXED
            'jsx-a11y/click-events-have-key-events': 'off',

            // General rules - RELAXED
            'no-console': 'off',
            'no-debugger': 'warn',
            'no-alert': 'off',

            // Complexity rules - RELAXED
            complexity: 'off',
            'max-depth': 'off',
            'max-lines': 'off',
            'max-lines-per-function': 'off',
            'max-params': 'off',
        },
        settings: {
            react: {
                version: 'detect',
            },
        },
    }, // Configuration for Jest test files
    {
        files: ['cypress/**/*.{js,jsx,ts,tsx}'],
        languageOptions: {
            globals: {
                ...globals.browser,
                cy: 'readonly',
                Cypress: 'readonly',
                describe: 'readonly',
                it: 'readonly',
                before: 'readonly',
                beforeEach: 'readonly',
                after: 'readonly',
                afterEach: 'readonly',
                expect: 'readonly',
                assert: 'readonly',
            },
        },
    }, // Ignore patterns
    {
        files: ['**/*.test.{js,jsx,ts,tsx}', '**/*.spec.{js,jsx,ts,tsx}'],
        languageOptions: {
            // For test files we avoid using the typed parser project to prevent
            // 'file not found in project' errors when ESLint runs on isolated files.
            // Tests still get Jest globals via globals.jest.
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
                ecmaFeatures: { jsx: true },
            },
            globals: {
                ...globals.jest,
            },
        },
    }, {
        ignores: [
            '.next/**',
            'out/**',
            'build/**',
            'dist/**',
            'node_modules/**',
            '*.config.js',
            '*.config.mjs',
            'next-env.d.ts',
            'coverage/**',
            '.nyc_output/**',
            '**/*.stories.tsx',
            '**/*.stories.ts',
            '.storybook/**',
            '**/__tests__/**',
            '.venv/**',
        ],
    }];

export default eslintConfig;
