/**
 * Calendar Settings Page
 * 
 * Allows users to connect Google Calendar and Microsoft Outlook
 * for automatic interview scheduling and calendar sync.
 */

'use client';

import { Calendar, CheckCircle2, Loader2, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CalendarService } from '@/lib/api/client';
import type { CalendarCredential, CalendarProvider } from '@/types/calendar';

import { useToast } from '@/components/ui/use-toast';

export default function CalendarSettingsPage() {
    const [credentials, setCredentials] = useState<CalendarCredential[]>([]);
    const [loading, setLoading] = useState(true);
    const [connecting, setConnecting] = useState<CalendarProvider | null>(null);
    const { toast } = useToast();

    const loadCredentials = async () => {
        try {
            setLoading(true);
            const response = await CalendarService.getCredentials();
            if (response.data) {
                setCredentials(response.data);
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to load calendar credentials',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadCredentials();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const connectCalendar = async (provider: CalendarProvider) => {
        try {
            setConnecting(provider);
            const redirectUri = `${window.location.origin}/settings/calendar/callback`;
            const response = await CalendarService.getAuthUrl(provider, redirectUri);
            
            if (response.data?.authorization_url) {
                // Redirect to OAuth provider
                window.location.href = response.data.authorization_url;
            } else {
                throw new Error('Failed to get authorization URL');
            }
        } catch (error) {
            toast({
                title: 'Connection Failed',
                description: `Failed to connect ${provider === 'google' ? 'Google Calendar' : 'Microsoft Outlook'}`,
                variant: 'destructive',
            });
            setConnecting(null);
        }
    };

    const disconnectCalendar = async (provider: CalendarProvider) => {
        try {
            const response = await CalendarService.disconnect(provider);
            if (response.status === 200) {
                toast({
                    title: 'Calendar Disconnected',
                    description: `${provider === 'google' ? 'Google Calendar' : 'Microsoft Outlook'} has been disconnected`,
                });
                await loadCredentials();
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to disconnect calendar',
                variant: 'destructive',
            });
        }
    };

    const isConnected = (provider: CalendarProvider) => {
        return credentials.some(cred => cred.provider === provider && cred.is_active);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8 px-4">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Calendar Integration</h1>
                    <p className="text-muted-foreground">
                        Connect your calendar to automatically sync interview schedules and receive reminders
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {/* Google Calendar */}
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                        <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <div>
                                        <CardTitle>Google Calendar</CardTitle>
                                        <CardDescription>Sync with your Google account</CardDescription>
                                    </div>
                                </div>
                                {isConnected('google') && (
                                    <Badge variant="success" className="flex items-center space-x-1">
                                        <CheckCircle2 className="h-3 w-3" />
                                        <span>Connected</span>
                                    </Badge>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">
                                    Connect your Google Calendar to automatically create and sync interview events.
                                    Events will be synced in real-time between Career Copilot and Google Calendar.
                                </p>
                                
                                {isConnected('google') ? (
                                    <div className="space-y-2">
                                        <div className="text-sm">
                                            <p className="font-medium">Status: Active</p>
                                            <p className="text-muted-foreground">
                                                Connected on {new Date(credentials.find(c => c.provider === 'google')?.created_at || '').toLocaleDateString()}
                                            </p>
                                        </div>
                                        <Button
                                            variant="destructive"
                                            onClick={() => disconnectCalendar('google')}
                                            className="w-full"
                                        >
                                            <XCircle className="mr-2 h-4 w-4" />
                                            Disconnect Google Calendar
                                        </Button>
                                    </div>
                                ) : (
                                    <Button
                                        onClick={() => connectCalendar('google')}
                                        disabled={connecting === 'google'}
                                        className="w-full"
                                    >
                                        {connecting === 'google' ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Connecting...
                                            </>
                                        ) : (
                                            <>
                                                <Calendar className="mr-2 h-4 w-4" />
                                                Connect Google Calendar
                                            </>
                                        )}
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Microsoft Outlook */}
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                        <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <div>
                                        <CardTitle>Microsoft Outlook</CardTitle>
                                        <CardDescription>Sync with your Microsoft account</CardDescription>
                                    </div>
                                </div>
                                {isConnected('outlook') && (
                                    <Badge variant="success" className="flex items-center space-x-1">
                                        <CheckCircle2 className="h-3 w-3" />
                                        <span>Connected</span>
                                    </Badge>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">
                                    Connect your Microsoft Outlook calendar to automatically create and sync interview events.
                                    Events will be synced in real-time between Career Copilot and Outlook.
                                </p>
                                
                                {isConnected('outlook') ? (
                                    <div className="space-y-2">
                                        <div className="text-sm">
                                            <p className="font-medium">Status: Active</p>
                                            <p className="text-muted-foreground">
                                                Connected on {new Date(credentials.find(c => c.provider === 'outlook')?.created_at || '').toLocaleDateString()}
                                            </p>
                                        </div>
                                        <Button
                                            variant="destructive"
                                            onClick={() => disconnectCalendar('outlook')}
                                            className="w-full"
                                        >
                                            <XCircle className="mr-2 h-4 w-4" />
                                            Disconnect Outlook
                                        </Button>
                                    </div>
                                ) : (
                                    <Button
                                        onClick={() => connectCalendar('outlook')}
                                        disabled={connecting === 'outlook'}
                                        className="w-full"
                                    >
                                        {connecting === 'outlook' ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Connecting...
                                            </>
                                        ) : (
                                            <>
                                                <Calendar className="mr-2 h-4 w-4" />
                                                Connect Outlook
                                            </>
                                        )}
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Features Info */}
                <Card className="mt-6">
                    <CardHeader>
                        <CardTitle>Calendar Integration Features</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2 text-sm">
                            <li className="flex items-start">
                                <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                <span>Automatic event creation when scheduling interviews</span>
                            </li>
                            <li className="flex items-start">
                                <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                <span>Real-time bidirectional sync between Career Copilot and your calendar</span>
                            </li>
                            <li className="flex items-start">
                                <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                <span>Customizable reminders (15 minutes, 1 hour, 1 day before)</span>
                            </li>
                            <li className="flex items-start">
                                <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                <span>Link calendar events to specific job applications</span>
                            </li>
                            <li className="flex items-start">
                                <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                                <span>View all interview events in one unified calendar view</span>
                            </li>
                        </ul>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
