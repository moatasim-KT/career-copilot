# Phase 4: Performance Optimization Research

This document outlines the research findings for the performance optimization phase of the Career Copilot project.

## 9. Implement Code Splitting

### 9.1 Audit current bundle size

The `npm run build` command failed with multiple errors, so it was not possible to audit the bundle size. The errors are related to missing exports in the following files:

*   `frontend/src/components/ui/Button2.tsx`
*   `frontend/src/components/ui/Input2.tsx`
*   `frontend/src/components/ui/Select2.tsx`
*   `frontend/src/lib/animations.ts`

These errors need to be fixed before the bundle size can be audited.

**Recommendation:** Fix the build errors and then run `ANALYZE=true npm run build` to generate a bundle analysis report. This will help identify large chunks that can be optimized.

### 9.2 Implement component-level code splitting

**Heavy Components:**

Based on the file structure, the following components are likely to be heavy and could be candidates for lazy loading:

*   `frontend/src/components/charts/*`: Charting libraries are often large.
*   `frontend/src/components/ui/DataTable/DataTable.tsx`: Data tables with many features can be heavy.
*   `frontend/src/components/features/ResumeEditor.tsx`: A rich text editor for resumes could be a large component.

**Recommendation:**

*   Use `React.lazy()` and `Suspense` to wrap these components.
*   Create lightweight loading fallback components to show while the heavy components are being loaded.

### 9.3 Implement dynamic imports for conditional features

**Conditionally Used Features:**

The following features are likely used conditionally and can be loaded with dynamic imports:

*   Modals and dialogs (e.g., `frontend/src/components/ui/Modal.tsx`)
*   Features that are only available to authenticated users.
*   Features that are behind a feature flag.

**Recommendation:**

*   Use dynamic `import()` for these components.
*   This will ensure that the code for these features is only loaded when they are actually used.

### 9.4 Add preload for critical routes

**Critical User Paths:**

The following routes are critical for the user experience and should be preloaded:

*   `/jobs`
*   `/applications`
*   `/profile`
*   `/dashboard`

**Recommendation:**

*   Use the `router.prefetch()` method from Next.js to preload these routes when the user hovers over the links.

### 9.5 Set bundle size budget alerts

**Recommendation:**

*   Configure bundle size budgets in `next.config.js` to prevent the bundle size from growing unintentionally.
*   Set a warning threshold at 200KB and an error threshold at 250KB per route.
*   Integrate this into the CI/CD pipeline to fail builds that exceed the budget.

## 10. Optimize Images

### 10.1 Migrate all img tags to Next.js Image

**Recommendation:**

*   Search the entire codebase for `<img>` tags and replace them with the Next.js `<Image>` component.
*   Add the required props: `width`, `height`, and `alt`.

### 10.2 Configure responsive images

**Recommendation:**

*   Configure image sizes in `next.config.js` to generate different image sizes for different devices.
*   Use the `sizes` prop on the `<Image>` component to specify how the image should be displayed at different breakpoints.

### 10.3 Optimize image formats

**Recommendation:**

*   Configure WebP format in `next.config.js` to serve images in the modern WebP format, which is smaller than JPEG and PNG.
*   Compress source images to be less than 100KB.

### 10.4 Test image optimization

**Recommendation:**

*   Use the browser's developer tools to simulate a slow 3G network and verify that the blur placeholders appear while the images are loading.
*   Check the Network tab to ensure that the images are being served in the WebP format.

## 11. Implement List Virtualization

### 11.1 Create VirtualJobList component

**Recommendation:**

*   Use the `@tanstack/react-virtual` library to create a virtualized list for the jobs page.
*   Configure the virtualizer with an `estimateSize` function to estimate the size of each item in the list.
*   Set the `overscan` property to 5 to render a few items above and below the visible area.

### 11.2 Create VirtualApplicationList component

**Recommendation:**

*   Implement a virtualized list for the applications page, similar to the `VirtualJobList` component.

### 11.3 Add virtualization to DataTable

**Recommendation:**

*   Update the `DataTable` component to support virtualization when the number of rows is greater than 100.
*   Use `@tanstack/react-virtual` to virtualize the rows.

### 11.4 Performance testing

**Recommendation:**

*   Benchmark the rendering time before and after implementing virtualization to measure the performance improvement.
*   Measure the frames per second (FPS) during scrolling to ensure a smooth user experience.
*   Test on lower-end devices to ensure that the virtualization is effective.

## 12. Optimize Caching & State Management

### 12.1 Review and optimize React Query configuration

**Recommendation:**

*   Review the current `queryClient` configuration and optimize the `staleTime` and `cacheTime` for different query types.
*   **Jobs list:** `staleTime: 5 * 60 * 1000` (5 minutes), `refetchOnMount: true`
*   **Applications:** `staleTime: 1 * 60 * 1000` (1 minute), `refetchOnMount: true`
*   **User profile:** `staleTime: 30 * 60 * 1000` (30 minutes), `refetchOnFocus: true`
*   **Analytics:** `staleTime: 10 * 60 * 1000` (10 minutes), `refetchOnMount: false`
*   **Notifications:** `staleTime: 30 * 1000` (30 seconds), `refetchOnFocus: true`

### 12.2 Implement stale-while-revalidate pattern

**Recommendation:**

*   Configure SWR for key data endpoints to show cached data immediately while fetching fresh data in the background.

### 12.3 Implement optimistic updates

**Recommendation:**

*   Implement optimistic updates for application status changes and job saves/unsaves to make the UI feel more responsive.
*   Implement a rollback mechanism to handle cases where the server request fails.

### 12.4 Implement prefetching

**Recommendation:**

*   Prefetch job and application details when the user hovers over the cards.
*   Prefetch the next pagination page when the user scrolls near the end of the current page.

## 13. Setup Performance Monitoring

### 13.1 Install and configure Lighthouse CI

**Recommendation:**

*   Install `@lhci/cli`.
*   Create a `lighthouserc.json` configuration file.
*   Add an npm script: `"lighthouse": "lhci autorun"`.

### 13.2 Implement Web Vitals reporting

**Recommendation:**

*   Create a `frontend/src/lib/vitals.ts` file.
*   Implement the `reportWebVitals` function to send metrics to an analytics service (for now, `console.log` is sufficient).
*   Track FCP, LCP, FID, CLS, and TTFB.

### 13.3 Define performance budgets

**Recommendation:**

*   **FCP:** < 1.5s
*   **LCP:** < 2.5s
*   **FID:** < 100ms
*   **CLS:** < 0.1
*   **Bundle size:** < 250KB gzipped
*   **Lighthouse Performance score:** > 95

### 13.4 Add Lighthouse to CI/CD

**Recommendation:**

*   Create a GitHub Actions workflow for Lighthouse.
*   Run the workflow on every pull request.
*   Fail the build if the Performance score is less than 90.
*   Post the Lighthouse results as a comment on the pull request.
