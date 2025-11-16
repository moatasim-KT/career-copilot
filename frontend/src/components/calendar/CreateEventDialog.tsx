/**
 * Create Calendar Event Dialog
 * 
 * Modal dialog for creating calendar events linked to job applications.
 * Supports both Google Calendar and Microsoft Outlook.
 */

'use client';

import { Calendar } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { CalendarService } from '@/lib/api/client';
import type { CalendarProvider } from '@/types/calendar';

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

interface CreateEventDialogProps {
    applicationId?: number;
    trigger?: React.ReactNode;
    onEventCreated?: () => void;
}

export default function CreateEventDialog({
    applicationId,
    trigger,
    onEventCreated,
}: CreateEventDialogProps) {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        location: '',
        startDate: '',
        startTime: '',
        endDate: '',
        endTime: '',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        provider: 'google' as CalendarProvider,
        reminder15min: true,
        reminder1hour: true,
        reminder1day: false,
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.title || !formData.startDate || !formData.startTime || !formData.endDate || !formData.endTime) {
            toast({
                title: 'Missing Information',
                description: 'Please fill in all required fields',
                variant: 'destructive',
            });
            return;
        }

        try {
            setLoading(true);
            
            const startDateTime = `${formData.startDate}T${formData.startTime}:00`;
            const endDateTime = `${formData.endDate}T${formData.endTime}:00`;

            const response = await CalendarService.createEvent({
                application_id: applicationId,
                title: formData.title,
                description: formData.description || undefined,
                location: formData.location || undefined,
                start_time: startDateTime,
                end_time: endDateTime,
                timezone: formData.timezone,
                reminder_15min: formData.reminder15min,
                reminder_1hour: formData.reminder1hour,
                reminder_1day: formData.reminder1day,
                provider: formData.provider,
            });

            if (response.data) {
                toast({
                    title: 'Event Created',
                    description: `Calendar event has been created and synced to ${formData.provider === 'google' ? 'Google Calendar' : 'Outlook'}`,
                });
                setOpen(false);
                setFormData({
                    title: '',
                    description: '',
                    location: '',
                    startDate: '',
                    startTime: '',
                    endDate: '',
                    endTime: '',
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    provider: 'google',
                    reminder15min: true,
                    reminder1hour: true,
                    reminder1day: false,
                });
                onEventCreated?.();
            }
        } catch (error: any) {
            toast({
                title: 'Failed to Create Event',
                description: error.message || 'An error occurred while creating the calendar event',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                {trigger || (
                    <Button variant="outline" size="sm">
                        <Calendar className="mr-2 h-4 w-4" />
                        Add to Calendar
                    </Button>
                )}
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>Create Calendar Event</DialogTitle>
                        <DialogDescription>
                            Create an interview event that will sync with your connected calendar
                        </DialogDescription>
                    </DialogHeader>

                    <div className="grid gap-4 py-4">
                        {/* Title */}
                        <div className="grid gap-2">
                            <Label htmlFor="title">Event Title *</Label>
                            <Input
                                id="title"
                                placeholder="Interview with Company Name"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                required
                            />
                        </div>

                        {/* Description */}
                        <div className="grid gap-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                placeholder="Interview details, preparation notes..."
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                rows={3}
                            />
                        </div>

                        {/* Location */}
                        <div className="grid gap-2">
                            <Label htmlFor="location">Location</Label>
                            <Input
                                id="location"
                                placeholder="Office address or video call link"
                                value={formData.location}
                                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                            />
                        </div>

                        {/* Start Date and Time */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label htmlFor="start-date">Start Date *</Label>
                                <Input
                                    id="start-date"
                                    type="date"
                                    value={formData.startDate}
                                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="start-time">Start Time *</Label>
                                <Input
                                    id="start-time"
                                    type="time"
                                    value={formData.startTime}
                                    onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        {/* End Date and Time */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label htmlFor="end-date">End Date *</Label>
                                <Input
                                    id="end-date"
                                    type="date"
                                    value={formData.endDate}
                                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="end-time">End Time *</Label>
                                <Input
                                    id="end-time"
                                    type="time"
                                    value={formData.endTime}
                                    onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        {/* Calendar Provider */}
                        <div className="grid gap-2">
                            <Label htmlFor="provider">Calendar Provider *</Label>
                            <Select
                                value={formData.provider}
                                onValueChange={(value: CalendarProvider) =>
                                    setFormData({ ...formData, provider: value })
                                }
                            >
                                <SelectTrigger id="provider">
                                    <SelectValue placeholder="Select calendar" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="google">Google Calendar</SelectItem>
                                    <SelectItem value="outlook">Microsoft Outlook</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Reminders */}
                        <div className="grid gap-3">
                            <Label>Reminders</Label>
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="reminder15"
                                    checked={formData.reminder15min}
                                    onCheckedChange={(checked) =>
                                        setFormData({ ...formData, reminder15min: checked as boolean })
                                    }
                                />
                                <Label htmlFor="reminder15" className="font-normal cursor-pointer">
                                    15 minutes before
                                </Label>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="reminder1h"
                                    checked={formData.reminder1hour}
                                    onCheckedChange={(checked) =>
                                        setFormData({ ...formData, reminder1hour: checked as boolean })
                                    }
                                />
                                <Label htmlFor="reminder1h" className="font-normal cursor-pointer">
                                    1 hour before
                                </Label>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="reminder1d"
                                    checked={formData.reminder1day}
                                    onCheckedChange={(checked) =>
                                        setFormData({ ...formData, reminder1day: checked as boolean })
                                    }
                                />
                                <Label htmlFor="reminder1d" className="font-normal cursor-pointer">
                                    1 day before
                                </Label>
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Creating...' : 'Create Event'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
