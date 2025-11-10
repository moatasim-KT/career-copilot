# Performance Optimization TODO List

This document breaks down the performance optimization plan into actionable tasks.

## 1. Fix Build Errors [frontend] [blocker]

- [ ] **Investigate and fix import errors:**
  - [ ] In `frontend/src/components/ui/DataTable/DataTable.tsx`, correct the import of `Button2` from `@/components/ui/Button2`.
  - [ ] In `frontend/src/components/ui/DataTable/ColumnFilter.tsx`, correct the import of `Input` from `@/components/ui/Input2`.
  - [ ] In `frontend/src/components/ui/DataTable/DataTable.tsx`, correct the imports of `SelectContent`, `SelectItem`, `SelectTrigger`, and `SelectValue` from `@/components/ui/Select2`.
  - [ ] In `frontend/src/components/ui/Button.tsx`, remove or replace the import of `buttonHover` and `buttonTap` from `@/lib/animations`.
  - [ ] In `frontend/src/components/ui/Card.tsx`, remove or replace the import of `cardHover` from `@/lib/animations`.
- [ ] **Verify the build:** [test]
  - [ ] Run `npm run build` in the `frontend` directory to ensure all build errors are resolved.

## 2. Implement Code Splitting [frontend] [parallel]

- [ ] **Audit current bundle size:**
  - [ ] Run `ANALYZE=true npm run build` to generate a bundle analysis report.
  - [ ] Identify and document the largest chunks in the bundle.
- [ ] **Implement component-level code splitting:**
  - [ ] Identify heavy components (e.g., charts, rich editors, data tables).
  - [ ] Wrap heavy components with `React.lazy()` and `Suspense`.
  - [ ] Create loading fallback components.
- [ ] **Implement dynamic imports for conditional features:**
  - [ ] Identify conditionally used features (e.g., modals, dialogs).
  - [ ] Convert imports for these components to dynamic `import()`.
- [ ] **Add preload for critical routes:**
  - [ ] Identify critical user paths (e.g., `/jobs`, `/applications`, `/profile`, `/dashboard`).
  - [ ] Use `router.prefetch()` to preload these routes on link hover.
- [ ] **Set bundle size budget alerts:** [ci]
  - [ ] Configure bundle size budgets in `next.config.js`.
  - [ ] Set a warning threshold at 200KB and an error threshold at 250KB per route.
  - [ ] Add this to the CI/CD pipeline.

## 3. Optimize Images [frontend] [parallel]

- [ ] **Migrate all `<img>` tags to Next.js `<Image>`:**
  - [ ] Search the codebase for all instances of the `<img>` tag.
  - [ ] Replace them with the Next.js `<Image>` component, providing the required `width`, `height`, and `alt` props.
- [ ] **Configure responsive images:**
  - [ ] Configure image sizes in `next.config.js`.
  - [ ] Use the `sizes` prop on the `<Image>` component.
- [ ] **Optimize image formats:**
  - [ ] Configure WebP format in `next.config.js`.
  - [ ] Compress all source images to be less than 100KB.
- [ ] **Test image optimization:** [test]
  - [ ] Simulate a slow 3G network and verify that blur placeholders appear.
  - [ ] Check the Network tab to ensure that images are being served in the WebP format.

## 4. Implement List Virtualization [frontend] [parallel]

- [ ] **Create `VirtualJobList` component:**
  - [ ] Create a new component at `frontend/src/components/jobs/VirtualJobList.tsx`.
  - [ ] Use the `@tanstack/react-virtual` library to create a virtualized list.
  - [ ] Configure the virtualizer with an `estimateSize` function and an `overscan` of 5.
- [ ] **Create `VirtualApplicationList` component:**
  - [ ] Create a new component at `frontend/src/components/applications/VirtualApplicationList.tsx`.
  - [ ] Implement virtualization similar to the `VirtualJobList` component.
- [ ] **Add virtualization to `DataTable`:**
  - [ ] Update the `DataTable` component to support virtualization when the number of rows is greater than 100.
  - [ ] Use `@tanstack/react-virtual` to virtualize the rows.
- [ ] **Performance testing:** [test]
  - [ ] Benchmark the rendering time before and after implementing virtualization.
  - [ ] Measure the FPS during scrolling.
  - [ ] Test on lower-end devices.

## 5. Optimize Caching & State Management [frontend] [parallel]

- [ ] **Review and optimize React Query configuration:**
  - [ ] Review the current `queryClient` configuration.
  - [ ] Optimize `staleTime` and `cacheTime` for different query types.
- [ ] **Implement stale-while-revalidate pattern:**
  - [ ] Configure SWR for key data endpoints.
- [ ] **Implement optimistic updates:**
  - [ ] Implement optimistic updates for application status changes and job saves/unsaves.
  - [ ] Implement a rollback mechanism on error.
- [ ] **Implement prefetching:**
  - [ ] Prefetch job and application details on hover.
  - [ ] Prefetch the next pagination page when the user scrolls near the end of the list.

## 6. Setup Performance Monitoring [ci] [parallel]

- [ ] **Install and configure Lighthouse CI:**
  - [ ] Install `@lhci/cli`.
  - [ ] Create a `lighthouserc.json` configuration file.
  - [ ] Add an npm script: `"lighthouse": "lhci autorun"`.
- [ ] **Implement Web Vitals reporting:**
  - [ ] Create a `frontend/src/lib/vitals.ts` file.
  - [ ] Implement the `reportWebVitals` function to send metrics to an analytics service.
  - [ ] Track FCP, LCP, FID, CLS, and TTFB.
- [ ] **Define performance budgets:**
  - [ ] Document the performance budgets.
- [ ] **Add Lighthouse to CI/CD:**
  - [ ] Create a GitHub Actions workflow for Lighthouse.
  - [ ] Run the workflow on every pull request.
  - [ ] Fail the build if the Performance score is less than 90.
  - [ ] Post the Lighthouse results as a comment on the pull request.
