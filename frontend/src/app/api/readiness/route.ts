/**
 * Readiness Check Endpoint
 * 
 * Kubernetes-style readiness probe to determine if the application
 * is ready to accept traffic.
 * 
 * @module app/api/readiness/route
 */

import { NextResponse } from 'next/server';

interface ReadinessCheck {
    ready: boolean;
    timestamp: string;
    checks: {
        api: boolean;
        database: boolean;
        dependencies: boolean;
    };
}

/**
 * Quick API connectivity check
 */
async function checkAPIReadiness(): Promise<boolean> {
    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/health`, {
            method: 'HEAD',
            cache: 'no-store',
            signal: AbortSignal.timeout(2000), // 2 second timeout
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Check if essential environment variables are set
 */
function checkEnvironment(): boolean {
    const required = [
        'NEXT_PUBLIC_API_URL',
    ];

    return required.every((key) => !!process.env[key]);
}

/**
 * GET /api/readiness
 * 
 * Returns readiness status for Kubernetes readiness probe
 */
export async function GET() {
    try {
        const [apiReady, envReady] = await Promise.all([
            checkAPIReadiness(),
            Promise.resolve(checkEnvironment()),
        ]);

        const readiness: ReadinessCheck = {
            ready: apiReady && envReady,
            timestamp: new Date().toISOString(),
            checks: {
                api: apiReady,
                database: apiReady, // Implicit through API check
                dependencies: envReady,
            },
        };

        return NextResponse.json(readiness, {
            status: readiness.ready ? 200 : 503,
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            },
        });
    } catch (error) {
        return NextResponse.json(
            {
                ready: false,
                timestamp: new Date().toISOString(),
                error: error instanceof Error ? error.message : 'Unknown error',
            },
            {
                status: 503,
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                },
            },
        );
    }
}

/**
 * HEAD /api/readiness
 * 
 * Lightweight readiness check
 */
export async function HEAD() {
    const envReady = checkEnvironment();
    return new Response(null, {
        status: envReady ? 200 : 503,
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
    });
}
