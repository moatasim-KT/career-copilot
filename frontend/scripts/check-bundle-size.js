#!/usr/bin/env node

/**
 * Bundle Size Budget Checker
 * 
 * This script analyzes the Next.js build output and checks if bundle sizes
 * exceed the defined budgets:
 * - Warning threshold: 200KB per route
 * - Error threshold: 250KB per route
 * 
 * Exit codes:
 * - 0: All bundles within budget
 * - 1: One or more bundles exceed error threshold
 * - 2: One or more bundles exceed warning threshold
 */

const fs = require('fs');
const path = require('path');

// Bundle size budgets (in bytes)
const BUDGETS = {
  WARNING_THRESHOLD: 200 * 1024, // 200KB
  ERROR_THRESHOLD: 250 * 1024,   // 250KB
  TOTAL_WARNING: 1000 * 1024,    // 1MB total
  TOTAL_ERROR: 1500 * 1024,      // 1.5MB total
};

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  bold: '\x1b[1m',
};

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getPercentage(value, threshold) {
  return ((value / threshold) * 100).toFixed(1);
}

function getBudgetStatus(size) {
  if (size > BUDGETS.ERROR_THRESHOLD) {
    return { status: 'ERROR', color: colors.red, symbol: '✗' };
  } else if (size > BUDGETS.WARNING_THRESHOLD) {
    return { status: 'WARNING', color: colors.yellow, symbol: '⚠' };
  } else {
    return { status: 'OK', color: colors.green, symbol: '✓' };
  }
}

function parseNextBuildOutput() {
  const buildManifestPath = path.join(__dirname, '../.next/build-manifest.json');

  if (!fs.existsSync(buildManifestPath)) {
    console.error(`${colors.red}Error: Build manifest not found. Please run 'npm run build' first.${colors.reset}`);
    process.exit(1);
  }

  const buildManifest = JSON.parse(fs.readFileSync(buildManifestPath, 'utf8'));
  const bundles = [];
  const staticDir = path.join(__dirname, '../.next/static');

  // Analyze each page's bundles
  for (const [route, files] of Object.entries(buildManifest.pages)) {
    let totalSize = 0;
    const routeFiles = [];

    for (const file of files) {
      const filePath = path.join(staticDir, file);
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        totalSize += stats.size;
        routeFiles.push({
          file,
          size: stats.size,
        });
      }
    }

    bundles.push({
      route,
      size: totalSize,
      files: routeFiles,
    });
  }

  return bundles;
}

