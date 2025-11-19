import { act, renderHook, waitFor } from '@testing-library/react';

import { useWebSocket } from '@/hooks/useWebSocket';

class MockWebSocket {
    static instances: MockWebSocket[] = [];
    onopen: (() => void) | null = null;
    onclose: (() => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;

    constructor(public url: string) {
        MockWebSocket.instances.push(this);
    }

    close() {
        if (this.onclose) this.onclose();
    }

    receive(data: any) {
        if (this.onmessage) this.onmessage({ data: JSON.stringify(data) } as MessageEvent);
    }
}

describe('useWebSocket', () => {
    beforeEach(() => {
        MockWebSocket.instances = [];
        // @ts-expect-error override global
        global.WebSocket = MockWebSocket;
    });

    it('tracks connection status on open and close', async () => {
        const { result, unmount } = renderHook(() =>
            useWebSocket('ws://localhost:8002/ws', jest.fn(), jest.fn(), jest.fn()),
        );

        // Initially closed before the effect runs
        expect(result.current.connectionStatus).toBe('closed');

        const instance = MockWebSocket.instances[0];
        await act(async () => {
            instance.onopen && instance.onopen();
        });
        await waitFor(() => expect(result.current.connectionStatus).toBe('open'));

        await act(async () => {
            instance.close();
        });
        await waitFor(() => expect(result.current.connectionStatus).toBe('closed'));

        unmount();
    });

    it('dispatches messages to the correct handlers', () => {
        const dashboardHandler = jest.fn();
        const applicationHandler = jest.fn();
        const analyticsHandler = jest.fn();

        renderHook(() =>
            useWebSocket('ws://localhost:8002/ws', dashboardHandler, applicationHandler, analyticsHandler),
        );

        const instance = MockWebSocket.instances[0];

        instance.receive({ type: 'dashboard-update', payload: { foo: 'bar' } });
        expect(dashboardHandler).toHaveBeenCalledWith({ foo: 'bar' });

        instance.receive({ type: 'application-status-update', payload: { id: 1 } });
        expect(applicationHandler).toHaveBeenCalledWith({ id: 1 });

        instance.receive({ type: 'analytics-update', payload: { value: 42 } });
        expect(analyticsHandler).toHaveBeenCalledWith({ value: 42 });
    });
});
