import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/components/AuthProvider'; // Assuming you'll create this
import { Navbar } from '@/components/Navbar'; // Assuming you'll create this

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Career Copilot',
  description: 'AI-powered job application tracking and career management system',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <Navbar />
          <main className="pt-16">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
