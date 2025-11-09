import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Script from 'next/script';
import { Toaster } from 'sonner';

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
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Prevent flash of wrong theme */}
        <Script
          id="theme-init"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: getThemeInitScript(),
          }}
        />
      </head>
      <body
        className={`${inter.variable} font-sans antialiased bg-neutral-50 dark:bg-neutral-900 min-h-screen`}
      >
        <Providers>
          {/* 
            PageTransition wraps the app with AnimatePresence to provide smooth
            transitions between routes. It automatically detects route changes
            via usePathname and animates page content with fade and slide effects.
          */}
          <PageTransition>
            <Layout>{children}</Layout>
          </PageTransition>
        </Providers>
        <Toaster position="top-right" richColors closeButton />
      </body>
    </html>
  );
}
