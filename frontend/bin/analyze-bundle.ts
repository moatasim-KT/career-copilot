/**
 * Bundle Analyzer Script
 * 
 * Analyzes and reports on bundle size, identifies large dependencies,
 * and provides optimization recommendations.
 * 
 * @module scripts/analyzeBundle
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

interface BundleAnalysis {
  timestamp: string;
  totalSize: number;
  gzippedSize: number;
  chunks: Array<{
    name: string;
    size: number;
    gzipped: number;
  }>;
  largestDependencies: Array<{
    name: string;
    size: number;
  }>;
  recommendations: string[];
}

/**
 * Size thresholds (in bytes)
 */
const THRESHOLDS = {
  INITIAL_BUNDLE: 200 * 1024, // 200KB
  CHUNK: 100 * 1024, // 100KB
  WARNING: 150 * 1024, // 150KB
};

/**
 * Get directory size recursively
 */
function getDirSize(dirPath: string): number {
  let size = 0;
  
  try {
    const files = fs.readdirSync(dirPath);
    
    files.forEach((file) => {
      const filePath = path.join(dirPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        size += getDirSize(filePath);
      } else {
        size += stats.size;
      }
    });
  } catch (error) {
    console.error(`Error reading directory ${dirPath}:`, error);
  }
  
  return size;
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Analyze Next.js build output
 */
function analyzeNextBuild(): BundleAnalysis {
  console.log('🔍 Analyzing Next.js bundle...\n');
  
  const buildDir = path.join(process.cwd(), '.next');
  const staticDir = path.join(buildDir, 'static');
  
  if (!fs.existsSync(buildDir)) {
    throw new Error('Build directory not found. Run "npm run build" first.');
  }
  
  // Get total size
  const totalSize = getDirSize(staticDir);
  
  // Analyze chunks
  const chunksDir = path.join(staticDir, 'chunks');
  const chunks: BundleAnalysis['chunks'] = [];
  
  if (fs.existsSync(chunksDir)) {
    const chunkFiles = fs.readdirSync(chunksDir).filter(f => f.endsWith('.js'));
    
    chunkFiles.forEach((file) => {
      const filePath = path.join(chunksDir, file);
      const stats = fs.statSync(filePath);
      
      // Estimate gzipped size (roughly 30% of original)
      const gzipped = Math.round(stats.size * 0.3);
      
      chunks.push({
        name: file,
        size: stats.size,
        gzipped,
      });
    });
  }
  
  // Sort chunks by size
  chunks.sort((a, b) => b.size - a.size);
  
  // Generate recommendations
  const recommendations: string[] = [];
  const totalGzipped = Math.round(totalSize * 0.3);
  
  if (totalGzipped > THRESHOLDS.INITIAL_BUNDLE) {
    recommendations.push(
      `⚠️  Total bundle size (${formatBytes(totalGzipped)} gzipped) exceeds recommended ${formatBytes(THRESHOLDS.INITIAL_BUNDLE)}`,
    );
    recommendations.push('Consider code splitting or lazy loading');
  }
  
  const largeChunks = chunks.filter(c => c.gzipped > THRESHOLDS.CHUNK);
  if (largeChunks.length > 0) {
    recommendations.push(
      `⚠️  ${largeChunks.length} chunk(s) exceed ${formatBytes(THRESHOLDS.CHUNK)} gzipped`,
    );
    recommendations.push(`Large chunks: ${largeChunks.map(c => c.name).join(', ')}`);
  }
  
  // Check for common optimization opportunities
  const hasLargeVendorChunk = chunks.some(c => 
    c.name.includes('vendor') && c.gzipped > THRESHOLDS.WARNING,
  );
  
  if (hasLargeVendorChunk) {
    recommendations.push('💡 Consider splitting vendor chunk into smaller chunks');
  }
  
  // Recommendations for specific libraries
  const potentialOptimizations = [
    { lib: 'moment', recommendation: 'Replace moment.js with date-fns or dayjs' },
    { lib: 'lodash', recommendation: 'Use lodash-es with tree shaking' },
    { lib: '@material-ui', recommendation: 'Use individual imports instead of full package' },
  ];
  
  potentialOptimizations.forEach(({ lib, recommendation }) => {
    const hasLib = chunks.some(c => c.name.includes(lib));
    if (hasLib) {
      recommendations.push(`💡 ${recommendation}`);
    }
  });
  
  return {
    timestamp: new Date().toISOString(),
    totalSize,
    gzippedSize: totalGzipped,
    chunks: chunks.slice(0, 10), // Top 10 chunks
    largestDependencies: [],
    recommendations,
  };
}

/**
 * Print analysis report
 */
function printReport(analysis: BundleAnalysis): void {
  console.log('📊 Bundle Analysis Report');
  console.log('='.repeat(60));
  console.log(`Timestamp: ${analysis.timestamp}\n`);
  
  console.log('📦 Bundle Size:');
  console.log(`  Total: ${formatBytes(analysis.totalSize)}`);
  console.log(`  Gzipped: ${formatBytes(analysis.gzippedSize)}`);
  
  const percentage = (analysis.gzippedSize / THRESHOLDS.INITIAL_BUNDLE) * 100;
  console.log(`  Budget: ${percentage.toFixed(1)}% of ${formatBytes(THRESHOLDS.INITIAL_BUNDLE)}\n`);
  
  if (analysis.chunks.length > 0) {
    console.log('📄 Top 10 Largest Chunks:');
    analysis.chunks.forEach((chunk, index) => {
      const indicator = chunk.gzipped > THRESHOLDS.CHUNK ? '⚠️ ' : '✅ ';
      console.log(
        `  ${indicator}${index + 1}. ${chunk.name}: ${formatBytes(chunk.size)} (${formatBytes(chunk.gzipped)} gzipped)`,
      );
    });
    console.log('');
  }
  
  if (analysis.recommendations.length > 0) {
    console.log('💡 Recommendations:');
    analysis.recommendations.forEach((rec) => {
      console.log(`  ${rec}`);
    });
    console.log('');
  } else {
    console.log('✅ No optimization recommendations. Bundle size looks good!\n');
  }
  
  console.log('='.repeat(60));
}

/**
 * Save analysis to file
 */
function saveAnalysis(analysis: BundleAnalysis): void {
  const outputDir = path.join(process.cwd(), 'reports');
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const outputFile = path.join(outputDir, 'bundle-analysis.json');
  fs.writeFileSync(outputFile, JSON.stringify(analysis, null, 2));
  
  console.log(`📁 Analysis saved to: ${outputFile}\n`);
}

/**
 * Run bundle analysis with Next.js analyzer
 */
function runNextAnalyzer(): void {
  console.log('🔧 Running Next.js bundle analyzer...\n');
  
  try {
    execSync('ANALYZE=true npm run build', {
      stdio: 'inherit',
      env: { ...process.env, ANALYZE: 'true' },
    });
    
    console.log('\n✅ Bundle analyzer complete. Check .next/analyze/ for detailed reports.\n');
  } catch (error) {
    console.error('❌ Failed to run bundle analyzer:', error);
  }
}

/**
 * Main execution
 */
function main(): void {
  const args = process.argv.slice(2);
  const useAnalyzer = args.includes('--analyze');
  
  if (useAnalyzer) {
    runNextAnalyzer();
  } else {
    const analysis = analyzeNextBuild();
    printReport(analysis);
    saveAnalysis(analysis);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

export { analyzeNextBuild, printReport, saveAnalysis };
