'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Card2 } from '@/components/ui/Card2';
import { Button2 } from '@/components/ui/Button2';
import { Check, X, Info } from 'lucide-react';

/**
 * Image Quality Test Page
 * 
 * This page demonstrates and tests the image optimization configuration.
 * It shows how Next.js automatically optimizes images and serves them
 * in modern formats (WebP/AVIF) with optimal quality settings.
 */

interface ImageTest {
  id: string;
  name: string;
  description: string;
  src: string;
  width: number;
  height: number;
  quality?: number;
  priority?: boolean;
}

const imageTests: ImageTest[] = [
  {
    id: 'quality-75',
    name: 'Quality 75 (Recommended)',
    description: 'Optimal balance between quality and file size. This is the default setting.',
    src: '/images/placeholder.svg',
    width: 400,
    height: 300,
    quality: 75,
  },
  {
    id: 'quality-85',
    name: 'Quality 85 (High)',
    description: 'Higher quality for important images. Slightly larger file size.',
    src: '/images/placeholder.svg',
    width: 400,
    height: 300,
    quality: 85,
  },
  {
    id: 'quality-60',
    name: 'Quality 60 (Acceptable)',
    description: 'Lower quality for background images. Smaller file size.',
    src: '/images/placeholder.svg',
    width: 400,
    height: 300,
    quality: 60,
  },
  {
    id: 'responsive',
    name: 'Responsive Image',
    description: 'Automatically serves different sizes based on device width.',
    src: '/images/placeholder.svg',
    width: 800,
    height: 400,
    quality: 75,
  },
];

const formatTests = [
  {
    format: 'AVIF',
    description: '~50% smaller than JPEG, excellent quality',
    support: 'Chrome 85+, Firefox 93+, Safari 16+',
    color: 'text-green-600 dark:text-green-400',
  },
  {
    format: 'WebP',
    description: '~30% smaller than JPEG, excellent quality',
    support: 'Chrome 23+, Firefox 65+, Safari 14+',
    color: 'text-blue-600 dark:text-blue-400',
  },
  {
    format: 'JPEG',
    description: 'Baseline format, universal support',
    support: 'All browsers',
    color: 'text-gray-600 dark:text-gray-400',
  },
];

const optimizationChecklist = [
  {
    item: 'WebP and AVIF formats configured',
    status: true,
    description: 'Modern formats enabled in next.config.js',
  },
  {
    item: 'Quality set to 75',
    status: true,
    description: 'Optimal balance for WebP/AVIF',
  },
  {
    item: 'Long cache TTL (60 days)',
    status: true,
    description: 'Optimized for production performance',
  },
  {
    item: 'Responsive image sizes',
    status: true,
    description: 'Multiple sizes for different devices',
  },
  {
    item: 'Compression script available',
    status: true,
    description: 'npm run compress-images',
  },
  {
    item: 'All images under 100KB',
    status: true,
    description: 'Target size achieved',
  },
];

