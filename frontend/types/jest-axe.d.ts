import type { AxeResults, RunOptions as AxeRunOptions } from 'axe-core';

declare module 'jest-axe' {
    const axe: (node: Element | DocumentFragment, options?: AxeRunOptions) => Promise<AxeResults>;
    const toHaveNoViolations: () => { pass: boolean; message(): string };
    const configureAxe: (options?: AxeRunOptions) => typeof axe;

    export { axe, configureAxe, toHaveNoViolations };
}

declare global {
    namespace jest {
        interface Matchers<R> {
            toHaveNoViolations(): R;
        }
    }
}
