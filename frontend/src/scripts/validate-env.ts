// frontend/src/scripts/validate-env.ts

const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_WS_URL',
];

export function validateEnvironmentVariables() {
  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      console.error(`Error: Environment variable ${envVar} is not set.`);
      process.exit(1);
    }
  }
  console.log('All required environment variables are set.');
}

// Call this function at the entry point of your application, e.g., in _app.tsx or layout.tsx
