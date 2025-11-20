import { renderHook } from '@testing-library/react';

import { useKeyboardShortcut, getShortcutString } from '@/hooks/useKeyboardShortcut';

jest.mock('@/lib/keyboardShortcuts', () => {
    const registrations: any[] = [];
    return {
        useKeyboardShortcut: (config: any) => {
            registrations.push(config);
        },
        __getRegistrations: () => registrations,
        __clearRegistrations: () => {
            registrations.length = 0;
        },
    };
});

const keyboardShortcutsLib = require('@/lib/keyboardShortcuts');

describe('useKeyboardShortcut', () => {
    it('does not crash when navigator is undefined (SSR-safe)', () => {
        const originalNavigator = (global as any).navigator;
        // simulate SSR environment - navigator may be undefined
        delete (global as any).navigator;

        const callback = jest.fn();
        renderHook(() => useKeyboardShortcut('k', callback, { meta: true, ctrl: true }));

        (global as any).navigator = originalNavigator;
    });

    it('maps ctrl+meta to primary modifier on Mac', () => {
        const originalNavigator = (global as any).navigator;
        (global as any).navigator = { platform: 'MacIntel' } as any;

        keyboardShortcutsLib.__clearRegistrations();
        const callback = jest.fn();
        renderHook(() => useKeyboardShortcut('k', callback, { meta: true, ctrl: true }));

        const regs = keyboardShortcutsLib.__getRegistrations();
        expect(regs).toHaveLength(1);
        expect(regs[0].ctrl).toBe(false);
        expect(regs[0].meta).toBe(true);

        (global as any).navigator = originalNavigator;
    });

    it('maps ctrl+meta to Ctrl on non-Mac', () => {
        const originalNavigator = (global as any).navigator;
        (global as any).navigator = { platform: 'Win32' } as any;

        keyboardShortcutsLib.__clearRegistrations();
        const callback = jest.fn();
        renderHook(() => useKeyboardShortcut('k', callback, { meta: true, ctrl: true }));

        const regs = keyboardShortcutsLib.__getRegistrations();
        expect(regs).toHaveLength(1);
        expect(regs[0].ctrl).toBe(true);
        expect(regs[0].meta).toBe(false);

        (global as any).navigator = originalNavigator;
    });
});

describe('getShortcutString', () => {
    it('formats shortcut string for Mac vs non-Mac', () => {
        const originalNavigator = (global as any).navigator;

        (global as any).navigator = { platform: 'MacIntel' } as any;
        expect(getShortcutString('k', { meta: true, ctrl: true })).toBe('⌘K');

        (global as any).navigator = { platform: 'Win32' } as any;
        expect(getShortcutString('k', { meta: true, ctrl: true })).toBe('Ctrl+K');

        (global as any).navigator = originalNavigator;
    });
});
