#!/usr/bin/env node

/**
 * Accessibility Audit Script
 * 
 * Performs WCAG 2.1 AA compliance testing using axe-core across all major pages
 * Generates detailed reports with prioritized issues
 * 
 * Usage:
 *   npm run accessibility:audit
 *   npm run accessibility:audit -- --url=http://localhost:3000/specific-page
 *   npm run accessibility:audit -- --verbose
 */

const { AxePuppeteer } = require('@axe-core/puppeteer');
const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
const REPORT_DIR = path.join(__dirname, '../reports/accessibility');
const VERBOSE = process.argv.includes('--verbose');
const CUSTOM_URL = process.argv.find(arg => arg.startsWith('--url='))?.split('=')[1];

// Pages to audit
const PAGES_TO_AUDIT = [
    { name: 'Dashboard', path: '/' },
    { name: 'Jobs List', path: '/jobs' },
    { name: 'Job Details', path: '/jobs/1' }, // Mock ID
    { name: 'Applications', path: '/applications' },
    { name: 'Application Details', path: '/applications/1' }, // Mock ID
    { name: 'Content Generator', path: '/content' },
    { name: 'Interview Prep', path: '/interview' },
    { name: 'Analytics', path: '/analytics' },
    { name: 'Settings', path: '/settings' },
    { name: 'Help', path: '/help' },
];

// WCAG 2.1 AA rules configuration
const AXE_OPTIONS = {
    runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']
    }
};

// Severity mapping
const SEVERITY_LEVELS = {
    critical: { priority: 1, emoji: '🔴', label: 'CRITICAL' },
    serious: { priority: 2, emoji: '🟠', label: 'SERIOUS' },
    moderate: { priority: 3, emoji: '🟡', label: 'MODERATE' },
    minor: { priority: 4, emoji: '🟢', label: 'MINOR' }
};

class AccessibilityAuditor {
    constructor() {
        this.browser = null;
        this.results = [];
        this.summary = {
            totalPages: 0,
            totalViolations: 0,
            criticalViolations: 0,
            seriousViolations: 0,
            moderateViolations: 0,
            minorViolations: 0,
            passedPages: 0,
            failedPages: 0,
            timestamp: new Date().toISOString()
        };
    }

