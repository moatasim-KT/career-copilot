import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUser } from '../useUser';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client= { createTestQueryClient() } >
  { children }
  </QueryClientProvider>
);

describe('useUser', () => {
  it('fetches user data successfully', async () => {
    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({
      id: '1',
      name: 'John Doe',
      email: 'john.doe@example.com',
      roles: ['user'],
    });
  });
});
