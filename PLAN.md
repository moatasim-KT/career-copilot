# Performance Optimization Plan

This document outlines the plan for the performance optimization phase of the Career Copilot project.

## 1. Fix Build Errors

This is the highest priority task. Without a successful build, no other performance optimization tasks can be completed.

1.  **Investigate and fix the import errors:**
    *   In `frontend/src/components/ui/DataTable/DataTable.tsx`, correct the import of `Button2` from `@/components/ui/Button2`. It should likely be `Button` from `@/components/ui/Button`.
    *   In `frontend/src/components/ui/DataTable/ColumnFilter.tsx`, correct the import of `Input` from `@/components/ui/Input2`. It should likely be `Input` from `@/components/ui/Input`.
    *   In `frontend/src/components/ui/DataTable/DataTable.tsx`, correct the imports of `SelectContent`, `SelectItem`, `SelectTrigger`, and `SelectValue` from `@/components/ui/Select2`. They should likely be imported from `@/components/ui/Select`.
    *   In `frontend/src/components/ui/Button.tsx`, correct the import of `buttonHover` and `buttonTap` from `@/lib/animations`. These exports do not exist. The animations should be implemented using a different method, or the import should be removed.
    *   In `frontend/src/components/ui/Card.tsx`, correct the import of `cardHover` from `@/lib/animations`. This export does not exist. The animation should be implemented using a different method, or the import should be removed.
2.  **Run `npm run build` in the `frontend` directory to verify that the build is successful.**

## 2. Implement Code Splitting

1.  **Audit current bundle size:**
    *   Run `ANALYZE=true npm run build` in the `frontend` directory to generate a bundle analysis report.
    *   Identify and document the largest chunks in the bundle.
2.  **Implement component-level code splitting:**
    *   Identify heavy components for lazy loading (e.g., charts, rich editors, data tables).
    *   Wrap these components with `React.lazy()` and `Suspense`.
    *   Create loading fallback components to be displayed while the heavy components are loading.
3.  **Implement dynamic imports for conditional features:**
    *   Identify conditionally used features (e.g., modals, dialogs).
    *   Convert the imports for these components to dynamic `import()`.
4.  **Add preload for critical routes:**
    *   Identify critical user paths (e.g., `/jobs`, `/applications`, `/profile`, `/dashboard`).
    *   Use `router.prefetch()` to preload these routes on link hover.
5.  **Set bundle size budget alerts:**
    *   Configure bundle size budgets in `next.config.js`.
    *   Set a warning threshold at 200KB and an error threshold at 250KB per route.
    *   Add this to the CI/CD pipeline.

## 3. Optimize Images

1.  **Migrate all `<img>` tags to Next.js `<Image>`:**
    *   Search the codebase for all instances of the `<img>` tag.
    *   Replace them with the Next.js `<Image>` component, providing the required `width`, `height`, and `alt` props.
2.  **Configure responsive images:**
    *   Configure image sizes in `next.config.js` to generate different image sizes for different devices.
    *   Use the `sizes` prop on the `<Image>` component to specify how the image should be displayed at different breakpoints.
3.  **Optimize image formats:**
    *   Configure WebP format in `next.config.js` to serve images in the modern WebP format.
    *   Compress all source images to be less than 100KB.
4.  **Test image optimization:**
    *   Use browser developer tools to simulate a slow 3G network and verify that blur placeholders appear.
    *   Check the Network tab to ensure that images are being served in the WebP format.

## 4. Implement List Virtualization

1.  **Create `VirtualJobList` component:**
    *   Create a new component at `frontend/src/components/jobs/VirtualJobList.tsx`.
    *   Use the `@tanstack/react-virtual` library to create a virtualized list.
    *   Configure the virtualizer with an `estimateSize` function and an `overscan` of 5.
2.  **Create `VirtualApplicationList` component:**
    *   Create a new component at `frontend/src/components/applications/VirtualApplicationList.tsx`.
    *   Implement virtualization similar to the `VirtualJobList` component.
3.  **Add virtualization to `DataTable`:**
    *   Update the `DataTable` component to support virtualization when the number of rows is greater than 100.
    *   Use `@tanstack/react-virtual` to virtualize the rows.
4.  **Performance testing:**
    *   Benchmark the rendering time before and after implementing virtualization.
    *   Measure the FPS during scrolling.
    *   Test on lower-end devices.

## 5. Optimize Caching & State Management

1.  **Review and optimize React Query configuration:**
    *   Review the current `queryClient` configuration.
    *   Optimize `staleTime` and `cacheTime` for different query types as recommended in the research.
2.  **Implement stale-while-revalidate pattern:**
    *   Configure SWR for key data endpoints to show cached data immediately while fetching fresh data.
3.  **Implement optimistic updates:**
    *   Implement optimistic updates for application status changes and job saves/unsaves.
    *   Implement a rollback mechanism on error.
4.  **Implement prefetching:**
    *   Prefetch job and application details on hover.
    *   Prefetch the next pagination page when the user scrolls near the end of the list.

## 6. Setup Performance Monitoring

1.  **Install and configure Lighthouse CI:**
    *   Install `@lhci/cli`.
    *   Create a `lighthouserc.json` configuration file.
    *   Add an npm script: `"lighthouse": "lhci autorun"`.
2.  **Implement Web Vitals reporting:**
    *   Create a `frontend/src/lib/vitals.ts` file.
    *   Implement the `reportWebVitals` function to send metrics to an analytics service.
    *   Track FCP, LCP, FID, CLS, and TTFB.
3.  **Define performance budgets:**
    *   Document the performance budgets as recommended in the research.
4.  **Add Lighthouse to CI/CD:**
    *   Create a GitHub Actions workflow for Lighthouse.
    *   Run the workflow on every pull request.
    *   Fail the build if the Performance score is less than 90.
    *   Post the Lighthouse results as a comment on the pull request.
