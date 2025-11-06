#!/usr/bin/env node

/**
 * Bundle Optimization Script
 * 
 * Analyzes Next.js bundle sizes and enforces budget limits.
 * Runs in CI/CD to prevent bundle bloat and performance regressions.
 * 
 * Usage:
 *   node scripts/optimizeBundle.ts
 *   npm run analyze:bundle
 * 
 * @module scripts/optimizeBundle
 */

import { promises as fs } from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Bundle size budgets (in KB)
const BUDGETS = {
    'pages/_app': 300,          // Main app bundle
    'pages/index': 200,         // Home page
    'pages/dashboard': 250,     // Dashboard
    'pages/applications': 200,  // Applications page
    'shared': 500,              // Shared chunks (vendors, common)
    'total': 1500,              // Total bundle size
};

// Size thresholds for warnings
const WARNING_THRESHOLD = 0.9; // Warn at 90% of budget
const ERROR_THRESHOLD = 1.0;   // Error at 100% of budget

interface BundleStats {
    file: string;
    size: number;
    gzipSize: number;
    page?: string;
}

interface AnalysisResult {
    bundles: BundleStats[];
    violations: Violation[];
    warnings: Violation[];
    totalSize: number;
    totalGzipSize: number;
}

interface Violation {
    file: string;
    size: number;
    budget: number;
    percentage: number;
    type: 'error' | 'warning';
}

/**
 * Parse Next.js build output to extract bundle sizes
 */
async function parseBuildOutput(): Promise<BundleStats[]> {
    const buildDir = path.join(process.cwd(), '.next');
    const statsFile = path.join(buildDir, 'analyze/client.json');

    try {
        const stats = await fs.readFile(statsFile, 'utf-8');
        const data = JSON.parse(stats);

        return data.assets
            .filter((asset: any) => asset.name.endsWith('.js'))
            .map((asset: any) => ({
                file: asset.name,
                size: asset.size,
                gzipSize: Math.round(asset.size * 0.3), // Estimate gzip size
                page: extractPageName(asset.name),
            }));
    } catch (error) {
        console.error('Failed to parse build stats:', error);
        console.log('Attempting to read build manifest...');

        // Fallback to build manifest
        return await parseBuildManifest();
    }
}

/**
 * Fallback: Parse Next.js build manifest
 */
async function parseBuildManifest(): Promise<BundleStats[]> {
    const buildDir = path.join(process.cwd(), '.next');
    const manifestPath = path.join(buildDir, 'build-manifest.json');

    try {
        const manifest = await fs.readFile(manifestPath, 'utf-8');
        const data = JSON.parse(manifest);
        const bundles: BundleStats[] = [];

        // Parse page bundles
        for (const [page, files] of Object.entries(data.pages)) {
            for (const file of files as string[]) {
                const filePath = path.join(buildDir, 'static', 'chunks', file);
                try {
                    const stats = await fs.stat(filePath);
                    bundles.push({
                        file,
                        size: stats.size,
                        gzipSize: Math.round(stats.size * 0.3),
                        page,
                    });
                } catch {
                    // File might not exist, skip
                }
            }
        }

        return bundles;
    } catch (error) {
        throw new Error(`Failed to parse build manifest: ${error}`);
    }
}

/**
 * Extract page name from bundle filename
 */
function extractPageName(filename: string): string {
    const match = filename.match(/pages[\/\\](.+?)(?:\.[a-f0-9]+)?\.js$/);
    return match ? match[1] : 'unknown';
}

/**
 * Analyze bundles and check against budgets
 */
function analyzeBundles(bundles: BundleStats[]): AnalysisResult {
    const violations: Violation[] = [];
    const warnings: Violation[] = [];
    let totalSize = 0;
    let totalGzipSize = 0;

    // Group bundles by page
    const bundlesByPage = new Map<string, BundleStats[]>();
    bundles.forEach(bundle => {
        const page = bundle.page || 'shared';
        if (!bundlesByPage.has(page)) {
            bundlesByPage.set(page, []);
        }
        bundlesByPage.get(page)!.push(bundle);
        totalSize += bundle.size;
        totalGzipSize += bundle.gzipSize;
    });

    // Check each page against budget
    for (const [page, pageBundles] of bundlesByPage) {
        const pageSize = pageBundles.reduce((sum, b) => sum + b.size, 0);
        const budget = BUDGETS[page as keyof typeof BUDGETS] || BUDGETS.shared;
        const budgetBytes = budget * 1024;
        const percentage = pageSize / budgetBytes;

        if (percentage >= ERROR_THRESHOLD) {
            violations.push({
                file: page,
                size: pageSize,
                budget: budgetBytes,
                percentage,
                type: 'error',
            });
        } else if (percentage >= WARNING_THRESHOLD) {
            warnings.push({
                file: page,
                size: pageSize,
                budget: budgetBytes,
                percentage,
                type: 'warning',
            });
        }
    }

    // Check total size
    const totalBudget = BUDGETS.total * 1024;
    const totalPercentage = totalSize / totalBudget;

    if (totalPercentage >= ERROR_THRESHOLD) {
        violations.push({
            file: 'total',
            size: totalSize,
            budget: totalBudget,
            percentage: totalPercentage,
            type: 'error',
        });
    } else if (totalPercentage >= WARNING_THRESHOLD) {
        warnings.push({
            file: 'total',
            size: totalSize,
            budget: totalBudget,
            percentage: totalPercentage,
            type: 'warning',
        });
    }

    return {
        bundles,
        violations,
        warnings,
        totalSize,
        totalGzipSize,
    };
}

