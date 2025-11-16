'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import React, { ReactNode, useState, useEffect } from 'react';
import * as ReactDOM from 'react-dom';

import { CommandPaletteProvider } from '@/components/providers/CommandPaletteProvider';
import { AuthProvider } from '@/contexts/AuthContext';
import { NotificationProvider } from '@/contexts/NotificationContext';
import { createQueryClient } from '@/lib/queryClient';

// Accessibility audit (axe-core/react)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  import('@axe-core/react').then((axe) => {
    axe.default(React, ReactDOM, 1000);
  });
}

export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => createQueryClient());

  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
      // axe-core/react will already be loaded above
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <NotificationProvider>
          <CommandPaletteProvider>{children}</CommandPaletteProvider>
        </NotificationProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
