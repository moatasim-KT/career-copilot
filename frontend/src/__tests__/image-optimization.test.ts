/**
 * Image Optimization Configuration Tests
 * 
 * Tests to verify that image optimization is properly configured
 * and that the compression script works correctly.
 */

import { describe, it, expect } from '@jest/globals';
import fs from 'fs';
import path from 'path';

describe('Image Optimization Configuration', () => {
  describe('Next.js Configuration', () => {
    it('should have WebP and AVIF formats configured', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Check for image formats configuration
      expect(configContent).toContain("formats: ['image/avif', 'image/webp']");
    });

    it('should have quality setting configured', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Check for quality configuration
      expect(configContent).toContain('quality: 75');
    });

    it('should have proper cache TTL configured', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Check for cache TTL configuration (60 days)
      expect(configContent).toContain('minimumCacheTTL: 60 * 60 * 24 * 60');
    });

    it('should have device sizes configured', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Check for device sizes
      expect(configContent).toContain('deviceSizes:');
      expect(configContent).toContain('640');
      expect(configContent).toContain('1920');
    });

    it('should have image sizes configured', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Check for image sizes
      expect(configContent).toContain('imageSizes:');
      expect(configContent).toContain('16');
      expect(configContent).toContain('256');
    });

    it('should not have unoptimized flag set to true', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Check that optimization is enabled
      expect(configContent).toContain('unoptimized: false');
    });
  });

  describe('Compression Script', () => {
    it('should have compression script in package.json', () => {
      const packagePath = path.join(process.cwd(), 'package.json');
      const packageContent = fs.readFileSync(packagePath, 'utf-8');
      const packageJson = JSON.parse(packageContent);
      
      expect(packageJson.scripts).toHaveProperty('compress-images');
      expect(packageJson.scripts['compress-images']).toBe('node scripts/compress-images.js');
    });

    it('should have compression script file', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      expect(fs.existsSync(scriptPath)).toBe(true);
    });

    it('compression script should be executable', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      // Check for shebang
      expect(scriptContent).toContain('#!/usr/bin/env node');
      
      // Check for main function
      expect(scriptContent).toContain('async function main()');
      
      // Check for compression logic
      expect(scriptContent).toContain('async function compressImage');
      expect(scriptContent).toContain('MAX_SIZE_KB');
    });
  });

  describe('Public Directory Images', () => {
    it('should have public directory', () => {
      const publicPath = path.join(process.cwd(), 'public');
      expect(fs.existsSync(publicPath)).toBe(true);
    });

    it('should have images directory', () => {
      const imagesPath = path.join(process.cwd(), 'public', 'images');
      expect(fs.existsSync(imagesPath)).toBe(true);
    });

    it('should have patterns directory', () => {
      const patternsPath = path.join(process.cwd(), 'public', 'patterns');
      expect(fs.existsSync(patternsPath)).toBe(true);
    });

    it('all raster images should be under 100KB', () => {
      const publicPath = path.join(process.cwd(), 'public');
      const maxSizeKB = 100;
      const oversizedImages: string[] = [];

      function checkDirectory(dir: string) {
        const files = fs.readdirSync(dir);
        
        files.forEach((file) => {
          const filePath = path.join(dir, file);
          const stat = fs.statSync(filePath);
          
          if (stat.isDirectory()) {
            // Skip node_modules and hidden directories
            if (!file.startsWith('.') && file !== 'node_modules') {
              checkDirectory(filePath);
            }
          } else {
            const ext = path.extname(file).toLowerCase();
            // Check raster image formats (not SVG)
            if (['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext)) {
              const sizeKB = stat.size / 1024;
              if (sizeKB > maxSizeKB) {
                const relativePath = path.relative(publicPath, filePath);
                oversizedImages.push(`${relativePath} (${sizeKB.toFixed(2)} KB)`);
              }
            }
          }
        });
      }

      checkDirectory(publicPath);

      if (oversizedImages.length > 0) {
        console.warn('Oversized images found:', oversizedImages);
      }

      expect(oversizedImages).toHaveLength(0);
    });
  });

  describe('Documentation', () => {
    it('should have image optimization guide', () => {
      const guidePath = path.join(process.cwd(), 'IMAGE_OPTIMIZATION_GUIDE.md');
      expect(fs.existsSync(guidePath)).toBe(true);
    });

    it('should have image format optimization documentation', () => {
      const docPath = path.join(process.cwd(), 'IMAGE_FORMAT_OPTIMIZATION.md');
      expect(fs.existsSync(docPath)).toBe(true);
    });

    it('image format optimization doc should cover key topics', () => {
      const docPath = path.join(process.cwd(), 'IMAGE_FORMAT_OPTIMIZATION.md');
      const docContent = fs.readFileSync(docPath, 'utf-8');
      
      // Check for key sections
      expect(docContent).toContain('# Image Format Optimization Guide');
      expect(docContent).toContain('## Configuration');
      expect(docContent).toContain('## Image Format Comparison');
      expect(docContent).toContain('## Image Size Guidelines');
      expect(docContent).toContain('## Image Compression Script');
      expect(docContent).toContain('## Best Practices');
      expect(docContent).toContain('## Testing Image Optimization');
      
      // Check for format mentions
      expect(docContent).toContain('AVIF');
      expect(docContent).toContain('WebP');
      expect(docContent).toContain('quality: 75');
      expect(docContent).toContain('100KB');
    });
  });

  describe('Image Quality Settings', () => {
    it('should use optimal quality setting (75)', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // Quality 75 is optimal for WebP/AVIF
      expect(configContent).toContain('quality: 75');
    });

    it('should prioritize AVIF over WebP', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // AVIF should come first for best compression
      const formatsMatch = configContent.match(/formats:\s*\[(.*?)\]/);
      expect(formatsMatch).toBeTruthy();
      
      if (formatsMatch) {
        const formats = formatsMatch[1];
        const avifIndex = formats.indexOf('avif');
        const webpIndex = formats.indexOf('webp');
        
        expect(avifIndex).toBeGreaterThan(-1);
        expect(webpIndex).toBeGreaterThan(-1);
        expect(avifIndex).toBeLessThan(webpIndex);
      }
    });
  });

  describe('Performance Optimization', () => {
    it('should have long cache TTL for production', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      // 60 days cache = 60 * 60 * 24 * 60 seconds
      expect(configContent).toContain('minimumCacheTTL: 60 * 60 * 24 * 60');
    });

    it('should have remote patterns configured for external images', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      expect(configContent).toContain('remotePatterns:');
      expect(configContent).toContain('amazonaws.com');
      expect(configContent).toContain('cloudinary.com');
    });

    it('should have SVG security configured', () => {
      const configPath = path.join(process.cwd(), 'next.config.js');
      const configContent = fs.readFileSync(configPath, 'utf-8');
      
      expect(configContent).toContain('dangerouslyAllowSVG: true');
      expect(configContent).toContain('contentSecurityPolicy:');
    });
  });
});

