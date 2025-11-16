/**
 * Calendar Integration Types
 * 
 * TypeScript types for calendar integration features
 * including OAuth credentials, calendar events, and providers.
 */

export type CalendarProvider = 'google' | 'outlook';

export interface CalendarCredential {
    id: number;
    user_id: number;
    provider: CalendarProvider;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface CalendarEvent {
    id: number;
    user_id: number;
    application_id?: number;
    calendar_credential_id: number;
    event_id: string;
    title: string;
    description?: string;
    location?: string;
    start_time: string;
    end_time: string;
    timezone: string;
    reminder_15min: boolean;
    reminder_1hour: boolean;
    reminder_1day: boolean;
    is_synced: boolean;
    last_synced_at?: string;
    created_at: string;
    updated_at: string;
}

export interface CalendarEventCreate {
    application_id?: number;
    title: string;
    description?: string;
    location?: string;
    start_time: string;
    end_time: string;
    timezone?: string;
    reminder_15min?: boolean;
    reminder_1hour?: boolean;
    reminder_1day?: boolean;
    provider: CalendarProvider;
}

export interface CalendarEventUpdate {
    title?: string;
    description?: string;
    location?: string;
    start_time?: string;
    end_time?: string;
    timezone?: string;
    reminder_15min?: boolean;
    reminder_1hour?: boolean;
    reminder_1day?: boolean;
}

export interface CalendarOAuthUrl {
    authorization_url: string;
}

export interface CalendarOAuthCallback {
    code: string;
    redirect_uri: string;
}
