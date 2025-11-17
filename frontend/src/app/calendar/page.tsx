/**
 * Calendar Events Page
 * 
 * Displays all calendar events with react-big-calendar
 * Supports month, week, and day views
 */

'use client';

import { format } from 'date-fns';
import { Calendar as CalendarIcon, Clock, MapPin, Plus } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Calendar, dateFnsLocalizer, View } from 'react-big-calendar';
import 'react-big-calendar/lib/css/react-big-calendar.css';

import CreateEventDialog from '@/components/calendar/CreateEventDialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CalendarService } from '@/lib/api/client';
import type { CalendarEvent } from '@/types/calendar';

import { useToast } from '@/components/ui/use-toast';

const locales = {
    'en-US': require('date-fns/locale/en-US'),
};

const localizer = dateFnsLocalizer({
    format,
    parse: (str: string) => new Date(str),
    startOfWeek: () => new Date(),
    getDay: (date: Date) => date.getDay(),
    locales,
});

interface CalendarEventWithDates extends Omit<CalendarEvent, 'start_time' | 'end_time'> {
    start: Date;
    end: Date;
    title: string;
}

export default function CalendarPage() {
    const [events, setEvents] = useState<CalendarEventWithDates[]>([]);
    const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
    const [view, setView] = useState<View>('month');
    const [date, setDate] = useState(new Date());
    const [loading, setLoading] = useState(true);
    const [showEventDialog, setShowEventDialog] = useState(false);
    const { toast } = useToast();

    const loadEvents = useCallback(async () => {
        try {
            setLoading(true);
            const response = await CalendarService.listEvents();

            if (response.data) {
                const formattedEvents = response.data.map((event: CalendarEvent) => ({
                    ...event,
                    start: new Date(event.start_time),
                    end: new Date(event.end_time),
                    title: event.title,
                }));
                setEvents(formattedEvents);
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to load calendar events',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => {
        loadEvents();
    }, [loadEvents]);

    const handleSelectEvent = (event: CalendarEventWithDates) => {
        setSelectedEvent(events.find(e => e.id === event.id) || null);
    };

    const handleDeleteEvent = async (eventId: number) => {
        try {
            const response = await CalendarService.deleteEvent(eventId);
            if (response.status === 200) {
                toast({
                    title: 'Event Deleted',
                    description: 'Calendar event has been deleted',
                });
                setSelectedEvent(null);
                await loadEvents();
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to delete event',
                variant: 'destructive',
            });
        }
    };

    const eventStyleGetter = (event: CalendarEventWithDates) => {
        const style = {
            backgroundColor: '#3b82f6',
            borderRadius: '5px',
            opacity: 0.8,
            color: 'white',
            border: '0px',
            display: 'block',
        };
        return { style };
    };

    if (loading) {
        return (
            <div className="container mx-auto py-8 px-4">
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8 px-4">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Calendar</h1>
                    <p className="text-muted-foreground">
                        Manage your interview schedules and events
                    </p>
                </div>
                <CreateEventDialog
                    trigger={
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            New Event
                        </Button>
                    }
                    onEventCreated={loadEvents}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Calendar View */}
                <div className="lg:col-span-2">
                    <Card>
                        <CardContent className="p-6">
                            <div style={{ height: '600px' }}>
                                <Calendar
                                    localizer={localizer}
                                    events={events}
                                    startAccessor="start"
                                    endAccessor="end"
                                    view={view}
                                    onView={setView}
                                    date={date}
                                    onNavigate={setDate}
                                    onSelectEvent={handleSelectEvent}
                                    eventPropGetter={eventStyleGetter}
                                    popup
                                    style={{ height: '100%' }}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Event Details Sidebar */}
                <div>
                    <Card>
                        <CardHeader>
                            <CardTitle>Event Details</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {selectedEvent ? (
                                <div className="space-y-4">
                                    <div>
                                        <h3 className="font-semibold text-lg mb-2">{selectedEvent.title}</h3>
                                        {selectedEvent.description && (
                                            <p className="text-sm text-muted-foreground mb-4">
                                                {selectedEvent.description}
                                            </p>
                                        )}
                                    </div>

                                    <div className="space-y-3">
                                        <div className="flex items-start space-x-3">
                                            <Clock className="h-4 w-4 mt-0.5 text-muted-foreground" />
                                            <div className="text-sm">
                                                <p className="font-medium">
                                                    {format(new Date(selectedEvent.start_time), 'PPP')}
                                                </p>
                                                <p className="text-muted-foreground">
                                                    {format(new Date(selectedEvent.start_time), 'p')} -{' '}
                                                    {format(new Date(selectedEvent.end_time), 'p')}
                                                </p>
                                            </div>
                                        </div>

                                        {selectedEvent.location && (
                                            <div className="flex items-start space-x-3">
                                                <MapPin className="h-4 w-4 mt-0.5 text-muted-foreground" />
                                                <p className="text-sm">{selectedEvent.location}</p>
                                            </div>
                                        )}

                                        <div className="flex items-start space-x-3">
                                            <CalendarIcon className="h-4 w-4 mt-0.5 text-muted-foreground" />
                                            <div className="text-sm">
                                                <p className="text-muted-foreground">
                                                    Provider: {selectedEvent.calendar_credential_id ? 'Connected' : 'None'}
                                                </p>
                                                {selectedEvent.is_synced && (
                                                    <p className="text-green-600 text-xs mt-1">✓ Synced</p>
                                                )}
                                            </div>
                                        </div>

                                        {(selectedEvent.reminder_15min || selectedEvent.reminder_1hour || selectedEvent.reminder_1day) && (
                                            <div className="pt-2 border-t">
                                                <p className="text-sm font-medium mb-2">Reminders</p>
                                                <div className="space-y-1 text-sm text-muted-foreground">
                                                    {selectedEvent.reminder_15min && <p>• 15 minutes before</p>}
                                                    {selectedEvent.reminder_1hour && <p>• 1 hour before</p>}
                                                    {selectedEvent.reminder_1day && <p>• 1 day before</p>}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="pt-4 space-y-2">
                                        <Button
                                            variant="destructive"
                                            className="w-full"
                                            onClick={() => handleDeleteEvent(selectedEvent.id)}
                                        >
                                            Delete Event
                                        </Button>
                                        <Button
                                            variant="outline"
                                            className="w-full"
                                            onClick={() => setSelectedEvent(null)}
                                        >
                                            Close
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <CalendarIcon className="h-12 w-12 mx-auto mb-4 opacity-20" />
                                    <p>Select an event to view details</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Upcoming Events */}
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Upcoming Events</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {events
                                    .filter(e => new Date(e.start) > new Date())
                                    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
                                    .slice(0, 5)
                                    .map(event => (
                                        <button
                                            key={event.id}
                                            onClick={() => setSelectedEvent(events.find(e => e.id === event.id) || null)}
                                            className="w-full text-left p-3 rounded-lg border hover:bg-accent transition-colors"
                                        >
                                            <p className="font-medium text-sm">{event.title}</p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {format(new Date(event.start), 'MMM d, h:mm a')}
                                            </p>
                                        </button>
                                    ))}
                                {events.filter(e => new Date(e.start) > new Date()).length === 0 && (
                                    <p className="text-sm text-muted-foreground text-center py-4">
                                        No upcoming events
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
