import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'sonner';

import Layout from '@/components/layout/Layout';
import PageTransition from '@/components/layout/PageTransition';
import WebVitalsReporter from '@/components/WebVitalsReporter';

import Providers from './providers';
import './globals.css';

import { validateEnvironmentVariables } from '@/scripts/validate-env';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap',
});

validateEnvironmentVariables();

export const metadata: Metadata = {
  title: 'Career Copilot - AI-Powered Job Application Tracking',
  description: 'Track your job applications, get personalized recommendations, and analyze your job search progress with AI-powered insights.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full">
      <body
        className={`${inter.variable} font-sans antialiased bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 min-h-full`}
        suppressHydrationWarning
      >
        {/* Prevent flash of wrong theme - moved to body to avoid hydration issues */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const theme = localStorage.getItem('theme') || 'system';
                  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                  if (isDark) {
                    document.documentElement.classList.add('dark');
                  }
                  document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
                } catch (e) {}
              })();
            `,
          }}
        />
        <Providers>
          <WebVitalsReporter />
          <PageTransition>
            <Layout>{children}</Layout>
          </PageTransition>
        </Providers>
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700',
          }}
          closeButton
          richColors
        />
      </body>
    </html>
  );
}
