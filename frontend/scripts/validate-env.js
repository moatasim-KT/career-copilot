#!/usr/bin/env node

/**
 * Environment Variable Validation Script
 *
 * Validates that all required environment variables are present before starting the application.
 * This script should be run during build time or application startup to catch configuration
 * issues early.
 *
 * Usage:
 *   node scripts/validate-env.js
 *   npm run validate-env
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for console output
const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m',
    bold: '\x1b[1m',
};

// Required environment variables with descriptions
const REQUIRED_VARS = {
    // API Configuration
    NEXT_PUBLIC_API_URL: 'Base URL of the backend API (e.g., http://localhost:8000)',

    // WebSocket Configuration
    NEXT_PUBLIC_WS_URL: 'WebSocket URL for real-time connections (e.g., ws://localhost:8000)',
};

// Optional but recommended environment variables
const RECOMMENDED_VARS = {
    NEXT_PUBLIC_ENV: 'Application environment (development/staging/production)',
    NEXT_PUBLIC_DEBUG: 'Enable debug logging (true/false)',
    NEXT_PUBLIC_ENABLE_WEBSOCKET: 'Enable WebSocket connections (true/false)',
    NEXT_PUBLIC_ENABLE_ANALYTICS: 'Enable analytics tracking (true/false)',
};

// Environment variables that should NOT be logged (contain sensitive data)
const SENSITIVE_VARS = [
    'SENTRY_AUTH_TOKEN',
    // Add other sensitive variables here as needed
];

/**
 * Check if a variable is sensitive and should not be logged
 */
function isSensitiveVar(varName) {
    return SENSITIVE_VARS.includes(varName);
}

/**
 * Get the value of an environment variable, checking both process.env and .env files
 */
function getEnvVar(name) {
    // First check process.env (runtime environment)
    if (process.env[name]) {
        return process.env[name];
    }

    // Then check .env.local file (development overrides)
    try {
        const envLocalPath = path.join(process.cwd(), '.env.local');
        if (fs.existsSync(envLocalPath)) {
            const envContent = fs.readFileSync(envLocalPath, 'utf8');
            const lines = envContent.split('\n');
            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed && !trimmed.startsWith('#')) {
                    const [key, ...valueParts] = trimmed.split('=');
                    if (key === name) {
                        return valueParts.join('=');
                    }
                }
            }
        }
    } catch {
        // Ignore file read errors
    }

    // Finally check .env file
    try {
        const envPath = path.join(process.cwd(), '.env');
        if (fs.existsSync(envPath)) {
            const envContent = fs.readFileSync(envPath, 'utf8');
            const lines = envContent.split('\n');
            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed && !trimmed.startsWith('#')) {
                    const [key, ...valueParts] = trimmed.split('=');
                    if (key === name) {
                        return valueParts.join('=');
                    }
                }
            }
        }
    } catch {
        // Ignore file read errors
    }

    return undefined;
}

/**
 * Validate that all required environment variables are present
 */
