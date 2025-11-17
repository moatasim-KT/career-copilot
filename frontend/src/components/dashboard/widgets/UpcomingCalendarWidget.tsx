/**
 * Upcoming Calendar Widget
 * 
 * Displays next 5 upcoming interviews/events
 */

'use client';

import { format } from 'date-fns';
import { Calendar, Clock } from 'lucide-react';
import { useEffect, useState } from 'react';

import { CalendarService } from '@/lib/api/client';
import type { CalendarEvent } from '@/types/calendar';

export default function UpcomingCalendarWidget() {
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadEvents = async () => {
            try {
                const response = await CalendarService.listEvents();
                if (response.data) {
                    // Filter upcoming events and sort by date
                    const upcoming = response.data
                        .filter((event: CalendarEvent) => new Date(event.start_time) > new Date())
                        .sort((a: CalendarEvent, b: CalendarEvent) =>
                            new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
                        )
                        .slice(0, 5);
                    setEvents(upcoming);
                }
            } catch (error) {
                console.error('Failed to load calendar events:', error);
            } finally {
                setLoading(false);
            }
        };

        loadEvents();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {events.map((event) => (
                <div
                    key={event.id}
                    className="p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                    <h4 className="font-medium text-sm mb-2">{event.title}</h4>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            <span>{format(new Date(event.start_time), 'MMM d, yyyy')}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>
                                {format(new Date(event.start_time), 'h:mm a')} -{' '}
                                {format(new Date(event.end_time), 'h:mm a')}
                            </span>
                        </div>
                    </div>
                </div>
            ))}

            {events.length === 0 && (
                <div className="text-center py-6">
                    <Calendar className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-20" />
                    <p className="text-sm text-muted-foreground">No upcoming events</p>
                </div>
            )}
        </div>
    );
}
