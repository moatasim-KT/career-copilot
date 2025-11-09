import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'sonner';
import Script from 'next/script';

import Layout from '@/components/layout/Layout';
import PageTransition from '@/components/layout/PageTransition';
import { getThemeInitScript } from '@/hooks/useDarkMode';

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
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Prevent flash of wrong theme */}
        <Script
          id="theme-init"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: getThemeInitScript()
          }}
        />
      </head>
      <body
        className={`${inter.variable} font-sans antialiased bg-neutral-50 dark:bg-neutral-900 min-h-screen`}
      >
        <Providers>
          {/* PageTransition is a client component that handles AnimatePresence/motion */}
          <PageTransition>
            <Layout>{children}</Layout>
          </PageTransition>
        </Providers>
        {/* Loading indicator placeholder for route transitions */}
        {/* <div id="page-loading-indicator" /> */}
        <Toaster position="top-right" richColors closeButton />
      </body>
    </html>
  );
}
