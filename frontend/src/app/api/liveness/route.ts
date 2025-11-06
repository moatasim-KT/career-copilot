/**
 * Liveness Check Endpoint
 * 
 * Kubernetes-style liveness probe to determine if the application
 * process is alive and responsive.
 * 
 * @module app/api/liveness/route
 */

import { NextResponse } from 'next/server';

/**
 * GET /api/liveness
 * 
 * Returns liveness status for Kubernetes liveness probe
 * This is a simple check that the process is responsive
 */
export async function GET() {
    return NextResponse.json(
        {
            alive: true,
            timestamp: new Date().toISOString(),
            uptime: process.uptime ? process.uptime() : 0,
        },
        {
            status: 200,
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            },
        },
    );
}

/**
 * HEAD /api/liveness
 * 
 * Lightweight liveness check for load balancers
 */
export async function HEAD() {
    return new Response(null, {
        status: 200,
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
    });
}
