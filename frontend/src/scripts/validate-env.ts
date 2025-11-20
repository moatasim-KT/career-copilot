// frontend/src/scripts/validate-env.ts

const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_WS_URL',
];

const defaults = {
  NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
  NEXT_PUBLIC_WS_URL: 'ws://localhost:8000/ws',
};

export function validateEnvironmentVariables() {
  if (typeof window !== 'undefined') {
    // Skip validation on client side
    return;
  }

  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      const defaultValue = defaults[envVar as keyof typeof defaults];
      console.warn(`⚠️  Warning: Environment variable ${envVar} is not set.`);
      console.warn(`   Using default value: ${defaultValue}`);
      // Set the default value
      process.env[envVar] = defaultValue;
    }
  }
  console.log('✅ Environment variables validated.');
}

// Call this function at the entry point of your application, e.g., in _app.tsx or layout.tsx

