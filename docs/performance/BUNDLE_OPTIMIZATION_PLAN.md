
# Frontend Bundle Optimization Plan

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Migration Guide
- [[DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

## Current State (Nov 16, 2025)

**Total Bundle Size:** 4.7 MB uncompressed JavaScript
**Target:** < 250KB gzipped per route

### Largest Chunks Identified
1. `54becc2b1042c86d.js` - 598 KB
2. `48bdd8cd9886d65b.js` - 505 KB  
3. `a88b19cfc6e3b7e5.js` - 457 KB
4. `fede1bbbda7dc551.js` - 430 KB
5. `548821ed054b9702.js` - 261 KB

## Heavy Dependencies Analysis

### Major Contributors (from grep analysis)

1. **framer-motion** (~200KB)
   - Used in: Kanban, animations, onboarding wizard, feature tours, modals
   - **Solution**: Lazy load animation-heavy components

2. **lucide-react** (tree-shakeable but heavily imported)
   - Used extensively across all components
   - **Solution**: Already tree-shakeable, but ensure individual icon imports

3. **@tanstack/react-table** (~100KB)
   - Used in: JobTableView, ApplicationsTable  
   - **Solution**: Lazy load table views, use dynamic imports

4. **recharts** (not found in grep but likely in analytics)
   - Likely used in: AnalyticsPage, dashboard widgets
   - **Solution**: Lazy load chart components

## Optimization Strategy

### Phase 1: Code Splitting Heavy Features (Priority: High)

#### 1.1 Onboarding Wizard
**Impact:** ~150-200KB
```tsx
// Before: Direct import
import OnboardingWizard from '@/components/onboarding/OnboardingWizard';

// After: Dynamic import
const OnboardingWizard = dynamic(
  () => import('@/components/onboarding/OnboardingWizard'),
  { loading: () => <LoadingSpinner /> }
);
```

**Files to update:**
- `src/app/page.tsx` or wherever onboarding is triggered
- Show loading state during import

#### 1.2 Analytics & Charts
**Impact:** ~120-180KB
```tsx
// Lazy load entire analytics page
const AnalyticsContent = dynamic(
  () => import('@/components/pages/AnalyticsPage'),
  { loading: () => <AnalyticsLoadingSkeleton /> }
);
```

**Files to update:**
- `src/app/analytics/page.tsx`
- Create analytics loading skeleton

#### 1.3 Kanban View
**Impact:** ~100-150KB (framer-motion + drag-drop)
```tsx
const ApplicationKanban = dynamic(
  () => import('@/components/pages/ApplicationKanban'),
  { loading: () => <KanbanLoadingSkeleton /> }
);
```

**Files to update:**
- `src/app/applications/page.tsx`
- Create kanban loading skeleton

#### 1.4 Feature Tours & Help System
**Impact:** ~80-120KB
```tsx
const FeatureTour = dynamic(
  () => import('@/components/help/FeatureTour'),
  { ssr: false } // Client-only component
);
```

**Files to update:**
- Components that trigger feature tours
- Mark as client-only (no SSR needed)

### Phase 2: Optimize Dependencies (Priority: Medium)

#### 2.1 Framer Motion - Tree Shaking
**Current:** Importing from main package
```tsx
import { motion, AnimatePresence } from 'framer-motion';
```

**Optimized:** Use minimal motion for simpler animations
```tsx
// For simple animations, use CSS instead
import { m, LazyMotion, domAnimation } from 'framer-motion';
```

**Files to update:**
- All files using framer-motion (50+ files)
- Replace `motion` with `m` and wrap with `LazyMotion`

#### 2.2 Lucide Icons - Audit Usage
**Current:** ~500+ icon imports across codebase
**Action:** Ensure we're not importing the entire icon set anywhere

Verify all imports follow pattern:
```tsx
import { Icon1, Icon2 } from 'lucide-react'; // ✅ Tree-shakeable
// NOT: import * as Icons from 'lucide-react'; // ❌ Imports everything
```

#### 2.3 React Table - Lazy Load
**Current:** Imported in table views
**Action:** Only load when table view is selected

```tsx
// In JobsPage where table/list toggle exists
const JobTableView = dynamic(
  () => import('@/components/pages/JobTableView'),
  { loading: () => <TableLoadingSkeleton /> }
);
```

### Phase 3: Next.js Configuration (Priority: High)

#### 3.1 Enable Optimized Package Imports
Update `next.config.js`:

```javascript
experimental: {
  optimizePackageImports: [
    'lucide-react',
    '@tanstack/react-table',
    'recharts'
  ],
}
```

#### 3.2 Review Chunk Strategy
Currently chunks are large. Consider:

```javascript
webpack: (config, { isServer }) => {
  if (!isServer) {
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        default: false,
        vendors: false,
        // Separate large libraries
        framerMotion: {
          name: 'framer-motion',
          test: /[\\/]node_modules[\\/]framer-motion[\\/]/,
          priority: 40,
        },
        recharts: {
          name: 'recharts',
          test: /[\\/]node_modules[\\/]recharts[\\/]/,
          priority: 40,
        },
        // Common components
        commons: {
          name: 'commons',
          minChunks: 2,
          priority: 20,
        },
      },
    };
  }
  return config;
}
```

### Phase 4: Route-Level Optimization (Priority: Medium)

#### 4.1 Pages to Optimize First
Based on user flow priority:

1. **Dashboard** (`/dashboard`)
   - Remove heavy components from initial load
   - Lazy load charts and analytics widgets

2. **Jobs Page** (`/jobs`)
   - Keep list view lightweight
   - Lazy load table view and filters

3. **Applications** (`/applications`)
   - Lazy load kanban view
   - Keep list view as default

4. **Analytics** (`/analytics`)
   - Entire page should be lazy loaded
   - Heavy chart dependencies

#### 4.2 Demo/Test Pages
These can be aggressively code-split:
- `/button-glow-demo`
- `/glass-morphism-test`
- `/image-quality-test`
- `/responsive-images-demo`
- `/prefetch-demo`

**Action:** Move all demo pages to dynamic imports

### Phase 5: Asset Optimization (Priority: Low)

#### 5.1 Images
- Verify all images use Next.js `<Image>` component
- Add `priority` prop for above-fold images
- Use `loading="lazy"` for below-fold

#### 5.2 Fonts
- Verify font subsetting
- Check font-display strategy
- Preload critical fonts

## Implementation Order

### Sprint 1: Quick Wins (Week 1)
- [ ] Enable `optimizePackageImports` in next.config.js
- [ ] Lazy load OnboardingWizard
- [ ] Lazy load AnalyticsPage
- [ ] Lazy load ApplicationKanban
- [ ] Create loading skeletons for lazy components

### Sprint 2: Heavy Lifting (Week 2)
- [ ] Convert framer-motion to LazyMotion pattern
- [ ] Implement custom webpack splitChunks config
- [ ] Lazy load demo/test pages
- [ ] Add route-level performance monitoring

### Sprint 3: Polish (Week 3)
- [ ] Audit and optimize remaining heavy pages
- [ ] Implement progressive enhancement
- [ ] Add bundle size budgets to CI/CD
- [ ] Document bundle optimization guidelines

## Success Metrics

### Target Metrics (Post-Optimization)
- Total bundle size: < 2 MB (from 4.7 MB) = **58% reduction**
- Largest chunk: < 150 KB (from 598 KB) = **75% reduction**  
- First Load JS per route: < 250 KB gzipped
- Lighthouse Performance score: > 95
- Time to Interactive (TTI): < 3s on 3G

### Monitoring
- Run `npm run build` to check bundle sizes
- Run Lighthouse CI on every PR
- Set up bundle size monitoring in GitHub Actions
- Alert on bundle size regressions > 10KB

## CI/CD Integration

### Bundle Size Check Action
```yaml
- name: Check bundle size
  run: |
    npm run build
    node scripts/check-bundle-size.js --max-size=250
```

### Performance Budget
Add to `.lighthouserc.js`:
```javascript
budgets: [{
  path: '/*',
  resourceSizes: [{
    resourceType: 'script',
    budget: 250 // KB
  }]
}]
```

## Next Steps

1. **Immediate:** Enable optimizePackageImports (5 min)
2. **Today:** Implement lazy loading for top 4 heavy components (2-3 hours)
3. **This Week:** Migrate framer-motion pattern (4-6 hours)
4. **This Sprint:** Complete Phase 1-3 optimizations

## Resources

- [Next.js Code Splitting](https://nextjs.org/docs/app/building-your-application/optimizing/lazy-loading)
- [Framer Motion Performance](https://www.framer.com/motion/guide-reduce-bundle-size/)
- [Bundle Size Optimization Guide](https://nextjs.org/docs/app/building-your-application/optimizing/package-bundling)
