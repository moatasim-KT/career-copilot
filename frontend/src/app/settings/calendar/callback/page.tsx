/**
 * Calendar OAuth Callback Handler
 * 
 * Handles OAuth callback from Google Calendar and Microsoft Outlook
 * after user grants permission.
 */

'use client';

import { Loader2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';

import { useToast } from '@/components/ui/use-toast';
import { CalendarService } from '@/lib/api/client';


function CalendarCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { toast } = useToast();
    const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');

    useEffect(() => {
        const handleCallback = async () => {
            try {
                const code = searchParams.get('code');
                const error = searchParams.get('error');
                const state = searchParams.get('state');

                if (error) {
                    throw new Error(`Authorization failed: ${error}`);
                }

                if (!code) {
                    throw new Error('No authorization code received');
                }

                // Determine provider from state or URL
                const provider = state?.includes('outlook') ? 'outlook' : 'google';
                const redirectUri = `${window.location.origin}/settings/calendar/callback`;

                // Exchange code for credentials
                const response = await CalendarService.handleCallback(provider, code, redirectUri);

                if (response.data) {
                    setStatus('success');
                    toast({
                        title: 'Calendar Connected',
                        description: `${provider === 'google' ? 'Google Calendar' : 'Microsoft Outlook'} has been successfully connected`,
                    });

                    // Redirect back to settings page after 2 seconds
                    setTimeout(() => {
                        router.push('/settings/calendar');
                    }, 2000);
                } else {
                    throw new Error('Failed to connect calendar');
                }
            } catch (error: any) {
                setStatus('error');
                toast({
                    title: 'Connection Failed',
                    description: error.message || 'Failed to connect calendar',
                    variant: 'destructive',
                });

                // Redirect back to settings page after 3 seconds
                setTimeout(() => {
                    router.push('/settings/calendar');
                }, 3000);
            }
        };

        handleCallback();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="text-center space-y-4">
                {status === 'processing' && (
                    <>
                        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
                        <h2 className="text-2xl font-semibold">Connecting Your Calendar</h2>
                        <p className="text-muted-foreground">Please wait while we complete the connection...</p>
                    </>
                )}
                {status === 'success' && (
                    <>
                        <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mx-auto">
                            <svg
                                className="h-6 w-6 text-green-600 dark:text-green-400"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M5 13l4 4L19 7"
                                />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-semibold text-green-600 dark:text-green-400">
                            Calendar Connected!
                        </h2>
                        <p className="text-muted-foreground">Redirecting you back to settings...</p>
                    </>
                )}
                {status === 'error' && (
                    <>
                        <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center mx-auto">
                            <svg
                                className="h-6 w-6 text-red-600 dark:text-red-400"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-semibold text-red-600 dark:text-red-400">
                            Connection Failed
                        </h2>
                        <p className="text-muted-foreground">Redirecting you back to try again...</p>
                    </>
                )}
            </div>
        </div>
    );
}

export default function CalendarCallbackPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center space-y-4">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                    <p className="text-muted-foreground">Loading...</p>
                </div>
            </div>
        }>
            <CalendarCallbackContent />
        </Suspense>
    );
}
