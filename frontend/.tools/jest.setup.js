import '@testing-library/jest-dom';
import 'jest-axe/extend-expect';

import { TextDecoder, TextEncoder } from 'util';

import 'whatwg-fetch';

// Polyfill for TextEncoder/TextDecoder in Jest environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// MSW setup removed for unit tests to avoid ReferenceError
// import { server } from './src/mocks/server';
// beforeAll(() => server.listen());
// afterEach(() => server.resetHandlers());
// afterAll(() => server.close());