function analyzeBundles() {
  console.log(`\n${colors.bold}${colors.blue}Bundle Size Analysis${colors.reset}\n`);
  console.log('─'.repeat(80));

  const bundles = parseNextBuildOutput();
  const violations = {
    errors: [],
    warnings: [],
  };

  let totalSize = 0;

  // Sort bundles by size (largest first)
  bundles.sort((a, b) => b.size - a.size);

  console.log(`\n${colors.bold}Route Bundles:${colors.reset}\n`);
  console.log('Route'.padEnd(40) + 'Size'.padEnd(15) + 'Status'.padEnd(15) + 'Budget Usage');
  console.log('─'.repeat(80));

  for (const bundle of bundles) {
    const { status, color, symbol } = getBudgetStatus(bundle.size);
    const percentage = getPercentage(bundle.size, BUDGETS.ERROR_THRESHOLD);
    const budgetBar = createProgressBar(bundle.size, BUDGETS.ERROR_THRESHOLD);

    totalSize += bundle.size;

    console.log(
      bundle.route.padEnd(40) +
      formatBytes(bundle.size).padEnd(15) +
      `${color}${symbol} ${status}${colors.reset}`.padEnd(25) +
      `${percentage}% ${budgetBar}`
    );

    if (status === 'ERROR') {
      violations.errors.push({
        route: bundle.route,
        size: bundle.size,
        threshold: BUDGETS.ERROR_THRESHOLD,
        overage: bundle.size - BUDGETS.ERROR_THRESHOLD,
      });
    } else if (status === 'WARNING') {
      violations.warnings.push({
        route: bundle.route,
        size: bundle.size,
        threshold: BUDGETS.WARNING_THRESHOLD,
        overage: bundle.size - BUDGETS.WARNING_THRESHOLD,
      });
    }
  }

  console.log('─'.repeat(80));
  console.log(`\n${colors.bold}Total Bundle Size:${colors.reset} ${formatBytes(totalSize)}`);

  // Check total size
  const totalStatus = getBudgetStatus(totalSize);
  console.log(`${colors.bold}Total Budget Status:${colors.reset} ${totalStatus.color}${totalStatus.symbol} ${totalStatus.status}${colors.reset}`);

  // Display budgets
  console.log(`\n${colors.bold}Budget Thresholds:${colors.reset}`);
  console.log(`  Warning: ${formatBytes(BUDGETS.WARNING_THRESHOLD)} per route`);
  console.log(`  Error:   ${formatBytes(BUDGETS.ERROR_THRESHOLD)} per route`);

  // Display violations
  if (violations.errors.length > 0) {
    console.log(`\n${colors.red}${colors.bold}❌ ERROR: ${violations.errors.length} route(s) exceed error threshold!${colors.reset}\n`);
    for (const violation of violations.errors) {
      console.log(`  ${colors.red}✗${colors.reset} ${violation.route}`);
      console.log(`    Size: ${formatBytes(violation.size)} (${formatBytes(violation.overage)} over budget)`);
      console.log(`    Threshold: ${formatBytes(violation.threshold)}`);
    }
  }

  if (violations.warnings.length > 0) {
    console.log(`\n${colors.yellow}${colors.bold}⚠ WARNING: ${violations.warnings.length} route(s) exceed warning threshold!${colors.reset}\n`);
    for (const violation of violations.warnings) {
      console.log(`  ${colors.yellow}⚠${colors.reset} ${violation.route}`);
      console.log(`    Size: ${formatBytes(violation.size)} (${formatBytes(violation.overage)} over budget)`);
      console.log(`    Threshold: ${formatBytes(violation.threshold)}`);
    }
  }

  if (violations.errors.length === 0 && violations.warnings.length === 0) {
    console.log(`\n${colors.green}${colors.bold}✓ All bundles are within budget!${colors.reset}\n`);
  }

  // Recommendations
  if (violations.errors.length > 0 || violations.warnings.length > 0) {
    console.log(`\n${colors.bold}Recommendations:${colors.reset}`);
    console.log('  1. Use dynamic imports for heavy components');
    console.log('  2. Implement code splitting for large routes');
    console.log('  3. Review and optimize dependencies');
    console.log('  4. Use Next.js Image component for images');
    console.log('  5. Enable tree shaking for unused code');
    console.log('  6. Consider lazy loading non-critical features\n');
  }

  // Save report
  const report = {
    timestamp: new Date().toISOString(),
    totalSize,
    bundles: bundles.map(b => ({
      route: b.route,
      size: b.size,
      status: getBudgetStatus(b.size).status,
    })),
    violations,
    budgets: BUDGETS,
  };

  const reportsDir = path.join(__dirname, '../reports');
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
  }

  fs.writeFileSync(
    path.join(reportsDir, 'bundle-size-report.json'),
    JSON.stringify(report, null, 2)
  );

  console.log(`${colors.blue}Report saved to: reports/bundle-size-report.json${colors.reset}\n`);

  // Exit with appropriate code
  if (violations.errors.length > 0) {
    process.exit(1);
  } else if (violations.warnings.length > 0) {
    process.exit(2);
  } else {
    process.exit(0);
  }
}

function createProgressBar(value, max, width = 20) {
  const percentage = Math.min(value / max, 1);
  const filled = Math.round(width * percentage);
  const empty = width - filled;

  let color = colors.green;
  if (percentage > 1) {
    color = colors.red;
  } else if (percentage > 0.8) {
    color = colors.yellow;
  }

  return `${color}${'█'.repeat(filled)}${colors.reset}${'░'.repeat(empty)}`;
}

// Run the analysis
try {
  analyzeBundles();
} catch (error) {
  console.error(`${colors.red}Error analyzing bundles:${colors.reset}`, error.message);
  process.exit(1);
}