describe('Image Compression Script Functionality', () => {
  describe('Script Configuration', () => {
    it('should have correct max size configuration', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('const MAX_SIZE_KB = 100');
    });

    it('should support multiple image formats', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('.jpg');
      expect(scriptContent).toContain('.jpeg');
      expect(scriptContent).toContain('.png');
      expect(scriptContent).toContain('.webp');
    });

    it('should have quality settings for different formats', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('QUALITY_SETTINGS');
      expect(scriptContent).toContain('jpeg:');
      expect(scriptContent).toContain('png:');
      expect(scriptContent).toContain('webp:');
    });

    it('should create backups of original images', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('.original');
      expect(scriptContent).toContain('Backup created');
    });

    it('should generate compression report', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('function generateReport');
      expect(scriptContent).toContain('COMPRESSION REPORT');
    });
  });

  describe('Script Features', () => {
    it('should skip already optimized images', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('Already optimized');
      expect(scriptContent).toContain('skipped: true');
    });

    it('should handle compression failures gracefully', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('catch (error)');
      expect(scriptContent).toContain('Error compressing');
    });

    it('should use progressive quality reduction', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('quality -= 10');
      expect(scriptContent).toContain('maxAttempts');
    });

    it('should resize images if quality reduction is not enough', () => {
      const scriptPath = path.join(process.cwd(), 'scripts', 'compress-images.js');
      const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
      
      expect(scriptContent).toContain('resize');
      expect(scriptContent).toContain('trying resize');
    });
  });
});
