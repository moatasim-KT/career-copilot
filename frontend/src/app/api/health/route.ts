import { NextRequest, NextResponse } from 'next/server';

let jsErrors: Array<{ message: string; timestamp: string }> = [];
let renderTimes: { [path: string]: number } = {};

export async function GET(req: NextRequest) {
  const path = req.nextUrl.pathname;

  // Handle different health check endpoints
  switch (path) {
    case '/_health/render':
      return handleRenderCheck();
    case '/_health/js-errors':
      return handleJsErrorCheck();
    default:
      return handleBasicHealthCheck();
  }
}

export async function POST(req: NextRequest) {
  const path = req.nextUrl.pathname;

  if (path === '/_health/js-errors') {
    return handleJsErrorReport(req);
  }

  return NextResponse.json({ error: 'Not found' }, { status: 404 });
}

async function handleBasicHealthCheck() {
  try {
    const start = performance.now();

    // Check if we can access essential runtime features
    const runtimeCheck =
      typeof window !== 'undefined' &&
      typeof document !== 'undefined' &&
      typeof fetch !== 'undefined';

    const health = {
      status: runtimeCheck ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      js_errors_count: jsErrors.length,
      recent_render_times: renderTimes,
      runtime: {
        nextjs: process.env.NEXT_RUNTIME,
        node: process.version,
      },
    };

    const response_time = performance.now() - start;

    return NextResponse.json({
      ...health,
      response_time_ms: response_time,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}

async function handleRenderCheck() {
  const start = performance.now();

  try {
    // Simulate minimal page rendering
    const testElement =
      typeof document !== 'undefined' ? document.createElement('div') : null;

    if (testElement) {
      testElement.innerHTML = '<p>Test render</p>';
    }

    const renderTime = performance.now() - start;

    return NextResponse.json({
      rendered: true,
      render_time_ms: renderTime,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        rendered: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}

async function handleJsErrorCheck() {
  // Return recent JS errors (last 24 hours)
  const oneDayAgo = new Date();
  oneDayAgo.setDate(oneDayAgo.getDate() - 1);

  const recentErrors = jsErrors.filter(error => new Date(error.timestamp) > oneDayAgo);

  return NextResponse.json({
    errors: recentErrors,
    total_count: jsErrors.length,
    recent_count: recentErrors.length,
    timestamp: new Date().toISOString(),
  });
}

async function handleJsErrorReport(req: NextRequest) {
  try {
    const body = await req.json();

    // Add new error with timestamp
    jsErrors.push({
      message: body.error || 'Unknown error',
      timestamp: new Date().toISOString(),
    });

    // Keep only last 1000 errors
    if (jsErrors.length > 1000) {
      jsErrors = jsErrors.slice(-1000);
    }

    return NextResponse.json({
      status: 'recorded',
      total_errors: jsErrors.length,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 400 },
    );
  }
}

// Export the routes
export const GET_health = GET;
export const POST_health = POST;