function validateEnvironment() {
    console.log(`${colors.blue}${colors.bold}🔍 Validating Environment Variables${colors.reset}\n`);

    let hasErrors = false;
    let hasWarnings = false;

    // Check required variables
    console.log(`${colors.bold}Required Variables:${colors.reset}`);
    for (const [varName, description] of Object.entries(REQUIRED_VARS)) {
        const value = getEnvVar(varName);

        if (!value || value.trim() === '') {
            console.log(`  ${colors.red}❌ ${varName}${colors.reset}`);
            console.log(`     ${description}`);
            console.log(`     ${colors.red}ERROR: This variable is required but not set${colors.reset}`);
            hasErrors = true;
        } else {
            const displayValue = isSensitiveVar(varName) ? '[HIDDEN]' : value;
            console.log(`  ${colors.green}✅ ${varName}${colors.reset} = ${displayValue}`);
        }
    }

    console.log();

    // Check recommended variables
    console.log(`${colors.bold}Recommended Variables:${colors.reset}`);
    for (const [varName, description] of Object.entries(RECOMMENDED_VARS)) {
        const value = getEnvVar(varName);

        if (!value || value.trim() === '') {
            console.log(`  ${colors.yellow}⚠️  ${varName}${colors.reset}`);
            console.log(`     ${description}`);
            console.log(`     ${colors.yellow}WARNING: This variable is not set (optional but recommended)${colors.reset}`);
            hasWarnings = true;
        } else {
            const displayValue = isSensitiveVar(varName) ? '[HIDDEN]' : value;
            console.log(`  ${colors.green}✅ ${varName}${colors.reset} = ${displayValue}`);
        }
    }

    console.log();

    // Summary
    if (hasErrors) {
        console.log(`${colors.red}${colors.bold}❌ Validation Failed${colors.reset}`);
        console.log(`${colors.red}Missing required environment variables. Please check your .env.local or .env file.${colors.reset}`);
        console.log(`${colors.blue}See frontend/.env.example for configuration details.${colors.reset}`);
        process.exit(1);
    } else if (hasWarnings) {
        console.log(`${colors.yellow}${colors.bold}⚠️  Validation Passed with Warnings${colors.reset}`);
        console.log(`${colors.yellow}Some recommended variables are not set. The application will still work but may have limited functionality.${colors.reset}`);
        process.exit(0);
    } else {
        console.log(`${colors.green}${colors.bold}✅ Validation Passed${colors.reset}`);
        console.log(`${colors.green}All required environment variables are properly configured.${colors.reset}`);
        process.exit(0);
    }
}

// Additional validation for specific variables
function validateSpecificVars() {
    const issues = [];

    // Validate NEXT_PUBLIC_API_URL format
    const apiUrl = getEnvVar('NEXT_PUBLIC_API_URL');
    if (apiUrl) {
        try {
            const url = new URL(apiUrl);
            if (!['http:', 'https:'].includes(url.protocol)) {
                issues.push({
                    var: 'NEXT_PUBLIC_API_URL',
                    message: 'Must use http:// or https:// protocol',
                });
            }
        } catch {
            issues.push({
                var: 'NEXT_PUBLIC_API_URL',
                message: 'Must be a valid URL',
            });
        }
    }

    // Validate NEXT_PUBLIC_WS_URL format
    const wsUrl = getEnvVar('NEXT_PUBLIC_WS_URL');
    if (wsUrl) {
        try {
            const url = new URL(wsUrl);
            if (!['ws:', 'wss:'].includes(url.protocol)) {
                issues.push({
                    var: 'NEXT_PUBLIC_WS_URL',
                    message: 'Must use ws:// or wss:// protocol',
                });
            }
        } catch {
            issues.push({
                var: 'NEXT_PUBLIC_WS_URL',
                message: 'Must be a valid URL',
            });
        }
    }

    // Validate NEXT_PUBLIC_ENV values
    const env = getEnvVar('NEXT_PUBLIC_ENV');
    if (env && !['development', 'staging', 'production'].includes(env)) {
        issues.push({
            var: 'NEXT_PUBLIC_ENV',
            message: 'Must be one of: development, staging, production',
        });
    }

    // Validate boolean values
    const booleanVars = ['NEXT_PUBLIC_DEBUG', 'NEXT_PUBLIC_ENABLE_WEBSOCKET', 'NEXT_PUBLIC_ENABLE_ANALYTICS'];
    for (const varName of booleanVars) {
        const value = getEnvVar(varName);
        if (value && !['true', 'false'].includes(value.toLowerCase())) {
            issues.push({
                var: varName,
                message: 'Must be true or false',
            });
        }
    }

    return issues;
}

// Run validation
try {
    validateEnvironment();

    // Additional specific validations
    const specificIssues = validateSpecificVars();
    if (specificIssues.length > 0) {
        console.log(`\n${colors.bold}Additional Validation Issues:${colors.reset}`);
        for (const issue of specificIssues) {
            console.log(`  ${colors.red}❌ ${issue.var}${colors.reset}: ${issue.message}`);
        }
        console.log();
        console.log(`${colors.red}${colors.bold}❌ Validation Failed${colors.reset}`);
        console.log(`${colors.red}Please fix the configuration issues above.${colors.reset}`);
        process.exit(1);
    }
} catch (error) {
    console.error(`${colors.red}${colors.bold}❌ Validation Error${colors.reset}`);
    console.error(`${colors.red}${error.message}${colors.reset}`);
    process.exit(1);
}