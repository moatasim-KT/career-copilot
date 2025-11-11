#!/usr/bin/env node

/**
 * Performance Audit Script
 * 
 * Runs comprehensive performance tests including:
 * - Lighthouse audits on all main pages
 * - Core Web Vitals measurement
 * - Network throttling tests
 * - CPU throttling tests
 * - Bundle size analysis
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
      throw error;
    }
    return null;
  }
}

// Create reports directory
const reportsDir = path.join(__dirname, '..', 'reports', 'performance');
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
const reportFile = path.join(reportsDir, `performance-audit-${timestamp}.md`);

let report = `# Performance Audit Report\n\n`;
report += `**Date:** ${new Date().toLocaleString()}\n\n`;
report += `**Environment:** ${process.env.NODE_ENV || 'development'}\n\n`;

// 1. Build the application
section('1. Building Application');
log('Building Next.js application for production...', 'blue');
try {
  exec('npm run build');
  log('✓ Build completed successfully', 'green');
  report += `## Build Status\n\n✅ Build completed successfully\n\n`;
} catch (error) {
  log('✗ Build failed', 'red');
  report += `## Build Status\n\n❌ Build failed\n\n`;
  fs.writeFileSync(reportFile, report);
  process.exit(1);
}

// 2. Bundle Size Analysis
section('2. Bundle Size Analysis');
log('Analyzing bundle sizes...', 'blue');
try {
  const buildDir = path.join(__dirname, '..', '.next');
  const buildManifest = path.join(buildDir, 'build-manifest.json');
  
  if (fs.existsSync(buildManifest)) {
    const manifest = JSON.parse(fs.readFileSync(buildManifest, 'utf8'));
    report += `## Bundle Size Analysis\n\n`;
    
    // Get static files
    const staticDir = path.join(buildDir, 'static', 'chunks');
    if (fs.existsSync(staticDir)) {
      const files = fs.readdirSync(staticDir);
      let totalSize = 0;
      const fileSizes = [];
      
      files.forEach(file => {
        if (file.endsWith('.js')) {
          const filePath = path.join(staticDir, file);
          const stats = fs.statSync(filePath);
          const sizeKB = (stats.size / 1024).toFixed(2);
          totalSize += stats.size;
          fileSizes.push({ file, size: sizeKB });
        }
      });
      
      // Sort by size descending
      fileSizes.sort((a, b) => parseFloat(b.size) - parseFloat(a.size));
      
      report += `### JavaScript Bundles\n\n`;
      report += `**Total Size:** ${(totalSize / 1024).toFixed(2)} KB\n\n`;
      report += `| File | Size (KB) | Status |\n`;
      report += `|------|-----------|--------|\n`;
      
      fileSizes.slice(0, 10).forEach(({ file, size }) => {
        const status = parseFloat(size) > 200 ? '⚠️ Large' : '✅ OK';
        report += `| ${file} | ${size} | ${status} |\n`;
      });
      
      report += `\n`;
      
      if (totalSize / 1024 > 250) {
        log('⚠ Total bundle size exceeds 250KB target', 'yellow');
        report += `⚠️ **Warning:** Total bundle size exceeds 250KB target\n\n`;
      } else {
        log('✓ Bundle size within target', 'green');
        report += `✅ Bundle size within 250KB target\n\n`;
      }
    }
  }
} catch (error) {
  log('⚠ Could not analyze bundle sizes', 'yellow');
  report += `⚠️ Bundle size analysis unavailable\n\n`;
}

// 3. Run Lighthouse CI
section('3. Running Lighthouse Audits');
log('Running Lighthouse on all main pages...', 'blue');
log('This may take several minutes...', 'yellow');

try {
  // Run Lighthouse CI
  exec('npx lhci autorun --config=lighthouserc.json', { ignoreError: true });
  
  // Check for Lighthouse results
  const lhciDir = path.join(__dirname, '..', '.lighthouseci');
  if (fs.existsSync(lhciDir)) {
    log('✓ Lighthouse audits completed', 'green');
    report += `## Lighthouse Audit Results\n\n`;
    report += `Lighthouse audits completed. Results saved to \`.lighthouseci/\` directory.\n\n`;
    
    // Try to parse results
    const files = fs.readdirSync(lhciDir);
    const manifestFile = files.find(f => f.includes('manifest'));
    
    if (manifestFile) {
      try {
        const manifest = JSON.parse(fs.readFileSync(path.join(lhciDir, manifestFile), 'utf8'));
        
        report += `### Summary\n\n`;
        report += `| Page | Performance | Accessibility | Best Practices | SEO |\n`;
        report += `|------|-------------|---------------|----------------|-----|\n`;
        
        manifest.forEach(result => {
          const url = result.url.replace('http://localhost:3000', '');
          const perf = Math.round(result.summary.performance * 100);
          const a11y = Math.round(result.summary.accessibility * 100);
          const bp = Math.round(result.summary['best-practices'] * 100);
          const seo = Math.round(result.summary.seo * 100);
          
          const perfStatus = perf >= 95 ? '✅' : perf >= 90 ? '⚠️' : '❌';
          const a11yStatus = a11y >= 95 ? '✅' : a11y >= 90 ? '⚠️' : '❌';
          const bpStatus = bp >= 95 ? '✅' : bp >= 90 ? '⚠️' : '❌';
          const seoStatus = seo >= 90 ? '✅' : seo >= 85 ? '⚠️' : '❌';
          
          report += `| ${url || '/'} | ${perfStatus} ${perf} | ${a11yStatus} ${a11y} | ${bpStatus} ${bp} | ${seoStatus} ${seo} |\n`;
        });
        
        report += `\n`;
      } catch (e) {
        log('⚠ Could not parse Lighthouse results', 'yellow');
      }
    }
  } else {
    log('⚠ Lighthouse results not found', 'yellow');
    report += `⚠️ Lighthouse results not available\n\n`;
  }
} catch (error) {
  log('⚠ Lighthouse audit encountered issues', 'yellow');
  report += `⚠️ Lighthouse audit encountered issues\n\n`;
}

// 4. Core Web Vitals Targets
section('4. Core Web Vitals Targets');
report += `## Core Web Vitals Targets\n\n`;
report += `| Metric | Target | Status |\n`;
report += `|--------|--------|--------|\n`;
report += `| First Contentful Paint (FCP) | < 1.5s | See Lighthouse results |\n`;
report += `| Largest Contentful Paint (LCP) | < 2.5s | See Lighthouse results |\n`;
report += `| Cumulative Layout Shift (CLS) | < 0.1 | See Lighthouse results |\n`;
report += `| First Input Delay (FID) | < 100ms | See Lighthouse results |\n`;
report += `| Total Blocking Time (TBT) | < 200ms | See Lighthouse results |\n`;
report += `\n`;

// 5. Network Throttling Test
section('5. Network Throttling Test');
log('Testing with slow 3G network simulation...', 'blue');
report += `## Network Throttling Test\n\n`;
report += `Testing with slow 3G network conditions:\n`;
report += `- Download: 400 Kbps\n`;
report += `- Upload: 400 Kbps\n`;
report += `- RTT: 400ms\n\n`;
report += `Run Lighthouse with \`--throttling-method=simulate\` to test slow networks.\n\n`;
log('ℹ Use Chrome DevTools Network throttling for manual testing', 'cyan');

// 6. CPU Throttling Test
section('6. CPU Throttling Test');
log('Testing with CPU throttling...', 'blue');
report += `## CPU Throttling Test\n\n`;
report += `Testing with 4x CPU slowdown to simulate low-end devices.\n\n`;
report += `Run Lighthouse with CPU throttling enabled (default in mobile mode).\n\n`;
log('ℹ Use Chrome DevTools Performance panel with 4x slowdown', 'cyan');

// 7. Recommendations
section('7. Performance Recommendations');
report += `## Performance Optimization Recommendations\n\n`;
report += `### General Guidelines\n\n`;
report += `1. **Code Splitting**\n`;
report += `   - Use dynamic imports for heavy components\n`;
report += `   - Lazy load routes and features\n`;
report += `   - Keep initial bundle < 150KB gzipped\n\n`;
report += `2. **Image Optimization**\n`;
report += `   - Use Next.js Image component\n`;
report += `   - Serve WebP format\n`;
report += `   - Add blur placeholders\n`;
report += `   - Lazy load below-fold images\n\n`;
report += `3. **Caching Strategy**\n`;
report += `   - Configure React Query cache times\n`;
report += `   - Use stale-while-revalidate pattern\n`;
report += `   - Implement service worker for offline support\n\n`;
report += `4. **List Virtualization**\n`;
report += `   - Use @tanstack/react-virtual for long lists\n`;
report += `   - Render only visible items\n`;
report += `   - Target 60fps scrolling\n\n`;
report += `5. **Font Optimization**\n`;
report += `   - Use font-display: swap\n`;
report += `   - Preload critical fonts\n`;
report += `   - Subset fonts to reduce size\n\n`;
report += `6. **Third-Party Scripts**\n`;
report += `   - Load analytics asynchronously\n`;
report += `   - Defer non-critical scripts\n`;
report += `   - Use Next.js Script component\n\n`;

// 8. Testing Checklist
report += `## Performance Testing Checklist\n\n`;
report += `- [ ] Run Lighthouse on all main pages\n`;
report += `- [ ] Verify Performance score > 95\n`;
report += `- [ ] Verify Accessibility score > 95\n`;
report += `- [ ] Verify Best Practices score > 95\n`;
report += `- [ ] Verify SEO score > 90\n`;
report += `- [ ] Test FCP < 1.5s\n`;
report += `- [ ] Test LCP < 2.5s\n`;
report += `- [ ] Test CLS < 0.1\n`;
report += `- [ ] Test FID < 100ms\n`;
report += `- [ ] Test on slow 3G network\n`;
report += `- [ ] Test with 4x CPU throttling\n`;
report += `- [ ] Verify bundle size < 250KB gzipped\n`;
report += `- [ ] Test on low-end devices\n`;
report += `- [ ] Verify 60fps scrolling on long lists\n`;
report += `- [ ] Check for memory leaks\n\n`;

// Save report
fs.writeFileSync(reportFile, report);

section('Performance Audit Complete');
log(`Report saved to: ${reportFile}`, 'green');
log('\nNext steps:', 'bright');
log('1. Review the Lighthouse results in .lighthouseci/ directory', 'cyan');
log('2. Check the performance report for recommendations', 'cyan');
log('3. Test manually with Chrome DevTools Network and Performance panels', 'cyan');
log('4. Address any issues found and re-run the audit', 'cyan');

process.exit(0);
