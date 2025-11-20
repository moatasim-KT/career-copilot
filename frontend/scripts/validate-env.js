#!/usr/bin/env node

/**
 * Environment Variables Validation Script
 * Validates that required environment variables are set before starting the dev server
 */

const REQUIRED_ENV_VARS = [
    // Add any required env vars here if needed
    // For now, we'll just do a basic check
];

const OPTIONAL_ENV_VARS = [
    'NEXT_PUBLIC_API_URL',
    'NEXT_PUBLIC_APP_URL',
];

function validateEnv() {
    const missingRequired = REQUIRED_ENV_VARS.filter(
        (varName) => !process.env[varName]
    );

    if (missingRequired.length > 0) {
        console.error('\n❌ Missing required environment variables:');
        missingRequired.forEach((varName) => {
            console.error(`   - ${varName}`);
        });
        console.error('\nPlease set these variables in your .env.local file\n');
        process.exit(1);
    }

    const missingOptional = OPTIONAL_ENV_VARS.filter(
        (varName) => !process.env[varName]
    );

    if (missingOptional.length > 0) {
        console.warn('\n⚠️  Optional environment variables not set:');
        missingOptional.forEach((varName) => {
            console.warn(`   - ${varName}`);
        });
        console.warn('   Using default values...\n');
    }

    console.log('✅ Environment validation passed\n');
}

validateEnv();
