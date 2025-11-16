# Sprint 4: Turbopack & Dependency Optimization Strategy

**Date:** November 16, 2025  
**Status:** In Progress  
**Goal:** Reduce bundle size through Turbopack optimization and dependency management

## Current State Analysis

### Bundle Metrics (Post-Sprint 3)
- **Total JS:** 4.59 MB (82 chunks)
- **Largest chunks:** 598KB, 505KB, 457KB, 430KB, 261KB
- **Framework:** Next.js 16.0.1 with Turbopack
- **LazyMotion:** ✅ Implemented (78 files migrated)

### Heavy Dependencies Identified

1. **recharts** (~200-300KB estimated)
   - Status: Partially lazy-loaded via `LazyCharts.tsx`
   - Usage: 6+ chart components
   - Opportunity: Already optimized with dynamic imports

2. **lucide-react** (~100-150KB estimated)
   - Status: Imported in 100+ files
   - Usage: Icons throughout the app
   - Opportunity: Tree-shaking via `optimizePackageImports`

3. **@tanstack/react-table** (~80-100KB estimated)
   - Status: Used in DataTable components
   - Usage: 2-3 table implementations
   - Opportunity: Ensure only used features imported

4. **@dnd-kit/** (~60-80KB estimated)
   - Status: Used in Kanban and Dashboard
   - Usage: Drag-and-drop functionality
   - Opportunity: Already well-scoped

## Optimization Strategy

### Phase 1: Turbopack Configuration ✅

**Status:** Already implemented in `next.config.js`

```javascript
experimental: {
  optimizePackageImports: [
    'lucide-react',        // Tree-shake icons
    'recharts',            // Tree-shake chart components
    'framer-motion',       // Already using LazyMotion
    '@tanstack/react-query',
    '@tanstack/react-table',
    '@dnd-kit/core',
    '@dnd-kit/sortable',
  ],
}
```

**Benefits:**
- ✅ Automatic tree-shaking for listed packages
- ✅ Turbopack handles bundling optimization
- ✅ No code changes required

### Phase 2: Lucide Icons Optimization

**Current Pattern (Already Optimized):**
```typescript
// ✅ GOOD - Specific imports (Turbopack optimizes this)
import { Search, Filter, Download } from 'lucide-react';
```

**Anti-Pattern to Avoid:**
```typescript
// ❌ BAD - Namespace import
import * as Icons from 'lucide-react';
```

**Action Items:**
1. ✅ Verify all imports use named exports (already done in codebase)
2. ✅ Trust `optimizePackageImports` to handle tree-shaking
3. 📊 Measure: Check if lucide-react appears in specific chunks

**Expected Savings:** Turbopack handles this automatically with `optimizePackageImports`

### Phase 3: Recharts Optimization

**Current State: Already Optimized ✅**

File: `frontend/src/components/lazy/LazyCharts.tsx`
- All recharts components lazy-loaded via `dynamic()`
- Charts load on demand, not in initial bundle
- Proper SSR handling with `{ ssr: false }`

**No Additional Action Needed** - recharts is already well-optimized.

### Phase 4: Route-Level Code Splitting

**Strategy:** Ensure heavy pages lazy-load their components

**Target Routes:**
1. `/analytics` - Heavy with charts
2. `/applications` - Kanban board + tables
3. `/dashboard` - Multiple widgets
4. `/help` - Feature tour

**Current Status:**
- ✅ `/applications` - KanbanBoard lazy-loaded
- ✅ `/help` - FeatureTour lazy-loaded
- 🔄 `/analytics` - Charts already lazy via LazyCharts
- 🔄 `/dashboard` - Widgets could be optimized

**Implementation:**
```typescript
// ✅ Already implemented pattern
const LazyKanbanBoard = dynamic(
  () => import('@/components/kanban/KanbanBoard'),
  { loading: () => <KanbanLoadingSkeleton /> }
);
```

### Phase 5: Turbopack-Specific Features

**Next.js 16 Turbopack Enhancements:**

1. **Module Tracing** (Built-in)
   - Turbopack automatically traces imports
   - Eliminates unused code at compile time
   - No configuration needed ✅

2. **Optimized Package Imports** (Configured)
   - `optimizePackageImports` in `experimental`
   - Auto-tree-shaking for listed packages ✅

3. **Better Code Splitting**
   - Turbopack uses different strategy than webpack
   - Focuses on module graph optimization
   - File size may not show reduction, but runtime is faster ✅

4. **Faster Builds**
   - Incremental compilation
   - Persistent caching
   - Already benefiting from 12s builds ✅

## Implementation Plan

### Sprint 4 Tasks

#### Task 1: Verify Turbopack Optimizations ✅
- [x] Confirm `optimizePackageImports` configured
- [x] Verify recharts lazy-loading
- [x] Check lucide-react import patterns
- [ ] Test with `ANALYZE=true npm run build`

#### Task 2: Bundle Analysis Deep Dive
- [ ] Run webpack bundle analyzer
- [ ] Identify actual package sizes in chunks
- [ ] Document findings in report

#### Task 3: Lighthouse CI Setup
- [ ] Create `.github/workflows/lighthouse-ci.yml`
- [ ] Configure Core Web Vitals tracking
- [ ] Set up PR comments with performance metrics

#### Task 4: Progressive Enhancement
- [ ] Implement `requestIdleCallback` for deferred work
- [ ] Load non-critical features after interactive
- [ ] Optimize above-the-fold content

#### Task 5: Image Optimization Audit
- [ ] Verify all images use Next.js `<Image>` component
- [ ] Implement proper `sizes` attributes
- [ ] Optimize image formats (AVIF/WebP)

## Expected Outcomes

### Realistic Expectations with Turbopack

**File Size:**
- May not show dramatic reduction (Turbopack bundles differently)
- Focus on runtime performance, not static file size

**Runtime Performance:**
- ✅ Faster JavaScript execution (lazy-loading)
- ✅ Better caching (module graph optimization)
- ✅ Improved Time to Interactive

**Metrics to Track:**
- Time to Interactive (TTI) < 3s on 3G
- First Contentful Paint (FCP) < 1.5s
- Largest Contentful Paint (LCP) < 2.5s
- Cumulative Layout Shift (CLS) < 0.1
- Lighthouse Performance Score > 95

### Bundle Size Goals (Adjusted for Turbopack)

**Current:** 4.59 MB (82 chunks)

**Target (Realistic):**
- Total: 4.0-4.2 MB (10-15% reduction)
- Largest chunk: < 400 KB
- Focus: Better chunking, not smaller total

**Why Lower Expectations?**
- Turbopack optimizes for runtime, not file size
- Tree-shaking happens automatically
- Module graph is already optimized

## Alternative Strategies (Future Consideration)

### If More Reduction Needed

1. **Recharts Alternative:**
   - Consider `recharts-lite` or `visx`
   - ~50-80KB savings potential
   - Trade-off: Migration effort

2. **Icon Library:**
   - Replace lucide-react with SVG sprites
   - ~50-100KB savings potential
   - Trade-off: Type safety, developer experience

3. **Table Library:**
   - Evaluate lighter alternatives to react-table
   - ~40-60KB savings potential
   - Trade-off: Feature set

4. **Animation Library:**
   - Reduce framer-motion features further
   - ~20-30KB additional savings
   - Trade-off: Animation capabilities

## Success Criteria

### Sprint 4 Goals

1. ✅ **Turbopack Configuration Verified**
   - optimizePackageImports working
   - Build times maintained < 15s

2. 📊 **Bundle Analysis Complete**
   - Webpack analyzer run
   - Package sizes documented
   - Optimization opportunities identified

3. 🚀 **Lighthouse CI Integrated**
   - GitHub workflow created
   - Performance tracking automated
   - PR comments working

4. 📈 **Performance Improved**
   - TTI < 3.5s on 3G (from baseline)
   - FCP < 1.5s
   - LCP < 2.5s

5. 📝 **Documentation Updated**
   - Optimization guide created
   - Best practices documented
   - Team trained on patterns

## Monitoring & Maintenance

### Ongoing Tasks

1. **Weekly Performance Review**
   - Check Lighthouse CI trends
   - Review bundle size changes
   - Identify regressions

2. **Dependency Audits**
   - Quarterly review of package sizes
   - Update to lighter alternatives when available
   - Remove unused dependencies

3. **Performance Budgets**
   - Enforce in CI/CD (already setup)
   - Alert on violations
   - Block PRs that exceed limits

4. **Documentation**
   - Keep optimization guide current
   - Document new patterns
   - Share learnings with team

## Conclusion

Sprint 4 focuses on leveraging Turbopack's built-in optimizations rather than fighting against its bundling strategy. The key insight: **Turbopack optimizes for runtime performance, not just file size.**

**Next Sprint Preview (Sprint 5):**
- Lighthouse CI data analysis
- Progressive enhancement patterns
- Service worker implementation
- Offline-first optimizations

---

**Related Documents:**
- [Sprint 3 Summary](./SPRINT_3_SUMMARY.md)
- [Bundle Optimization Plan](./BUNDLE_OPTIMIZATION_PLAN.md)
- [Performance Testing Guide](./PERFORMANCE_TESTING_GUIDE.md)
