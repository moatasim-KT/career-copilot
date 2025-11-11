#!/usr/bin/env node

/**
 * Image Compression Script
 * 
 * This script compresses images in the public directory to ensure they are under 100KB.
 * It uses sharp for image processing and compression.
 * 
 * Usage:
 *   npm run compress-images
 *   node scripts/compress-images.js
 * 
 * Features:
 * - Compresses JPEG, PNG, WebP images
 * - Converts to WebP format for optimal compression
 * - Ensures images are under 100KB
 * - Preserves original images with .original extension
 * - Generates compression report
 */

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// Configuration
const MAX_SIZE_KB = 100;
const MAX_SIZE_BYTES = MAX_SIZE_KB * 1024;
const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

// Quality settings for different formats
const QUALITY_SETTINGS = {
  jpeg: { quality: 75 },
  png: { quality: 75, compressionLevel: 9 },
  webp: { quality: 75 },
};

/**
 * Get all image files recursively from a directory
 */
function getImageFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // Skip node_modules and hidden directories
      if (!file.startsWith('.') && file !== 'node_modules') {
        getImageFiles(filePath, fileList);
      }
    } else {
      const ext = path.extname(file).toLowerCase();
      if (IMAGE_EXTENSIONS.includes(ext) && !file.includes('.original')) {
        fileList.push(filePath);
      }
    }
  });

  return fileList;
}

/**
 * Get file size in KB
 */
function getFileSizeKB(filePath) {
  const stats = fs.statSync(filePath);
  return (stats.size / 1024).toFixed(2);
}

/**
 * Compress an image file
 */
