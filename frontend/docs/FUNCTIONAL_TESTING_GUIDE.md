# Functional Testing Guide

This guide provides instructions for conducting comprehensive functional testing of the Career Copilot application.

## Table of Contents

- [Overview](#overview)
- [Test Environment Setup](#test-environment-setup)
- [Automated Testing](#automated-testing)
- [Manual Testing](#manual-testing)
- [Test Scenarios](#test-scenarios)
- [Test Checklist](#test-checklist)
- [Bug Reporting](#bug-reporting)

## Overview

Functional testing ensures that all features work correctly from the user's perspective. This includes:

- User flows (sign up, login, job search, applications)
- Form validation and submission
- CRUD operations
- Error handling
- Navigation and routing
- Data persistence

## Test Environment Setup

### Prerequisites

1. **Backend API running:**
   ```bash
   cd backend
   npm run dev
   ```

2. **Frontend application running:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test database:**
   - Use a separate test database
   - Seed with test data if needed

### Environment Variables

Create `.env.test.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Automated Testing

### Run E2E Tests

```bash
cd frontend
npm run test:e2e
```

### Run Specific Test Suite

```bash
npx playwright test tests/e2e/functional-tests.spec.ts
```

### Run in UI Mode

```bash
npx playwright test --ui
```

### Run in Debug Mode

```bash
npx playwright test --debug
```

### Generate Test Report

```bash
npx playwright show-report
```

## Manual Testing

### Test Data

Use the following test accounts:

**Test User 1:**
- Email: `test1@example.com`
- Password: `TestPassword123!`

**Test User 2:**
- Email: `test2@example.com`
- Password: `TestPassword123!`

### Browser Testing

Test on the following browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Device Testing

Test on the following devices:
- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x667)

## Test Scenarios

### 1. User Registration and Onboarding

**Objective:** Verify users can sign up and complete onboarding.

**Steps:**
1. Navigate to `/signup`
2. Fill in registration form:
   - Email: `newuser@example.com`
   - Password: `TestPassword123!`
   - Confirm Password: `TestPassword123!`
   - Name: `New User`
3. Click "Sign Up"
4. Verify redirect to onboarding
5. Complete onboarding steps:
   - Profile information (job title, experience)
   - Job preferences (remote, full-time, etc.)
   - Skills (React, TypeScript, etc.)
6. Click "Complete Onboarding"
7. Verify redirect to dashboard

**Expected Results:**
- User account created successfully
- Onboarding completed
- Dashboard displays with user data
- Welcome message shown

**Test Variations:**
- Invalid email format
- Weak password
- Mismatched passwords
- Missing required fields
- Duplicate email

### 2. Job Search and Filtering

**Objective:** Verify users can search and filter jobs.

**Steps:**
1. Log in as test user
2. Navigate to `/jobs`
3. Verify job list loads
4. Enter search term: "Frontend Developer"
5. Apply filters:
   - Location: "Remote"
   - Job Type: "Full-time"
   - Salary: "$100k+"
6. Click "Apply Filters"
7. Verify filtered results

**Expected Results:**
- Job list displays correctly
- Search works as expected
- Filters apply correctly
- Results update in real-time
- No results message when appropriate

**Test Variations:**
- Search with no results
- Multiple filters combined
- Clear filters
- Sort by different criteria

### 3. Save and Apply to Jobs

**Objective:** Verify users can save jobs and submit applications.

**Steps:**
1. Log in as test user
2. Navigate to `/jobs`
3. Click on a job card
4. Verify job details display
5. Click "Save Job"
6. Verify job saved (toast notification)
7. Click "Apply"
8. Fill application form:
   - Cover Letter: "I am interested..."
   - Resume URL: "https://example.com/resume.pdf"
   - Portfolio URL: "https://example.com/portfolio"
9. Click "Submit Application"
10. Verify success message
11. Verify redirect to applications page

**Expected Results:**
- Job details display correctly
- Save job works
- Application form validates input
- Application submits successfully
- Application appears in applications list

**Test Variations:**
- Apply without saving
- Save without applying
- Invalid URLs in application
- Missing required fields

### 4. Track Applications

**Objective:** Verify users can view and update applications.

**Steps:**
1. Log in as test user
2. Navigate to `/applications`
3. Verify applications list displays
4. Click on an application
5. Verify application details display
6. Click "Update Status"
7. Change status to "Interviewing"
8. Add notes: "Had first round interview"
9. Click "Save"
10. Verify status updated
11. Add interview event:
    - Type: "Interview"
    - Date: Tomorrow
    - Time: "2:00 PM"
    - Notes: "Technical interview"
12. Click "Add Event"
13. Verify event added

**Expected Results:**
- Applications list displays correctly
- Application details show all information
- Status updates successfully
- Events add successfully
- Timeline displays correctly

**Test Variations:**
- Filter by status
- Sort by date
- Delete application
- Add multiple events

### 5. Analytics Dashboard

**Objective:** Verify analytics display correctly.

**Steps:**
1. Log in as test user
2. Navigate to `/analytics`
3. Verify charts display:
   - Applications over time
   - Status distribution
   - Response rate
4. Change time range to "Last 30 days"
5. Verify charts update
6. Click "Export"
7. Verify CSV downloads

**Expected Results:**
- All charts display correctly
- Data is accurate
- Time range filter works
- Export functionality works
- No errors in console

**Test Variations:**
- Different time ranges
- Empty state (no data)
- Large dataset

### 6. Settings and Profile

**Objective:** Verify users can update settings.

**Steps:**
1. Log in as test user
2. Navigate to `/settings/profile`
3. Update profile information:
   - Name: "Updated Name"
   - Job Title: "Senior Engineer"
4. Click "Save"
5. Verify success message
6. Navigate to `/settings/appearance`
7. Change theme to "Dark"
8. Verify theme changes
9. Navigate to `/settings/notifications`
10. Toggle notification preferences
11. Click "Save"
12. Verify preferences saved

**Expected Results:**
- Profile updates successfully
- Theme changes apply immediately
- Notification preferences save
- Changes persist after refresh

**Test Variations:**
- Invalid email format
- Change password
- Delete account

### 7. Data Import/Export

**Objective:** Verify data import and export functionality.

**Steps:**
1. Log in as test user
2. Navigate to `/jobs`
3. Click "Export"
4. Select "All data (CSV)"
5. Verify CSV downloads
6. Click "Import"
7. Upload CSV file
8. Verify preview displays
9. Click "Import"
10. Verify data imported successfully

**Expected Results:**
- Export generates correct CSV
- Import validates CSV format
- Preview shows correct data
- Import creates records
- Error handling for invalid CSV

**Test Variations:**
- Export PDF
- Import invalid CSV
- Import large file

### 8. Error Handling

**Objective:** Verify error scenarios are handled gracefully.

**Steps:**
1. **Network Error:**
   - Disconnect internet
   - Try to load page
   - Verify offline message
   - Reconnect internet
   - Verify page loads

2. **404 Error:**
   - Navigate to `/non-existent-page`
   - Verify 404 page displays
   - Verify helpful links

3. **Server Error:**
   - Simulate 500 error (mock API)
   - Verify error message
   - Verify retry button

4. **Authentication Error:**
   - Expire session token
   - Try to access protected page
   - Verify redirect to login
   - Verify session expired message

**Expected Results:**
- All errors handled gracefully
- User-friendly error messages
- Retry/recovery options provided
- No application crashes

### 9. Form Validation

**Objective:** Verify all forms validate input correctly.

**Forms to Test:**
- Sign up form
- Login form
- Job creation form
- Application form
- Profile settings form
- Password change form

**Validation Tests:**
- Required fields
- Email format
- Password strength
- URL format
- Number ranges
- Text length limits
- Special characters

**Expected Results:**
- Validation errors display clearly
- Errors appear inline with fields
- Form doesn't submit with errors
- Error messages are helpful

### 10. Navigation and Routing

**Objective:** Verify navigation works correctly.

**Steps:**
1. Test all navigation links
2. Test browser back/forward buttons
3. Test direct URL access
4. Test protected routes (without auth)
5. Test redirects after login
6. Test deep linking

**Expected Results:**
- All links work correctly
- Browser navigation works
- Protected routes redirect to login
- Redirects work after login
- Deep links work correctly

## Test Checklist

### User Authentication
- [ ] Sign up with valid data
- [ ] Sign up with invalid data
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Logout
- [ ] Password reset
- [ ] Session persistence
- [ ] Session expiration

### Onboarding
- [ ] Complete all onboarding steps
- [ ] Skip optional steps
- [ ] Navigate back/forward
- [ ] Save progress
- [ ] Validation on each step

### Jobs
- [ ] View job list
- [ ] Search jobs
- [ ] Filter jobs
- [ ] Sort jobs
- [ ] View job details
- [ ] Save job
- [ ] Unsave job
- [ ] Apply to job
- [ ] Create custom job
- [ ] Edit job
- [ ] Delete job

### Applications
- [ ] View applications list
- [ ] Filter applications
- [ ] Sort applications
- [ ] View application details
- [ ] Update application status
- [ ] Add notes
- [ ] Add events
- [ ] Delete application
- [ ] Export applications

### Analytics
- [ ] View analytics dashboard
- [ ] Change time range
- [ ] View different charts
- [ ] Export analytics data
- [ ] Handle empty state

### Settings
- [ ] Update profile
- [ ] Change password
- [ ] Update preferences
- [ ] Change theme
- [ ] Update notifications
- [ ] Export data
- [ ] Import data
- [ ] Delete account

### Forms
- [ ] All required fields validated
- [ ] Email format validated
- [ ] URL format validated
- [ ] Number ranges validated
- [ ] Text length validated
- [ ] Error messages clear
- [ ] Success messages shown

### Error Handling
- [ ] Network errors handled
- [ ] 404 errors handled
- [ ] 500 errors handled
- [ ] 401 errors handled
- [ ] Validation errors handled
- [ ] Retry functionality works

### Navigation
- [ ] All nav links work
- [ ] Browser back/forward work
- [ ] Direct URL access works
- [ ] Protected routes redirect
- [ ] Deep linking works

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] Color contrast sufficient

### Performance
- [ ] Pages load quickly
- [ ] No layout shifts
- [ ] Smooth animations
- [ ] No memory leaks
- [ ] Efficient re-renders

## Bug Reporting

### Bug Report Template

```markdown
**Title:** Brief description of the bug

**Severity:** Critical / High / Medium / Low

**Environment:**
- Browser: Chrome 120
- OS: macOS 14
- Device: Desktop
- URL: https://app.example.com/jobs

**Steps to Reproduce:**
1. Navigate to /jobs
2. Click on first job
3. Click "Apply"
4. ...

**Expected Behavior:**
Application form should open

**Actual Behavior:**
Nothing happens, console shows error

**Screenshots:**
[Attach screenshots]

**Console Errors:**
```
TypeError: Cannot read property 'id' of undefined
```

**Additional Context:**
Only happens when not logged in
```

### Severity Levels

**Critical:**
- Application crashes
- Data loss
- Security vulnerabilities
- Cannot complete core user flows

**High:**
- Major features broken
- Significant user impact
- Workaround exists but difficult

**Medium:**
- Minor features broken
- Moderate user impact
- Easy workaround exists

**Low:**
- Cosmetic issues
- Minor inconvenience
- No functional impact

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [E2E Testing Guide](https://martinfowler.com/articles/practical-test-pyramid.html)
