import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value || request.headers.get('Authorization')?.split(' ')[1];
  const { pathname } = request.nextUrl;

  // Allow access to login and register pages without authentication
  if (pathname === '/login' || pathname === '/register') {
    // If authenticated, redirect from login/register to dashboard
    if (token) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    return NextResponse.next();
  }

  // Protect all other routes
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*) ',
  ],
};
