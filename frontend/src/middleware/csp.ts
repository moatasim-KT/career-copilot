/**
 * Content Security Policy Middleware
 * 
 * Enterprise-grade CSP implementation for protecting against XSS,
 * clickjacking, and other injection attacks.
 * 
 * @module middleware/csp
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Generate CSP nonce for inline scripts
 */
function generateNonce(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return Buffer.from(array).toString('base64');
}

/**
 * Build Content Security Policy header
 */
function buildCSP(nonce: string): string {
    const isDev = process.env.NODE_ENV === 'development';

    const cspDirectives = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            `'nonce-${nonce}'`,
            isDev ? "'unsafe-eval'" : '', // Required for React dev tools
            'https://cdn.vercel-insights.com',
            'https://va.vercel-scripts.com',
            'https://*.posthog.com',
            'https://*.sentry.io',
        ].filter(Boolean),
        'style-src': [
            "'self'",
            "'unsafe-inline'", // Required for CSS-in-JS
            'https://fonts.googleapis.com',
        ],
        'img-src': [
            "'self'",
            'data:',
            'blob:',
            'https:',
            'https://*.vercel.app',
        ],
        'font-src': [
            "'self'",
            'data:',
            'https://fonts.gstatic.com',
        ],
        'connect-src': [
            "'self'",
            process.env.NEXT_PUBLIC_API_URL || '',
            'https://*.vercel.app',
            'https://*.posthog.com',
            'https://*.sentry.io',
            'https://vitals.vercel-analytics.com',
        ].filter(Boolean),
        'frame-src': [
            "'self'",
            'https://www.youtube.com',
            'https://player.vimeo.com',
        ],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
        'frame-ancestors': ["'none'"], // Prevents clickjacking
        'upgrade-insecure-requests': isDev ? [] : [''],
    };

    return Object.entries(cspDirectives)
        .map(([key, values]) => {
            if (values.length === 0) return '';
            if (values[0] === '') return key; // For directives without values
            return `${key} ${values.join(' ')}`;
        })
        .filter(Boolean)
        .join('; ');
}

/**
 * Security headers middleware
 */
export function securityHeaders(_request: NextRequest) {
    const nonce = generateNonce();
    const response = NextResponse.next();

    // Content Security Policy
    response.headers.set('Content-Security-Policy', buildCSP(nonce));

    // Store nonce for use in app
    response.headers.set('X-CSP-Nonce', nonce);

    // Strict Transport Security
    if (process.env.NODE_ENV === 'production') {
        response.headers.set(
            'Strict-Transport-Security',
            'max-age=31536000; includeSubDomains; preload',
        );
    }

    // Prevent MIME type sniffing
    response.headers.set('X-Content-Type-Options', 'nosniff');

    // XSS Protection (legacy but still useful)
    response.headers.set('X-XSS-Protection', '1; mode=block');

    // Clickjacking protection
    response.headers.set('X-Frame-Options', 'DENY');

    // Referrer Policy
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

    // Permissions Policy (Feature Policy)
    response.headers.set(
        'Permissions-Policy',
        'camera=(), microphone=(), geolocation=(), interest-cohort=()',
    );

    // Cross-Origin Policies
    response.headers.set('Cross-Origin-Opener-Policy', 'same-origin');
    response.headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
    response.headers.set('Cross-Origin-Resource-Policy', 'same-origin');

    return response;
}

/**
 * Rate limiting headers
 */
export function rateLimitHeaders(response: NextResponse, limit: number, remaining: number, reset: number) {
    response.headers.set('X-RateLimit-Limit', limit.toString());
    response.headers.set('X-RateLimit-Remaining', remaining.toString());
    response.headers.set('X-RateLimit-Reset', reset.toString());
    return response;
}

/**
 * CORS headers for API routes
 */
export function corsHeaders(response: NextResponse, origin?: string) {
    const allowedOrigins = [
        process.env.NEXT_PUBLIC_APP_URL,
        'http://localhost:3000',
        'http://localhost:3001',
    ].filter(Boolean);

    if (origin && allowedOrigins.includes(origin)) {
        response.headers.set('Access-Control-Allow-Origin', origin);
    }

    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    response.headers.set('Access-Control-Max-Age', '86400'); // 24 hours

    return response;
}
