# API Integration Issues

This document details the frontend API integration gaps that are blocking full functionality.

## Current Issues

### Hook Implementation Placeholders
Multiple React hooks contain placeholder API client implementations:

- `useDeleteApplication.ts` - Placeholder for delete application API
- `useAddJob.ts` - Placeholder for job creation API
- `useDeleteJob.ts` - Placeholder for job deletion API
- `useUpdateJob.ts` - Placeholder for job update API
- `useAddApplication.ts` - Placeholder for application creation API

### Authentication Flow Issues
- **Location**: `frontend/src/lib/api/api.ts`
- **Issue**: TODO for global logout/re-authentication flow
- **Impact**: Users cannot properly handle expired sessions

### Data Backup Integration
- **Location**: `frontend/src/lib/export/dataBackup.ts`
- **Issue**: Placeholder implementations for backup/restore operations
- **Impact**: No data export/import functionality

## Required Implementation

### API Client Enhancement
```typescript
// Replace placeholder with actual API calls
const deleteApplication = async (id: string) => {
  return await apiClient.delete(`/applications/${id}`);
};
```

### Authentication Flow
- Implement automatic token refresh
- Handle 401 responses with re-authentication
- Provide user feedback for authentication issues

### Error Handling
- Standardized error responses
- User-friendly error messages
- Retry logic for transient failures

## Dependencies
- Backend API endpoints must be fully implemented
- Authentication system must be operational
- Error handling middleware must be in place

## Testing Requirements
- API integration tests for all hooks
- Authentication flow testing
- Error scenario testing
- Offline functionality testing

## Related Files
- `frontend/src/hooks/`
- `frontend/src/lib/api/`
- `backend/app/api/v1/`

## Priority
🟠 **HIGH** - Critical for frontend functionality

---

*See [[frontend-gaps.md]] for complete list and [[prioritization.md]] for timeline*