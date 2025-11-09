import { AnimatePresence, motion } from 'framer-motion';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'sonner';

import Layout from '@/components/layout/Layout';
import { pageTransition } from '@/lib/animations';

import Providers from './providers';
import './globals.css';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Career Copilot - AI-Powered Job Application Tracking',
  description: 'Track your job applications, get personalized recommendations, and analyze your job search progress with AI-powered insights.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Note: usePathname only works in client components, so this is a placeholder for actual implementation.
  // In a real Next.js app, page transitions are best handled in a client component wrapper.
  // Here, we show the pattern for AnimatePresence and motion.div usage.
  return (
    <html lang="en">
      <body
        className={`${inter.variable} font-sans antialiased bg-gray-50 min-h-screen`}
      >
        <Providers>
          <AnimatePresence mode="wait">
            {/*
              In a real app, use a key based on route (e.g., pathname) to trigger transitions.
              This is a static example; for dynamic transitions, move this logic to a client component.
            */}
            <motion.div
              key="page"
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
              style={{ minHeight: '100vh' }}
            >
              <Layout>{children}</Layout>
            </motion.div>
          </AnimatePresence>
        </Providers>
        {/* Loading indicator placeholder for route transitions */}
        {/* <div id="page-loading-indicator" /> */}
        <Toaster position="top-right" richColors closeButton />
      </body>
    </html>
  );
}