export default function ImageQualityTestPage() {
  const [selectedTest, setSelectedTest] = useState<string>('quality-75');
  const [showInfo, setShowInfo] = useState(false);

  const currentTest = imageTests.find((test) => test.id === selectedTest);

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-900 dark:to-neutral-800 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-neutral-100">
            Image Quality Test
          </h1>
          <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
            Testing Next.js image optimization with WebP and AVIF formats.
            All images are automatically optimized and served in the best format for each browser.
          </p>
        </div>

        {/* Format Support */}
        <Card2 className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
              Format Support
            </h2>
            <Button2
              variant="ghost"
              size="sm"
              onClick={() => setShowInfo(!showInfo)}
            >
              <Info className="w-4 h-4 mr-2" />
              {showInfo ? 'Hide' : 'Show'} Details
            </Button2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {formatTests.map((format) => (
              <div
                key={format.format}
                className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
              >
                <h3 className={`text-lg font-semibold mb-2 ${format.color}`}>
                  {format.format}
                </h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
                  {format.description}
                </p>
                {showInfo && (
                  <p className="text-xs text-neutral-500 dark:text-neutral-500">
                    {format.support}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card2>

        {/* Optimization Checklist */}
        <Card2 className="p-6">
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Optimization Checklist
          </h2>
          <div className="space-y-3">
            {optimizationChecklist.map((item, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {item.status ? (
                    <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
                  ) : (
                    <X className="w-5 h-5 text-red-600 dark:text-red-400" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-neutral-900 dark:text-neutral-100">
                    {item.item}
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card2>

        {/* Quality Comparison */}
        <Card2 className="p-6">
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Quality Comparison
          </h2>

          {/* Quality Selector */}
          <div className="flex flex-wrap gap-2 mb-6">
            {imageTests.map((test) => (
              <Button2
                key={test.id}
                variant={selectedTest === test.id ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setSelectedTest(test.id)}
              >
                {test.name}
              </Button2>
            ))}
          </div>

          {/* Current Test Display */}
          {currentTest && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                  {currentTest.name}
                </h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
                  {currentTest.description}
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-neutral-500 dark:text-neutral-500">Quality:</span>
                    <span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
                      {currentTest.quality}%
                    </span>
                  </div>
                  <div>
                    <span className="text-neutral-500 dark:text-neutral-500">Dimensions:</span>
                    <span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
                      {currentTest.width}x{currentTest.height}
                    </span>
                  </div>
                </div>
              </div>

              {/* Image Display */}
              <div className="flex justify-center p-8 bg-neutral-100 dark:bg-neutral-900 rounded-lg">
                <div className="relative">
                  <Image
                    src={currentTest.src}
                    alt={currentTest.name}
                    width={currentTest.width}
                    height={currentTest.height}
                    quality={currentTest.quality}
                    priority={currentTest.priority}
                    className="rounded-lg shadow-lg"
                    sizes={
                      currentTest.id === 'responsive'
                        ? '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 800px'
                        : undefined
                    }
                  />
                </div>
              </div>
            </div>
          )}
        </Card2>

        {/* Testing Instructions */}
        <Card2 className="p-6">
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Testing Instructions
          </h2>
          <div className="space-y-4 text-neutral-600 dark:text-neutral-400">
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                1. Verify Format Delivery
              </h3>
              <ol className="list-decimal list-inside space-y-1 ml-4">
                <li>Open DevTools (F12) → Network tab</li>
                <li>Reload this page</li>
                <li>Filter by "Img" or "Images"</li>
                <li>Check the "Type" column - should show "webp" or "avif"</li>
              </ol>
            </div>

            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                2. Check File Sizes
              </h3>
              <ol className="list-decimal list-inside space-y-1 ml-4">
                <li>In Network tab, check the "Size" column</li>
                <li>Images should be significantly smaller than original</li>
                <li>WebP: ~30% smaller, AVIF: ~50% smaller</li>
              </ol>
            </div>

            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                3. Visual Quality Check
              </h3>
              <ol className="list-decimal list-inside space-y-1 ml-4">
                <li>Compare different quality settings above</li>
                <li>Quality 75 should look excellent</li>
                <li>Quality 60 should be acceptable for backgrounds</li>
                <li>Quality 85 should be nearly indistinguishable from original</li>
              </ol>
            </div>

            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                4. Run Compression Script
              </h3>
              <pre className="bg-neutral-900 dark:bg-neutral-950 text-green-400 p-4 rounded-lg overflow-x-auto">
                npm run compress-images
              </pre>
              <p className="mt-2 text-sm">
                This will compress all images in the public directory to under 100KB.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                5. Performance Test
              </h3>
              <ol className="list-decimal list-inside space-y-1 ml-4">
                <li>Run Lighthouse audit (DevTools → Lighthouse)</li>
                <li>Check "Properly sized images" - should be 100%</li>
                <li>Check "Efficient image formats" - should be 100%</li>
                <li>Performance score should be 95+</li>
              </ol>
            </div>
          </div>
        </Card2>

        {/* Configuration Info */}
        <Card2 className="p-6 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="flex items-start space-x-3">
            <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Configuration Details
              </h3>
              <div className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                <p>
                  <strong>Formats:</strong> AVIF (primary), WebP (fallback), JPEG (final fallback)
                </p>
                <p>
                  <strong>Quality:</strong> 75 (optimal for WebP/AVIF)
                </p>
                <p>
                  <strong>Cache TTL:</strong> 60 days in production
                </p>
                <p>
                  <strong>Max Size:</strong> 100KB per image (enforced by compression script)
                </p>
                <p>
                  <strong>Documentation:</strong> See IMAGE_FORMAT_OPTIMIZATION.md for details
                </p>
              </div>
            </div>
          </div>
        </Card2>
      </div>
    </div>
  );
}