/**
 * Format bytes to human readable string
 */
function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Print analysis report
 */
function printReport(result: AnalysisResult): void {
    console.log('\n📦 Bundle Analysis Report\n');
    console.log('='.repeat(60));

    // Summary
    console.log(`\nTotal Bundle Size: ${formatBytes(result.totalSize)}`);
    console.log(`Total Gzipped: ${formatBytes(result.totalGzipSize)}`);
    console.log(`Number of Bundles: ${result.bundles.length}`);

    // Violations
    if (result.violations.length > 0) {
        console.log(`\n❌ Budget Violations (${result.violations.length}):\n`);
        result.violations.forEach(v => {
            console.log(`  ${v.file}`);
            console.log(`    Size: ${formatBytes(v.size)} / ${formatBytes(v.budget)}`);
            console.log(`    Over budget by: ${((v.percentage - 1) * 100).toFixed(1)}%`);
        });
    }

    // Warnings
    if (result.warnings.length > 0) {
        console.log(`\n⚠️  Warnings (${result.warnings.length}):\n`);
        result.warnings.forEach(w => {
            console.log(`  ${w.file}`);
            console.log(`    Size: ${formatBytes(w.size)} / ${formatBytes(w.budget)}`);
            console.log(`    Using: ${(w.percentage * 100).toFixed(1)}% of budget`);
        });
    }

    // Largest bundles
    const largest = [...result.bundles]
        .sort((a, b) => b.size - a.size)
        .slice(0, 5);

    console.log('\n📊 Largest Bundles:\n');
    largest.forEach((bundle, i) => {
        console.log(`  ${i + 1}. ${bundle.file}`);
        console.log(`     ${formatBytes(bundle.size)} (${formatBytes(bundle.gzipSize)} gzipped)`);
    });

    console.log('\n' + '='.repeat(60) + '\n');

    // Recommendations
    if (result.violations.length > 0 || result.warnings.length > 0) {
        console.log('💡 Optimization Recommendations:\n');
        console.log('  • Use dynamic imports for large components');
        console.log('  • Enable tree shaking for unused code');
        console.log('  • Consider code splitting for routes');
        console.log('  • Analyze with: npm run analyze:bundle');
        console.log('  • Check for duplicate dependencies');
        console.log('  • Use lighter alternatives for heavy libraries\n');
    }
}

/**
 * Save report to file
 */
async function saveReport(result: AnalysisResult): Promise<void> {
    const reportPath = path.join(process.cwd(), 'reports/bundle-analysis.json');
    await fs.mkdir(path.dirname(reportPath), { recursive: true });
    await fs.writeFile(reportPath, JSON.stringify(result, null, 2));
    console.log(`📄 Report saved to: ${reportPath}\n`);
}

/**
 * Main execution
 */
async function main() {
    console.log('🚀 Starting bundle analysis...\n');

    try {
        // Build the project first
        console.log('Building project...');
        execSync('npm run build', { stdio: 'inherit' });

        // Parse bundle stats
        console.log('\nParsing bundle statistics...');
        const bundles = await parseBuildOutput();

        // Analyze
        const result = analyzeBundles(bundles);

        // Print report
        printReport(result);

        // Save to file
        await saveReport(result);

        // Exit with error if violations found
        if (result.violations.length > 0) {
            console.error('❌ Bundle size budget violations detected!');
            process.exit(1);
        }

        if (result.warnings.length > 0) {
            console.warn('⚠️  Bundle size warnings detected. Consider optimization.');
        } else {
            console.log('✅ All bundle sizes within budget!');
        }

    } catch (error) {
        console.error('❌ Bundle analysis failed:', error);
        process.exit(1);
    }
}

// Run if executed directly
if (require.main === module) {
    main();
}

export { analyzeBundles, parseBuildOutput, formatBytes };
