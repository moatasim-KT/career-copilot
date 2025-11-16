'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';

export default function OAuthCallbackPage({ params }: { params: { provider: string } }) {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { refreshUser } = useAuth();
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(true);

    useEffect(() => {
        const handleOAuthCallback = async () => {
            try {
                // The backend OAuth callback should have already set cookies/redirected
                // or returned tokens in URL params
                const token = searchParams.get('token');
                const errorParam = searchParams.get('error');

                if (errorParam) {
                    setError(decodeURIComponent(errorParam));
                    setIsProcessing(false);
                    return;
                }

                if (token) {
                    // Store token if provided in URL
                    localStorage.setItem('access_token', token);

                    // Fetch user details
                    await refreshUser();

                    // Redirect to dashboard
                    router.push('/dashboard');
                } else {
                    // Try to refresh user in case token was set via cookie
                    await refreshUser();
                    router.push('/dashboard');
                }
            } catch (err) {
                console.error('OAuth callback error:', err);
                setError('Failed to complete authentication. Please try again.');
                setIsProcessing(false);
            }
        };

        handleOAuthCallback();
    }, [searchParams, refreshUser, router]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="max-w-md w-full space-y-8 text-center">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">Authentication Error</h2>
                        <p className="mt-4 text-gray-600">{error}</p>
                        <div className="mt-6">
                            <button
                                onClick={() => router.push('/login')}
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                            >
                                Back to Login
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full space-y-8 text-center">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900">
                        {isProcessing ? 'Completing Sign In...' : 'Redirecting...'}
                    </h2>
                    <div className="mt-4">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    </div>
                    <p className="mt-4 text-gray-600">
                        Please wait while we complete your {params.provider} authentication.
                    </p>
                </div>
            </div>
        </div>
    );
}
