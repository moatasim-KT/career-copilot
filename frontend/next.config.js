const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  output: 'standalone', // Required for Docker deployment

  // Image optimization configuration
  images: {
    // Supported image formats - Next.js will automatically serve WebP/AVIF when supported
    // WebP: ~30% smaller than JPEG, excellent browser support
    // AVIF: ~50% smaller than JPEG, growing browser support
    formats: ['image/avif', 'image/webp'],

    // Device sizes for responsive images
    // These correspond to common device breakpoints and are used when you specify sizes prop
    // Example: sizes="(max-width: 640px) 100vw, 50vw"
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],

    // Image sizes for smaller images (icons, avatars, thumbnails)
    // Used for images that don't need full device width
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],

    // Enable image optimization in development for testing
    unoptimized: false,

    // Allowed domains for external images
    // Add any external image sources here
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: '**.cloudinary.com',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
      },
    ],

    // Cache optimized images for 60 days in production
    minimumCacheTTL: 60 * 60 * 24 * 60,

    // Allow SVG images (with security restrictions)
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",

    // Loader configuration for custom image optimization
    // Using default Next.js loader
    loader: 'default',
  },

  // Bundle size budgets
  // Warning threshold: 200KB per route
  // Error threshold: 250KB per route
  onDemandEntries: {
    // Period (in ms) where the server will keep pages in the buffer
    maxInactiveAge: 25 * 1000,
    // Number of pages that should be kept simultaneously without being disposed
    pagesBufferLength: 2,
  },

  // Experimental features for better bundle optimization
  experimental: {
    optimizePackageImports: [
      'lucide-react',
      'recharts',
      'framer-motion',
      '@tanstack/react-query',
      '@tanstack/react-table',
      '@dnd-kit/core',
      '@dnd-kit/sortable',
    ],
  },

  // Webpack configuration for bundle size monitoring and optimization
  webpack: (config, { isServer }) => {
    // Performance hints
    config.performance = {
      ...config.performance,
      hints: process.env.NODE_ENV === 'production' ? 'error' : false,
      maxAssetSize: 250000, // 250KB error threshold
      maxEntrypointSize: 250000, // 250KB error threshold
    };

    // Advanced code splitting for client bundles
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            // Default groups
            default: false,
            vendors: false,

            // Framework code (React, React DOM, Next.js)
            framework: {
              name: 'framework',
              test: /[\\/]node_modules[\\/](react|react-dom|scheduler|next)[\\/]/,
              priority: 50,
              enforce: true,
            },

            // Animation library - separate for better caching
            framerMotion: {
              name: 'framer-motion',
              test: /[\\/]node_modules[\\/]framer-motion[\\/]/,
              priority: 40,
              reuseExistingChunk: true,
            },

            // Charts library - lazy loaded but separate when used
            recharts: {
              name: 'recharts',
              test: /[\\/]node_modules[\\/](recharts|d3-[a-z]+)[\\/]/,
              priority: 40,
              reuseExistingChunk: true,
            },

            // Table library - lazy loaded but separate when used
            reactTable: {
              name: 'react-table',
              test: /[\\/]node_modules[\\/]@tanstack[\\/]react-table[\\/]/,
              priority: 40,
              reuseExistingChunk: true,
            },

            // Lucide icons - heavily used, separate for caching
            lucideReact: {
              name: 'lucide-react',
              test: /[\\/]node_modules[\\/]lucide-react[\\/]/,
              priority: 35,
              reuseExistingChunk: true,
            },

            // Other vendor libraries
            lib: {
              name: 'lib',
              test: /[\\/]node_modules[\\/]/,
              priority: 30,
              minChunks: 1,
              reuseExistingChunk: true,
            },

            // Common code used across multiple chunks
            commons: {
              name: 'commons',
              minChunks: 2,
              priority: 20,
              reuseExistingChunk: true,
            },

            // Shared UI components
            shared: {
              name: 'shared',
              test: /[\\/]src[\\/]components[\\/]ui[\\/]/,
              minChunks: 2,
              priority: 25,
              reuseExistingChunk: true,
            },
          },
        },
      };
    }

    return config;
  },
};

module.exports = withBundleAnalyzer(nextConfig);


// Injected content via Sentry wizard below

const { withSentryConfig } = require("@sentry/nextjs");

module.exports = withSentryConfig(
  module.exports,
  {
    // For all available options, see:
    // https://www.npmjs.com/package/@sentry/webpack-plugin#options

    org: "motive-ok",
    project: "javascript-nextjs",

    // Only print logs for uploading source maps in CI
    silent: !process.env.CI,

    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
    // This can increase your server load as well as your hosting bill.
    // Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
    // side errors will fail.
    tunnelRoute: "/monitoring",

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    disableLogger: true,

    // Enables automatic instrumentation of Vercel Cron Monitors. (Does not yet work with App Router route handlers.)
    // See the following for more information:
    // https://docs.sentry.io/product/crons/
    // https://vercel.com/docs/cron-jobs
    automaticVercelMonitors: true,
  }
);
