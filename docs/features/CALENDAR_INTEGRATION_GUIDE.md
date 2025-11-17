# Calendar Integration Guide

## Overview

Career Copilot's calendar integration allows you to sync your job interview schedules with Google Calendar and Microsoft Outlook. This ensures you never miss an important interview and keeps all your professional events in one place.

## Features

- **Two-way Sync**: Events created in Career Copilot automatically sync to your calendar
- **Multiple Providers**: Support for Google Calendar and Microsoft Outlook
- **Event Management**: Create, view, edit, and delete interview events
- **Automatic Reminders**: Set reminders for 15 minutes, 1 hour, or 1 day before events
- **Application Linking**: Connect events directly to job applications
- **Multiple Views**: View events in month, week, or day view

## Getting Started

### Connecting Your Calendar

#### Google Calendar Setup

1. Navigate to **Settings → Calendar Integration**
2. Click the **"Connect Google Calendar"** button
3. Sign in to your Google account when prompted
4. Grant Career Copilot permission to access your calendar
5. You'll be redirected back to the settings page with a success message

**Permissions Required:**
- View and edit events on all your calendars
- Create new calendars
- View calendar settings

#### Microsoft Outlook Setup

1. Navigate to **Settings → Calendar Integration**
2. Click the **"Connect Microsoft Outlook"** button
3. Sign in with your Microsoft account
4. Grant the requested permissions
5. You'll be redirected back to the settings page with a success message

**Permissions Required:**
- Read and write access to your calendars
- Read your profile information

### Disconnecting a Calendar

1. Go to **Settings → Calendar Integration**
2. Find the connected calendar provider
3. Click the **"Disconnect"** button
4. Confirm the disconnection

**Note**: Disconnecting will stop future syncs but won't delete existing events from your calendar.

## Using the Calendar

### Viewing Your Calendar

1. Navigate to **Calendar** from the main menu
2. Choose your preferred view:
   - **Month View**: See all events for the entire month
   - **Week View**: Focus on the current week
   - **Day View**: See hourly breakdown for a single day

### Creating Events

#### From the Calendar Page

1. Click the **"New Event"** button
2. Fill in the event details:
   - **Title**: Event name (e.g., "Interview with Company X")
   - **Description**: Additional details about the interview
   - **Location**: Physical address or video call link
   - **Start Date & Time**: When the interview begins
   - **End Date & Time**: When it ends
   - **Timezone**: Auto-detected, but can be changed
3. Select reminder preferences:
   - ☐ 15 minutes before
   - ☑ 1 hour before (default)
   - ☐ 1 day before
4. (Optional) Link to an application
5. Click **"Create Event"**

#### From Application Cards

1. Navigate to your applications list
2. Find the application you want to schedule
3. Click the **"Add to Calendar"** button on the application card
4. The event form will pre-fill with:
   - Interview title with company name
   - Job title and application details
   - Application link for reference
5. Set the date and time
6. Click **"Create Event"**

**Pro Tip**: Use this method for interview scheduling to automatically link events to applications!

### Viewing Event Details

1. Click on any event in the calendar
2. The **Event Details** sidebar will display:
   - Event title and description
   - Date and time
   - Location
   - Calendar provider sync status
   - Reminder settings
   - Linked application (if any)

### Editing Events

1. Click on an event to view details
2. Click the **"Edit"** button (coming soon in next update)
3. Make your changes
4. Click **"Save Changes"**

### Deleting Events

1. Click on an event to view details
2. Click the **"Delete Event"** button
3. Confirm the deletion
4. The event will be removed from both Career Copilot and your synced calendar

### Upcoming Events

The **Upcoming Events** sidebar shows your next 5 interviews/events:
- Event title
- Date and time
- Quick access to event details

## Calendar Sync

### How Sync Works

- **New Events**: Created in Career Copilot and synced to your connected calendar
- **Updates**: Changes made in Career Copilot sync to your calendar
- **Deletions**: Deleted events are removed from your calendar
- **Sync Status**: Green checkmark indicates successful sync

### Sync Frequency

- Events sync immediately upon creation or modification
- Background sync runs every 15 minutes for updates

### Manual Re-sync

If sync status shows an error:
1. Navigate to **Settings → Calendar Integration**
2. Click **"Reconnect"** for the affected calendar
3. Events will re-sync automatically

## Troubleshooting

### Calendar Not Connecting

**Problem**: OAuth connection fails or times out

**Solutions**:
1. Check your internet connection
2. Ensure pop-ups are not blocked in your browser
3. Try incognito/private browsing mode
4. Clear browser cookies and cache
5. Use a different browser

### Events Not Syncing

**Problem**: Events don't appear in Google Calendar or Outlook

**Solutions**:
1. Check the sync status (green checkmark = synced)
2. Wait 1-2 minutes for sync to complete
3. Disconnect and reconnect your calendar
4. Check calendar permissions in your Google/Microsoft account settings

### Wrong Timezone

**Problem**: Events appear at the wrong time

**Solutions**:
1. Verify your computer's timezone settings
2. Check the timezone field when creating events
3. Update the event with the correct timezone

### "Forbidden" or Permission Errors

**Problem**: Error messages about permissions

**Solutions**:
1. Disconnect your calendar
2. Reconnect and ensure all permissions are granted
3. Check your Google/Microsoft account security settings
4. Ensure the calendar account is active

## Best Practices

### 1. Set Consistent Reminders
- Enable 1-hour reminder for all interviews
- Add 1-day reminder for important final rounds

### 2. Use Descriptive Titles
- Include company name: "Interview with TechCorp"
- Specify round: "2nd Round Interview - Engineering Manager"

### 3. Add Important Details
- Video call links in the location field
- Interview prep notes in the description
- Interviewer names and titles

### 4. Link to Applications
- Always link events to applications for tracking
- Use "Add to Calendar" from application cards

### 5. Keep Calendar Updated
- Delete canceled interviews immediately
- Update times if rescheduled

### 6. Review Upcoming Events
- Check the upcoming events sidebar daily
- Prepare for interviews in advance

## Privacy & Security

- **Data Encryption**: All calendar data is encrypted in transit
- **Limited Access**: Career Copilot only accesses event data, not email or contacts
- **Revocable Access**: You can disconnect at any time
- **No Sharing**: Your calendar data is never shared with third parties

## FAQ

**Q: Can I sync multiple calendars?**
A: Currently, you can connect one Google Calendar and one Outlook calendar per account.

**Q: Will events I create in Google Calendar appear in Career Copilot?**
A: No, sync is currently one-way (Career Copilot → Your Calendar). Two-way sync is planned for a future update.

**Q: What happens to events if I disconnect my calendar?**
A: Events remain in your Google Calendar/Outlook but will no longer sync with Career Copilot.

**Q: Can I change which calendar events sync to?**
A: Events sync to your primary calendar. You can change this in your Google/Outlook settings.

**Q: Are past events synced?**
A: Only future events are synced. Past events are kept for reference in Career Copilot.

**Q: Is there a limit on the number of events?**
A: No limit on the number of events you can create and sync.

## Support

Need help? Contact us:
- **Email**: support@careercopilot.com
- **Help Center**: [https://help.careercopilot.com](https://help.careercopilot.com)
- **GitHub Issues**: [Report bugs or suggest features](https://github.com/moatasim-KT/career-copilot/issues)

---

**Last Updated**: November 17, 2025
**Version**: 1.0.0