    async init() {
        console.log('🚀 Launching browser for accessibility audit...\n');
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });
    }

    async auditPage(pageConfig) {
        const page = await this.browser.newPage();
        const url = `${BASE_URL}${pageConfig.path}`;

        console.log(`\n📄 Auditing: ${pageConfig.name}`);
        console.log(`   URL: ${url}`);

        try {
            // Set viewport for consistent testing
            await page.setViewport({ width: 1920, height: 1080 });

            // Navigate to page with timeout
            await page.goto(url, {
                waitUntil: 'networkidle0',
                timeout: 30000
            });

            // Wait for page to be fully rendered
            await page.waitForTimeout(2000);

            // Run axe accessibility checks
            const results = await new AxePuppeteer(page)
                .options(AXE_OPTIONS)
                .analyze();

            const violations = results.violations;
            const passes = results.passes;

            // Categorize violations by severity
            const violationsBySeverity = {
                critical: violations.filter(v => v.impact === 'critical'),
                serious: violations.filter(v => v.impact === 'serious'),
                moderate: violations.filter(v => v.impact === 'moderate'),
                minor: violations.filter(v => v.impact === 'minor')
            };

            // Update summary
            this.summary.totalViolations += violations.length;
            this.summary.criticalViolations += violationsBySeverity.critical.length;
            this.summary.seriousViolations += violationsBySeverity.serious.length;
            this.summary.moderateViolations += violationsBySeverity.moderate.length;
            this.summary.minorViolations += violationsBySeverity.minor.length;

            if (violations.length === 0) {
                this.summary.passedPages++;
                console.log(`   ✅ No violations found!`);
            } else {
                this.summary.failedPages++;
                console.log(`   ❌ Found ${violations.length} violation(s)`);

                if (VERBOSE) {
                    this.logViolations(violationsBySeverity);
                } else {
                    console.log(`      ${violationsBySeverity.critical.length} critical, ${violationsBySeverity.serious.length} serious, ${violationsBySeverity.moderate.length} moderate, ${violationsBySeverity.minor.length} minor`);
                }
            }

            // Store results
            this.results.push({
                page: pageConfig.name,
                url,
                violations,
                violationsBySeverity,
                passes: passes.length,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error(`   ⚠️  Error auditing ${pageConfig.name}: ${error.message}`);
            this.results.push({
                page: pageConfig.name,
                url,
                error: error.message,
                timestamp: new Date().toISOString()
            });
        } finally {
            await page.close();
        }
    }

    logViolations(violationsBySeverity) {
        for (const [severity, violations] of Object.entries(violationsBySeverity)) {
            if (violations.length > 0) {
                const { emoji, label } = SEVERITY_LEVELS[severity];
                console.log(`\n      ${emoji} ${label} Issues (${violations.length}):`);

                violations.forEach((violation, index) => {
                    console.log(`      ${index + 1}. ${violation.help}`);
                    console.log(`         Rule: ${violation.id}`);
                    console.log(`         Impact: ${violation.impact}`);
                    console.log(`         Affected elements: ${violation.nodes.length}`);

                    if (VERBOSE && violation.nodes.length > 0) {
                        console.log(`         Example: ${violation.nodes[0].html.substring(0, 100)}...`);
                    }
                });
            }
        }
    }

    async generateReport() {
        console.log('\n\n📊 Generating accessibility report...\n');

        // Ensure report directory exists
        await fs.mkdir(REPORT_DIR, { recursive: true });

        const reportDate = new Date().toISOString().split('T')[0];
        const jsonReportPath = path.join(REPORT_DIR, `accessibility-audit-${reportDate}.json`);
        const mdReportPath = path.join(REPORT_DIR, `accessibility-audit-${reportDate}.md`);

        // Generate JSON report
        const jsonReport = {
            summary: this.summary,
            results: this.results
        };
        await fs.writeFile(jsonReportPath, JSON.stringify(jsonReport, null, 2));
        console.log(`✅ JSON report saved: ${jsonReportPath}`);

        // Generate Markdown report
        const mdReport = this.generateMarkdownReport();
        await fs.writeFile(mdReportPath, mdReport);
        console.log(`✅ Markdown report saved: ${mdReportPath}`);

        return { jsonReportPath, mdReportPath };
    }

    generateMarkdownReport() {
        const { summary, results } = this;

        let md = `# Accessibility Audit Report\n\n`;
        md += `**Generated:** ${new Date(summary.timestamp).toLocaleString()}\n`;
        md += `**WCAG Level:** 2.1 AA\n\n`;

        // Executive Summary
        md += `## Executive Summary\n\n`;
        md += `| Metric | Count |\n`;
        md += `|--------|-------|\n`;
        md += `| Total Pages Audited | ${summary.totalPages} |\n`;
        md += `| Passed (No Violations) | ${summary.passedPages} |\n`;
        md += `| Failed (With Violations) | ${summary.failedPages} |\n`;
        md += `| Total Violations | ${summary.totalViolations} |\n`;
        md += `| 🔴 Critical | ${summary.criticalViolations} |\n`;
        md += `| 🟠 Serious | ${summary.seriousViolations} |\n`;
        md += `| 🟡 Moderate | ${summary.moderateViolations} |\n`;
        md += `| 🟢 Minor | ${summary.minorViolations} |\n\n`;

        // Pass/Fail Status
        const overallStatus = summary.criticalViolations === 0 && summary.seriousViolations === 0
            ? '✅ PASS'
            : '❌ FAIL';
        md += `**Overall Status:** ${overallStatus}\n\n`;

        if (summary.criticalViolations > 0 || summary.seriousViolations > 0) {
            md += `⚠️ **Action Required:** ${summary.criticalViolations + summary.seriousViolations} high-priority violations must be fixed before deployment.\n\n`;
        }

        // Detailed Results by Page
        md += `## Detailed Results\n\n`;

        results.forEach(result => {
            if (result.error) {
                md += `### ❌ ${result.page}\n`;
                md += `**URL:** ${result.url}\n`;
                md += `**Error:** ${result.error}\n\n`;
                return;
            }

            const status = result.violations.length === 0 ? '✅' : '❌';
            md += `### ${status} ${result.page}\n`;
            md += `**URL:** ${result.url}\n`;
            md += `**Violations:** ${result.violations.length}\n`;
            md += `**Passes:** ${result.passes}\n\n`;

            if (result.violations.length > 0) {
                md += `#### Violations by Severity\n\n`;

                for (const [severity, violations] of Object.entries(result.violationsBySeverity)) {
                    if (violations.length > 0) {
                        const { emoji, label } = SEVERITY_LEVELS[severity];
                        md += `##### ${emoji} ${label} (${violations.length})\n\n`;

                        violations.forEach((violation, index) => {
                            md += `${index + 1}. **${violation.help}**\n`;
                            md += `   - **Rule ID:** \`${violation.id}\`\n`;
                            md += `   - **Impact:** ${violation.impact}\n`;
                            md += `   - **Description:** ${violation.description}\n`;
                            md += `   - **Affected Elements:** ${violation.nodes.length}\n`;
                            md += `   - **WCAG Criteria:** ${violation.tags.filter(t => t.startsWith('wcag')).join(', ')}\n`;

                            if (violation.nodes.length > 0) {
                                md += `   - **Example Element:**\n`;
                                md += `     \`\`\`html\n`;
                                md += `     ${violation.nodes[0].html}\n`;
                                md += `     \`\`\`\n`;
                                md += `   - **How to Fix:** ${violation.nodes[0].failureSummary}\n`;
                            }
                            md += `\n`;
                        });
                    }
                }
            }

            md += `---\n\n`;
        });

        // Recommendations
        md += `## Recommendations\n\n`;
        md += `### Priority 1: Critical & Serious Issues\n`;
        md += `- [ ] Fix all ${summary.criticalViolations} critical violations\n`;
        md += `- [ ] Fix all ${summary.seriousViolations} serious violations\n`;
        md += `- [ ] Conduct manual keyboard navigation testing\n`;
        md += `- [ ] Test with screen readers (NVDA, JAWS, VoiceOver)\n\n`;

        md += `### Priority 2: Moderate Issues\n`;
        md += `- [ ] Address ${summary.moderateViolations} moderate violations\n`;
        md += `- [ ] Verify color contrast ratios (WCAG AA: 4.5:1 for normal text)\n`;
        md += `- [ ] Ensure all interactive elements have focus indicators\n\n`;

        md += `### Priority 3: Minor Issues & Best Practices\n`;
        md += `- [ ] Fix ${summary.minorViolations} minor violations\n`;
        md += `- [ ] Add ARIA labels where appropriate\n`;
        md += `- [ ] Improve semantic HTML structure\n`;
        md += `- [ ] Add skip-to-content links\n\n`;

        md += `## Resources\n\n`;
        md += `- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)\n`;
        md += `- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)\n`;
        md += `- [WebAIM WCAG Checklist](https://webaim.org/standards/wcag/checklist)\n`;
        md += `- [A11y Project Checklist](https://www.a11yproject.com/checklist/)\n\n`;

        return md;
    }

    async run() {
        try {
            await this.init();

            const pagesToAudit = CUSTOM_URL
                ? [{ name: 'Custom URL', path: CUSTOM_URL.replace(BASE_URL, '') }]
                : PAGES_TO_AUDIT;

            this.summary.totalPages = pagesToAudit.length;

            console.log(`🔍 Starting WCAG 2.1 AA Accessibility Audit`);
            console.log(`📋 Auditing ${pagesToAudit.length} page(s)...\n`);

            for (const page of pagesToAudit) {
                await this.auditPage(page);
            }

            const { jsonReportPath, mdReportPath } = await this.generateReport();

            // Print summary
            console.log('\n\n' + '='.repeat(60));
            console.log('📊 ACCESSIBILITY AUDIT SUMMARY');
            console.log('='.repeat(60));
            console.log(`\nTotal Pages Audited: ${this.summary.totalPages}`);
            console.log(`Passed: ${this.summary.passedPages} | Failed: ${this.summary.failedPages}`);
            console.log(`\nTotal Violations: ${this.summary.totalViolations}`);
            console.log(`  🔴 Critical: ${this.summary.criticalViolations}`);
            console.log(`  🟠 Serious: ${this.summary.seriousViolations}`);
            console.log(`  🟡 Moderate: ${this.summary.moderateViolations}`);
            console.log(`  🟢 Minor: ${this.summary.minorViolations}`);

            const overallStatus = this.summary.criticalViolations === 0 && this.summary.seriousViolations === 0
                ? '✅ PASS'
                : '❌ FAIL';
            console.log(`\nOverall Status: ${overallStatus}`);
            console.log('\n' + '='.repeat(60) + '\n');

            if (this.summary.criticalViolations > 0 || this.summary.seriousViolations > 0) {
                console.log('⚠️  HIGH PRIORITY: Fix critical and serious violations before deployment!');
                process.exit(1);
            }

        } catch (error) {
            console.error('❌ Audit failed:', error);
            process.exit(1);
        } finally {
            if (this.browser) {
                await this.browser.close();
            }
        }
    }
}

// Run audit
const auditor = new AccessibilityAuditor();
auditor.run().catch(console.error);
