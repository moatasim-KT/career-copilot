'use client';

import { ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-neutral-950">
      <main className="flex-1 flex items-center justify-center">
        {children}
      </main>
    </div>
  );
}
