'use client';

import { useState } from 'react';

import { OptimizedImage, OptimizedAvatar, OptimizedThumbnail, RESPONSIVE_SIZES } from '@/components/ui/OptimizedImage';

/**
 * Responsive Images Demo Page
 * 
 * This page demonstrates all responsive image contexts and patterns.
 * Resize your browser window to see different image sizes being loaded.
 */
export default function ResponsiveImagesDemo() {
  const [showSizes, setShowSizes] = useState(false);

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 py-12 px-4">
      <div className="max-w-7xl mx-auto space-y-16">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">Responsive Images Demo</h1>
          <p className="text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
            This page demonstrates responsive image loading. Open DevTools Network tab and resize your browser to see different image sizes being loaded.
          </p>
          <button
            onClick={() => setShowSizes(!showSizes)}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            {showSizes ? 'Hide' : 'Show'} Sizes Configuration
          </button>
        </div>

        {/* Sizes Reference */}
        {showSizes && (
          <div className="bg-white dark:bg-neutral-900 rounded-lg p-6 border border-neutral-200 dark:border-neutral-800">
            <h2 className="text-2xl font-bold mb-4">Available Responsive Contexts</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(RESPONSIVE_SIZES).map(([key, value]) => (
                <div key={key} className="p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                  <div className="font-mono font-semibold text-primary-600 dark:text-primary-400 mb-2">
                    {key}
                  </div>
                  <div className="text-sm text-neutral-600 dark:text-neutral-400 break-all">
                    {value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Hero Context */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Hero Context</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            Full width on mobile, half on tablet, third on desktop
          </p>
          <div className="relative w-full h-96 rounded-lg overflow-hidden">
            <OptimizedImage
              src="/images/placeholder.svg"
              alt="Hero image"
              fill
              objectFit="cover"
              responsiveContext="hero"
              priority
            />
            <div className="absolute inset-0 bg-gradient-to-r from-black/60 to-transparent flex items-center">
              <div className="text-white px-8">
                <h3 className="text-3xl font-bold mb-2">Hero Image</h3>
                <p className="text-sm opacity-90">responsiveContext=&quot;hero&quot;</p>
              </div>
            </div>
          </div>
        </section>

        {/* Card Context */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Card Context</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            Full width on mobile, 50% on larger screens
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white dark:bg-neutral-900 rounded-lg overflow-hidden border border-neutral-200 dark:border-neutral-800">
                <div className="relative w-full h-48">
                  <OptimizedImage
                    src="/images/placeholder.svg"
                    alt={`Card ${i}`}
                    fill
                    objectFit="cover"
                    responsiveContext="card"
                  />
                </div>
                <div className="p-4">
                  <h3 className="text-lg font-semibold mb-2">Card {i}</h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    Using responsiveContext=&quot;card&quot;
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Grid Context */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Grid Context</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            2 columns on mobile, 3 on tablet, 4 on desktop
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="relative aspect-square rounded-lg overflow-hidden">
                <OptimizedImage
                  src="/images/placeholder.svg"
                  alt={`Grid item ${i}`}
                  fill
                  objectFit="cover"
                  responsiveContext="grid"
                />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                  <span className="text-white font-semibold">{i}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Banner Context */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Banner Context</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            Full width on mobile, 80% on tablet, max 1200px on desktop
          </p>
          <div className="relative w-full h-64 rounded-lg overflow-hidden">
            <OptimizedImage
              src="/images/placeholder.svg"
              alt="Banner"
              fill
              objectFit="cover"
              responsiveContext="banner"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
              <div className="text-white p-8">
                <h3 className="text-2xl font-bold mb-2">Banner Image</h3>
                <p className="text-sm opacity-90">responsiveContext=&quot;banner&quot;</p>
              </div>
            </div>
          </div>
        </section>

        {/* Content Context */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Content Context</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            For images within article content
          </p>
          <div className="max-w-3xl mx-auto bg-white dark:bg-neutral-900 rounded-lg p-8 border border-neutral-200 dark:border-neutral-800">
            <h3 className="text-xl font-semibold mb-4">Article Title</h3>
            <p className="text-neutral-600 dark:text-neutral-400 mb-6">
              This is an example of an article with an embedded image using the content responsive context.
              The image will adapt to different screen sizes appropriately.
            </p>
            <div className="relative w-full h-96 rounded-lg overflow-hidden my-6">
              <OptimizedImage
                src="/images/placeholder.svg"
                alt="Content image"
                fill
                objectFit="cover"
                responsiveContext="content"
              />
            </div>
            <p className="text-neutral-600 dark:text-neutral-400">
              The image automatically adapts using the &quot;content&quot; preset which is optimized for article layouts.
            </p>
          </div>
        </section>

        {/* Avatars */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Avatars</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            Fixed small sizes optimized for profile images
          </p>
          <div className="flex flex-wrap gap-4 items-center">
            <OptimizedAvatar
              src="/images/default-avatar.svg"
              alt="User 1"
              size={24}
            />
            <OptimizedAvatar
              src="/images/default-avatar.svg"
              alt="User 2"
              size={32}
            />
            <OptimizedAvatar
              src="/images/default-avatar.svg"
              alt="User 3"
              size={40}
            />
            <OptimizedAvatar
              src="/images/default-avatar.svg"
              alt="User 4"
              size={48}
            />
            <OptimizedAvatar
              src="/images/default-avatar.svg"
              alt="User 5"
              size={64}
            />
            <OptimizedAvatar
              src="/images/default-avatar.svg"
              alt="User 6"
              size={80}
            />
          </div>
        </section>

        {/* Thumbnails */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Thumbnails</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            Fixed small sizes for image previews
          </p>
          <div className="flex flex-wrap gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <OptimizedThumbnail
                key={i}
                src="/images/placeholder.svg"
                alt={`Thumbnail ${i}`}
                size={100}
              />
            ))}
          </div>
        </section>

        {/* Custom Sizes */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Custom Sizes</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            You can also provide custom sizes for specific layouts
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="relative w-full h-96 rounded-lg overflow-hidden">
                <OptimizedImage
                  src="/images/placeholder.svg"
                  alt="Main content"
                  fill
                  objectFit="cover"
                  sizes="(max-width: 1024px) 100vw, 66vw"
                />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                  <div className="text-white text-center">
                    <p className="text-sm mb-2">Custom Sizes</p>
                    <p className="text-xs opacity-80">(max-width: 1024px) 100vw, 66vw</p>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <div className="relative w-full h-96 rounded-lg overflow-hidden">
                <OptimizedImage
                  src="/images/placeholder.svg"
                  alt="Sidebar"
                  fill
                  objectFit="cover"
                  sizes="(max-width: 1024px) 100vw, 33vw"
                />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                  <div className="text-white text-center px-4">
                    <p className="text-sm mb-2">Sidebar</p>
                    <p className="text-xs opacity-80">(max-width: 1024px) 100vw, 33vw</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Testing Instructions */}
        <section className="bg-blue-50 dark:bg-blue-950 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
          <h2 className="text-2xl font-bold mb-4 text-blue-900 dark:text-blue-100">
            Testing Instructions
          </h2>
          <ol className="list-decimal list-inside space-y-2 text-blue-800 dark:text-blue-200">
            <li>Open Chrome DevTools (F12)</li>
            <li>Go to the Network tab</li>
            <li>Filter by &quot;Img&quot; to see only images</li>
            <li>Clear the network log</li>
            <li>Resize your browser window</li>
            <li>Reload the page</li>
            <li>Observe which image sizes are loaded for different viewport widths</li>
            <li>Check the &quot;Size&quot; column to see actual file sizes</li>
            <li>Verify WebP or AVIF format is being served (check &quot;Type&quot; column)</li>
          </ol>
        </section>

        {/* Performance Tips */}
        <section className="bg-green-50 dark:bg-green-950 rounded-lg p-6 border border-green-200 dark:border-green-800">
          <h2 className="text-2xl font-bold mb-4 text-green-900 dark:text-green-100">
            Performance Tips
          </h2>
          <ul className="list-disc list-inside space-y-2 text-green-800 dark:text-green-200">
            <li>Always use the <code className="bg-green-100 dark:bg-green-900 px-1 rounded">sizes</code> prop with <code className="bg-green-100 dark:bg-green-900 px-1 rounded">fill</code> images</li>
            <li>Use <code className="bg-green-100 dark:bg-green-900 px-1 rounded">priority</code> for above-the-fold images</li>
            <li>Choose appropriate responsive contexts for your layout</li>
            <li>Test on real devices with throttled network</li>
            <li>Monitor image load times in production</li>
            <li>Compress source images before uploading</li>
            <li>Use WebP/AVIF formats (automatic with Next.js Image)</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