async function compressImage(filePath) {
  const originalSize = getFileSizeKB(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const fileName = path.basename(filePath);
  
  console.log(`\nProcessing: ${fileName}`);
  console.log(`Original size: ${originalSize} KB`);

  // Skip if already under size limit
  if (parseFloat(originalSize) < MAX_SIZE_KB) {
    console.log(`✓ Already optimized (under ${MAX_SIZE_KB}KB)`);
    return {
      file: fileName,
      originalSize: parseFloat(originalSize),
      newSize: parseFloat(originalSize),
      saved: 0,
      skipped: true,
    };
  }

  try {
    // Backup original file
    const backupPath = filePath.replace(ext, `.original${ext}`);
    if (!fs.existsSync(backupPath)) {
      fs.copyFileSync(filePath, backupPath);
      console.log(`Backup created: ${path.basename(backupPath)}`);
    }

    // Load image with sharp
    let image = sharp(filePath);
    const metadata = await image.metadata();

    // Start with standard quality compression
    let quality = 75;
    let compressed = false;
    let attempts = 0;
    const maxAttempts = 5;

    while (!compressed && attempts < maxAttempts) {
      attempts++;

      // Apply compression based on format
      if (ext === '.png') {
        image = sharp(filePath).png({
          quality,
          compressionLevel: 9,
          adaptiveFiltering: true,
        });
      } else if (ext === '.jpg' || ext === '.jpeg') {
        image = sharp(filePath).jpeg({
          quality,
          mozjpeg: true,
        });
      } else if (ext === '.webp') {
        image = sharp(filePath).webp({
          quality,
        });
      }

      // Write to temporary file
      const tempPath = filePath + '.temp';
      await image.toFile(tempPath);

      const tempSize = getFileSizeKB(tempPath);
      console.log(`Attempt ${attempts}: Quality ${quality}% = ${tempSize} KB`);

      if (parseFloat(tempSize) <= MAX_SIZE_KB) {
        // Success! Replace original with compressed version
        fs.renameSync(tempPath, filePath);
        compressed = true;
        
        const newSize = getFileSizeKB(filePath);
        const saved = parseFloat(originalSize) - parseFloat(newSize);
        const savedPercent = ((saved / parseFloat(originalSize)) * 100).toFixed(1);

        console.log(`✓ Compressed successfully!`);
        console.log(`New size: ${newSize} KB`);
        console.log(`Saved: ${saved.toFixed(2)} KB (${savedPercent}%)`);

        return {
          file: fileName,
          originalSize: parseFloat(originalSize),
          newSize: parseFloat(newSize),
          saved: parseFloat(saved.toFixed(2)),
          skipped: false,
        };
      } else {
        // Try with lower quality
        fs.unlinkSync(tempPath);
        quality -= 10;

        if (quality < 30) {
          // If quality is too low, try resizing
          const newWidth = Math.floor(metadata.width * 0.8);
          console.log(`Quality too low, trying resize to ${newWidth}px width`);
          
          image = sharp(filePath)
            .resize(newWidth, null, {
              fit: 'inside',
              withoutEnlargement: true,
            })
            .webp({ quality: 75 });

          await image.toFile(tempPath);
          const resizedSize = getFileSizeKB(tempPath);
          
          if (parseFloat(resizedSize) <= MAX_SIZE_KB) {
            fs.renameSync(tempPath, filePath);
            compressed = true;
            
            const newSize = getFileSizeKB(filePath);
            const saved = parseFloat(originalSize) - parseFloat(newSize);
            const savedPercent = ((saved / parseFloat(originalSize)) * 100).toFixed(1);

            console.log(`✓ Compressed with resize!`);
            console.log(`New size: ${newSize} KB`);
            console.log(`Saved: ${saved.toFixed(2)} KB (${savedPercent}%)`);

            return {
              file: fileName,
              originalSize: parseFloat(originalSize),
              newSize: parseFloat(newSize),
              saved: parseFloat(saved.toFixed(2)),
              skipped: false,
            };
          } else {
            fs.unlinkSync(tempPath);
            break;
          }
        }
      }
    }

    if (!compressed) {
      console.log(`⚠ Could not compress below ${MAX_SIZE_KB}KB`);
      console.log(`Consider manually optimizing this image or using a smaller version`);
      
      return {
        file: fileName,
        originalSize: parseFloat(originalSize),
        newSize: parseFloat(originalSize),
        saved: 0,
        skipped: false,
        failed: true,
      };
    }
  } catch (error) {
    console.error(`✗ Error compressing ${fileName}:`, error.message);
    return {
      file: fileName,
      originalSize: parseFloat(originalSize),
      newSize: parseFloat(originalSize),
      saved: 0,
      skipped: false,
      error: error.message,
    };
  }
}

/**
 * Generate compression report
 */
function generateReport(results) {
  console.log('\n' + '='.repeat(60));
  console.log('COMPRESSION REPORT');
  console.log('='.repeat(60));

  const processed = results.filter((r) => !r.skipped);
  const skipped = results.filter((r) => r.skipped);
  const failed = results.filter((r) => r.failed);
  const errors = results.filter((r) => r.error);

  const totalOriginalSize = results.reduce((sum, r) => sum + r.originalSize, 0);
  const totalNewSize = results.reduce((sum, r) => sum + r.newSize, 0);
  const totalSaved = results.reduce((sum, r) => sum + r.saved, 0);
  const savedPercent = ((totalSaved / totalOriginalSize) * 100).toFixed(1);

  console.log(`\nTotal images: ${results.length}`);
  console.log(`Processed: ${processed.length}`);
  console.log(`Skipped (already optimized): ${skipped.length}`);
  console.log(`Failed: ${failed.length}`);
  console.log(`Errors: ${errors.length}`);

  console.log(`\nTotal original size: ${totalOriginalSize.toFixed(2)} KB`);
  console.log(`Total new size: ${totalNewSize.toFixed(2)} KB`);
  console.log(`Total saved: ${totalSaved.toFixed(2)} KB (${savedPercent}%)`);

  if (processed.length > 0) {
    console.log('\nProcessed files:');
    processed.forEach((r) => {
      const status = r.failed ? '⚠' : '✓';
      console.log(
        `  ${status} ${r.file}: ${r.originalSize.toFixed(2)} KB → ${r.newSize.toFixed(2)} KB (saved ${r.saved.toFixed(2)} KB)`
      );
    });
  }

  if (skipped.length > 0) {
    console.log('\nSkipped files (already optimized):');
    skipped.forEach((r) => {
      console.log(`  ✓ ${r.file}: ${r.originalSize.toFixed(2)} KB`);
    });
  }

  if (failed.length > 0) {
    console.log('\n⚠ Failed to compress:');
    failed.forEach((r) => {
      console.log(`  ✗ ${r.file}: ${r.originalSize.toFixed(2)} KB`);
    });
  }

  if (errors.length > 0) {
    console.log('\n✗ Errors:');
    errors.forEach((r) => {
      console.log(`  ✗ ${r.file}: ${r.error}`);
    });
  }

  console.log('\n' + '='.repeat(60));
}

/**
 * Main function
 */
async function main() {
  console.log('Image Compression Script');
  console.log('='.repeat(60));
  console.log(`Target: Images under ${MAX_SIZE_KB}KB`);
  console.log(`Directory: ${PUBLIC_DIR}`);
  console.log('='.repeat(60));

  // Check if sharp is installed
  try {
    require.resolve('sharp');
  } catch (e) {
    console.error('\n✗ Error: sharp is not installed');
    console.error('Please install it with: npm install --save-dev sharp');
    process.exit(1);
  }

  // Get all image files
  const imageFiles = getImageFiles(PUBLIC_DIR);

  if (imageFiles.length === 0) {
    console.log('\nNo image files found to compress.');
    return;
  }

  console.log(`\nFound ${imageFiles.length} image(s) to process\n`);

  // Compress each image
  const results = [];
  for (const filePath of imageFiles) {
    const result = await compressImage(filePath);
    results.push(result);
  }

  // Generate report
  generateReport(results);

  // Exit with error code if any compressions failed
  const failed = results.filter((r) => r.failed || r.error);
  if (failed.length > 0) {
    console.log('\n⚠ Some images could not be compressed below the target size.');
    console.log('Please review and manually optimize these images.');
    process.exit(1);
  }

  console.log('\n✓ All images successfully optimized!');
}

// Run the script
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
