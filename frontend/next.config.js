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
    formats: ['image/webp', 'image/avif'],
    
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
    
    // Cache optimized images for 60 seconds
    minimumCacheTTL: 60,
    
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
  
  // Webpack configuration for bundle size monitoring
  webpack: (config, { isServer, webpack }) => {
    // Add bundle size plugin
    if (!isServer) {
      config.plugins.push(
        new webpack.optimize.LimitChunkCountPlugin({
          maxChunks: 1,
        })
      );
    }
    
    // Performance hints
    config.performance = {
      ...config.performance,
      hints: process.env.NODE_ENV === 'production' ? 'error' : false,
      maxAssetSize: 250000, // 250KB error threshold
      maxEntrypointSize: 250000, // 250KB error threshold
    };
    
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
