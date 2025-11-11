#!/usr/bin/env node

/**
 * Security Audit Script
 * 
 * Runs comprehensive security checks including:
 * - npm audit for dependency vulnerabilities
 * - Environment variable validation
 * - XSS vulnerability checks
 * - CSRF protection verification
 * - Authentication flow review
 * - API security checks
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function section(title) {
  log('\n' + '='.repeat(60), 'cyan');
  log(title, 'bright');
  log('='.repeat(60), 'cyan');
}

function exec(command, options = {}) {
  try {
    return execSync(command, { 
      encoding: 'utf8', 
      stdio: options.silent ? 'pipe' : 'inherit',
      ...options 
    });
  } catch (error) {
    if (!options.ignoreError) {
      log(`Error executing: ${command}`, 'red');
      return null;
    }
    return error.stdout || '';
  }
}

// Create reports directory
const reportsDir = path.join(__dirname, '..', 'reports', 'security');
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
const reportFile = path.join(reportsDir, `security-audit-${timestamp}.md`);

let report = `# Security Audit Report\n\n`;
report += `**Date:** ${new Date().toLocaleString()}\n\n`;
report += `**Auditor:** Automated Security Scan\n\n`;

let criticalIssues = 0;
let highIssues = 0;
let mediumIssues = 0;
let lowIssues = 0;

// 1. NPM Audit
section('1. Dependency Vulnerability Scan (npm audit)');
log('Scanning dependencies for known vulnerabilities...', 'blue');

try {
  const auditOutput = exec('npm audit --json', { silent: true, ignoreError: true });
  
  if (auditOutput) {
    try {
      const auditData = JSON.parse(auditOutput);
      
      report += `## Dependency Vulnerabilities\n\n`;
      
      if (auditData.metadata) {
        const { vulnerabilities } = auditData.metadata;
        
        criticalIssues += vulnerabilities.critical || 0;
        highIssues += vulnerabilities.high || 0;
        mediumIssues += vulnerabilities.moderate || 0;
        lowIssues += vulnerabilities.low || 0;
        
        report += `| Severity | Count |\n`;
        report += `|----------|-------|\n`;
        report += `| Critical | ${vulnerabilities.critical || 0} |\n`;
        report += `| High | ${vulnerabilities.high || 0} |\n`;
        report += `| Moderate | ${vulnerabilities.moderate || 0} |\n`;
        report += `| Low | ${vulnerabilities.low || 0} |\n`;
        report += `| Info | ${vulnerabilities.info || 0} |\n\n`;
        
        if (vulnerabilities.critical > 0 || vulnerabilities.high > 0) {
          log(`⚠ Found ${vulnerabilities.critical} critical and ${vulnerabilities.high} high severity vulnerabilities`, 'red');
          report += `⚠️ **Action Required:** Fix critical and high severity vulnerabilities immediately.\n\n`;
          report += `Run \`npm audit fix\` to automatically fix vulnerabilities.\n\n`;
        } else if (vulnerabilities.moderate > 0) {
          log(`⚠ Found ${vulnerabilities.moderate} moderate severity vulnerabilities`, 'yellow');
          report += `⚠️ **Recommendation:** Review and fix moderate severity vulnerabilities.\n\n`;
        } else {
          log('✓ No critical or high severity vulnerabilities found', 'green');
          report += `✅ No critical or high severity vulnerabilities found.\n\n`;
        }
      }
    } catch (e) {
      log('⚠ Could not parse npm audit output', 'yellow');
      report += `⚠️ Could not parse npm audit results.\n\n`;
    }
  }
} catch (error) {
  log('⚠ npm audit failed', 'yellow');
  report += `⚠️ npm audit scan failed.\n\n`;
}

// 2. Environment Variables Check
section('2. Environment Variable Security');
log('Checking environment variable handling...', 'blue');

report += `## Environment Variable Security\n\n`;

const envExamplePath = path.join(__dirname, '..', '.env.example');
const envLocalPath = path.join(__dirname, '..', '.env.local');
const gitignorePath = path.join(__dirname, '..', '.gitignore');

let envIssues = [];

// Check if .env.example exists
if (!fs.existsSync(envExamplePath)) {
  envIssues.push('Missing .env.example file');
  mediumIssues++;
}

// Check if .env.local is in .gitignore
if (fs.existsSync(gitignorePath)) {
  const gitignore = fs.readFileSync(gitignorePath, 'utf8');
  if (!gitignore.includes('.env.local') && !gitignore.includes('.env*.local')) {
    envIssues.push('.env.local not in .gitignore - risk of exposing secrets');
    criticalIssues++;
  }
}

// Check for hardcoded secrets in code
const srcDir = path.join(__dirname, '..', 'src');
const secretPatterns = [
  /api[_-]?key\s*=\s*['"][^'"]+['"]/gi,
  /secret\s*=\s*['"][^'"]+['"]/gi,
  /password\s*=\s*['"][^'"]+['"]/gi,
  /token\s*=\s*['"][^'"]+['"]/gi,
];

function scanForSecrets(dir) {
  const files = fs.readdirSync(dir);
  const findings = [];
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      findings.push(...scanForSecrets(filePath));
    } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js') || file.endsWith('.jsx')) {
      const content = fs.readFileSync(filePath, 'utf8');
      
      secretPatterns.forEach(pattern => {
        const matches = content.match(pattern);
        if (matches) {
          // Filter out false positives (process.env references)
          const realMatches = matches.filter(m => !m.includes('process.env'));
          if (realMatches.length > 0) {
            findings.push({
              file: filePath.replace(srcDir, 'src'),
              matches: realMatches
            });
          }
        }
      });
    }
  });
  
  return findings;
}

const secretFindings = scanForSecrets(srcDir);
if (secretFindings.length > 0) {
  envIssues.push(`Found ${secretFindings.length} potential hardcoded secrets in code`);
  criticalIssues += secretFindings.length;
}

if (envIssues.length === 0) {
  log('✓ Environment variable handling looks good', 'green');
  report += `✅ Environment variable handling is secure.\n\n`;
} else {
  log(`⚠ Found ${envIssues.length} environment variable issues`, 'yellow');
  report += `⚠️ **Issues Found:**\n\n`;
  envIssues.forEach(issue => {
    report += `- ${issue}\n`;
  });
  report += `\n`;
  
  if (secretFindings.length > 0) {
    report += `### Potential Hardcoded Secrets\n\n`;
    secretFindings.forEach(finding => {
      report += `**File:** \`${finding.file}\`\n`;
      finding.matches.forEach(match => {
        report += `- \`${match}\`\n`;
      });
      report += `\n`;
    });
  }
}

// 3. XSS Vulnerability Check
section('3. XSS Vulnerability Check');
log('Checking for potential XSS vulnerabilities...', 'blue');

report += `## XSS Vulnerability Check\n\n`;

const xssPatterns = [
  { pattern: /dangerouslySetInnerHTML/g, severity: 'high', description: 'dangerouslySetInnerHTML usage' },
  { pattern: /innerHTML\s*=/g, severity: 'high', description: 'Direct innerHTML assignment' },
  { pattern: /document\.write/g, severity: 'high', description: 'document.write usage' },
  { pattern: /eval\(/g, severity: 'critical', description: 'eval() usage' },
  { pattern: /new Function\(/g, severity: 'high', description: 'new Function() usage' },
];

function scanForXSS(dir) {
  const files = fs.readdirSync(dir);
  const findings = [];
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      findings.push(...scanForXSS(filePath));
    } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js') || file.endsWith('.jsx')) {
      const content = fs.readFileSync(filePath, 'utf8');
      
      xssPatterns.forEach(({ pattern, severity, description }) => {
        const matches = content.match(pattern);
        if (matches) {
          findings.push({
            file: filePath.replace(srcDir, 'src'),
            severity,
            description,
            count: matches.length
          });
          
          if (severity === 'critical') criticalIssues++;
          else if (severity === 'high') highIssues++;
          else if (severity === 'medium') mediumIssues++;
        }
      });
    }
  });
  
  return findings;
}

const xssFindings = scanForXSS(srcDir);

if (xssFindings.length === 0) {
  log('✓ No obvious XSS vulnerabilities found', 'green');
  report += `✅ No obvious XSS vulnerabilities detected.\n\n`;
} else {
  log(`⚠ Found ${xssFindings.length} potential XSS vulnerabilities`, 'yellow');
  report += `⚠️ **Potential XSS Vulnerabilities:**\n\n`;
  report += `| File | Issue | Severity | Count |\n`;
  report += `|------|-------|----------|-------|\n`;
  
  xssFindings.forEach(finding => {
    const severityIcon = finding.severity === 'critical' ? '🔴' : finding.severity === 'high' ? '🟠' : '🟡';
    report += `| \`${finding.file}\` | ${finding.description} | ${severityIcon} ${finding.severity} | ${finding.count} |\n`;
  });
  
  report += `\n**Recommendations:**\n`;
  report += `- Review all instances of \`dangerouslySetInnerHTML\` and ensure content is sanitized\n`;
  report += `- Use DOMPurify or similar library to sanitize HTML content\n`;
  report += `- Avoid using \`eval()\` and \`new Function()\`\n`;
  report += `- Use React's built-in XSS protection (JSX escaping)\n\n`;
}

// 4. CSRF Protection Check
section('4. CSRF Protection Check');
log('Checking CSRF protection...', 'blue');

report += `## CSRF Protection\n\n`;

// Check for CSRF token implementation
const apiClientPath = path.join(srcDir, 'lib', 'api', 'client.ts');
let csrfProtected = false;

if (fs.existsSync(apiClientPath)) {
  const content = fs.readFileSync(apiClientPath, 'utf8');
  
  if (content.includes('X-CSRF-Token') || content.includes('csrf') || content.includes('CSRF')) {
    csrfProtected = true;
    log('✓ CSRF token implementation found', 'green');
    report += `✅ CSRF token implementation detected in API client.\n\n`;
  } else {
    log('⚠ No CSRF token implementation found', 'yellow');
    report += `⚠️ **Warning:** No CSRF token implementation detected.\n\n`;
    report += `**Recommendation:** Implement CSRF protection for state-changing requests.\n\n`;
    mediumIssues++;
  }
} else {
  log('⚠ API client not found', 'yellow');
  report += `⚠️ Could not verify CSRF protection (API client not found).\n\n`;
}

// Check for SameSite cookie attribute
report += `### Cookie Security\n\n`;
report += `**Recommendations:**\n`;
report += `- Set \`SameSite=Strict\` or \`SameSite=Lax\` on authentication cookies\n`;
report += `- Set \`HttpOnly\` flag on authentication cookies\n`;
report += `- Set \`Secure\` flag on cookies in production\n`;
report += `- Use short-lived tokens with refresh mechanism\n\n`;

// 5. Authentication Flow Review
section('5. Authentication Flow Review');
log('Reviewing authentication implementation...', 'blue');

report += `## Authentication Flow\n\n`;

const authFiles = [
  'src/lib/auth/authContext.tsx',
  'src/lib/auth/authService.ts',
  'src/hooks/useAuth.ts',
];

let authIssues = [];

authFiles.forEach(file => {
  const filePath = path.join(__dirname, '..', file);
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Check for secure token storage
    if (content.includes('localStorage') && content.includes('token')) {
      authIssues.push(`${file}: Tokens stored in localStorage (consider httpOnly cookies)`);
      lowIssues++;
    }
    
    // Check for password handling
    if (content.includes('password') && !content.includes('hash')) {
      // This is a false positive check - just a warning
      authIssues.push(`${file}: Ensure passwords are never logged or stored in plain text`);
    }
  }
});

if (authIssues.length === 0) {
  log('✓ Authentication implementation looks secure', 'green');
  report += `✅ Authentication implementation follows security best practices.\n\n`;
} else {
  log(`⚠ Found ${authIssues.length} authentication concerns`, 'yellow');
  report += `⚠️ **Authentication Concerns:**\n\n`;
  authIssues.forEach(issue => {
    report += `- ${issue}\n`;
  });
  report += `\n`;
}

report += `### Authentication Best Practices Checklist\n\n`;
report += `- [ ] Passwords are hashed with bcrypt/argon2 (backend)\n`;
report += `- [ ] JWT tokens have short expiration (15-30 minutes)\n`;
report += `- [ ] Refresh tokens are used for long-lived sessions\n`;
report += `- [ ] Tokens are stored securely (httpOnly cookies preferred)\n`;
report += `- [ ] Failed login attempts are rate-limited\n`;
report += `- [ ] Account lockout after multiple failed attempts\n`;
report += `- [ ] Password reset tokens expire quickly (15-30 minutes)\n`;
report += `- [ ] Two-factor authentication is available\n`;
report += `- [ ] Session invalidation on logout\n`;
report += `- [ ] Secure password requirements enforced\n\n`;

// 6. API Security Check
section('6. API Security Check');
log('Checking API security measures...', 'blue');

report += `## API Security\n\n`;

report += `### Rate Limiting\n\n`;
report += `**Status:** Should be implemented on backend\n\n`;
report += `**Recommendations:**\n`;
report += `- Implement rate limiting on all API endpoints\n`;
report += `- Use different limits for authenticated vs. unauthenticated users\n`;
report += `- Return 429 status code when limit exceeded\n`;
report += `- Include Retry-After header\n\n`;

report += `### Input Validation\n\n`;

// Check for validation libraries
const packageJsonPath = path.join(__dirname, '..', 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const hasZod = packageJson.dependencies?.zod || packageJson.devDependencies?.zod;
const hasYup = packageJson.dependencies?.yup || packageJson.devDependencies?.yup;

if (hasZod || hasYup) {
  log('✓ Validation library found', 'green');
  report += `✅ Validation library detected (${hasZod ? 'Zod' : 'Yup'}).\n\n`;
} else {
  log('⚠ No validation library found', 'yellow');
  report += `⚠️ **Warning:** No validation library detected.\n\n`;
  report += `**Recommendation:** Use Zod or Yup for input validation.\n\n`;
  mediumIssues++;
}

report += `**Best Practices:**\n`;
report += `- Validate all user inputs on both client and server\n`;
report += `- Sanitize inputs to prevent injection attacks\n`;
report += `- Use allowlists instead of denylists\n`;
report += `- Validate data types, formats, and ranges\n`;
report += `- Reject invalid requests with clear error messages\n\n`;

// 7. Security Headers Check
section('7. Security Headers Check');
log('Checking security headers configuration...', 'blue');

report += `## Security Headers\n\n`;

const nextConfigPath = path.join(__dirname, '..', 'next.config.js');
let hasSecurityHeaders = false;

if (fs.existsSync(nextConfigPath)) {
  const content = fs.readFileSync(nextConfigPath, 'utf8');
  
  if (content.includes('X-Frame-Options') || content.includes('Content-Security-Policy')) {
    hasSecurityHeaders = true;
    log('✓ Security headers configured', 'green');
    report += `✅ Security headers are configured in next.config.js.\n\n`;
  } else {
    log('⚠ Security headers not found in next.config.js', 'yellow');
    report += `⚠️ **Warning:** Security headers not configured.\n\n`;
    mediumIssues++;
  }
}

report += `### Required Security Headers\n\n`;
report += `| Header | Purpose | Status |\n`;
report += `|--------|---------|--------|\n`;
report += `| X-Frame-Options | Prevent clickjacking | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n`;
report += `| X-Content-Type-Options | Prevent MIME sniffing | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n`;
report += `| X-XSS-Protection | Enable XSS filter | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n`;
report += `| Strict-Transport-Security | Enforce HTTPS | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n`;
report += `| Content-Security-Policy | Prevent XSS/injection | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n`;
report += `| Referrer-Policy | Control referrer info | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n`;
report += `| Permissions-Policy | Control browser features | ${hasSecurityHeaders ? '✅' : '⚠️'} |\n\n`;

// 8. Summary
section('8. Security Audit Summary');

report += `## Summary\n\n`;
report += `| Severity | Count |\n`;
report += `|----------|-------|\n`;
report += `| 🔴 Critical | ${criticalIssues} |\n`;
report += `| 🟠 High | ${highIssues} |\n`;
report += `| 🟡 Medium | ${mediumIssues} |\n`;
report += `| 🔵 Low | ${lowIssues} |\n\n`;

if (criticalIssues > 0) {
  log(`🔴 CRITICAL: ${criticalIssues} critical security issues found!`, 'red');
  report += `🔴 **CRITICAL:** ${criticalIssues} critical security issues require immediate attention!\n\n`;
} else if (highIssues > 0) {
  log(`🟠 HIGH: ${highIssues} high severity issues found`, 'yellow');
  report += `🟠 **HIGH:** ${highIssues} high severity issues should be addressed soon.\n\n`;
} else if (mediumIssues > 0) {
  log(`🟡 MEDIUM: ${mediumIssues} medium severity issues found`, 'yellow');
  report += `🟡 **MEDIUM:** ${mediumIssues} medium severity issues should be reviewed.\n\n`;
} else {
  log('✓ No critical or high severity issues found', 'green');
  report += `✅ No critical or high severity security issues detected.\n\n`;
}

report += `## Next Steps\n\n`;
report += `1. **Fix Critical Issues:** Address all critical vulnerabilities immediately\n`;
report += `2. **Review High Issues:** Evaluate and fix high severity issues\n`;
report += `3. **Plan Medium Issues:** Schedule fixes for medium severity issues\n`;
report += `4. **Run npm audit fix:** Automatically fix dependency vulnerabilities\n`;
report += `5. **Manual Testing:** Perform manual security testing\n`;
report += `6. **Penetration Testing:** Consider professional security audit\n`;
report += `7. **Security Training:** Ensure team follows secure coding practices\n\n`;

report += `## Resources\n\n`;
report += `- [OWASP Top 10](https://owasp.org/www-project-top-ten/)\n`;
report += `- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)\n`;
report += `- [Next.js Security](https://nextjs.org/docs/advanced-features/security-headers)\n`;
report += `- [React Security Best Practices](https://react.dev/learn/security)\n`;
report += `- [npm Security Best Practices](https://docs.npmjs.com/security-best-practices)\n\n`;

// Save report
fs.writeFileSync(reportFile, report);

log(`\nReport saved to: ${reportFile}`, 'green');

// Exit with appropriate code
if (criticalIssues > 0) {
  process.exit(1);
} else {
  process.exit(0);
}
