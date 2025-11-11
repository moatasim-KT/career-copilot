# Performance Budgets

This document defines the performance budgets for the Career Copilot frontend application. These budgets ensure that the application maintains excellent performance and user experience across all devices and network conditions.

## Overview

Performance budgets are limits set on metrics that affect site performance. They help prevent performance regressions by failing builds when budgets are exceeded. Our budgets are based on industry best practices and Google's Core Web Vitals recommendations.

## Core Web Vitals Budgets

Core Web Vitals are the essential metrics that measure real-world user experience. These are the primary metrics we optimize for.

### First Contentful Paint (FCP)

**Budget: < 1.5 seconds**

FCP measures the time from when the page starts loading to when any part of the page's content is rendered on the screen.

- **Good**: < 1.8s
- **Needs Improvement**: 1.8s - 3.0s
- **Poor**: > 3.0s

**Why this matters**: Users want to see content quickly. A fast FCP reassures users that the page is loading.

**How to achieve**:
- Minimize render-blocking resources (CSS, JavaScript)
- Use code splitting to load only necessary code
- Optimize font loading with `font-display: swap`
- Preload critical resources
- Use server-side rendering (SSR) or static generation (SSG)

### Largest Contentful Paint (LCP)

**Budget: < 2.5 seconds**

LCP measures the time from when the page starts loading to when the largest text block or image element is rendered on the screen.

- **Good**: < 2.5s
- **Needs Improvement**: 2.5s - 4.0s
- **Poor**: > 4.0s

**Why this matters**: LCP is a key indicator of perceived load speed. It marks the point when the main content is visible to users.

**How to achieve**:
- Optimize images (use Next.js Image component, WebP format, proper sizing)
- Minimize server response time (TTFB < 800ms)
- Eliminate render-blocking resources
- Use CDN for static assets
- Implement resource hints (preload, prefetch)

### First Input Delay (FID)

**Budget: < 100 milliseconds**

FID measures the time from when a user first interacts with your site (clicks a link, taps a button) to when the browser is able to respond to that interaction.

- **Good**: < 100ms
- **Needs Improvement**: 100ms - 300ms
- **Poor**: > 300ms

**Why this matters**: FID quantifies the experience users feel when trying to interact with unresponsive pages. A low FID ensures the page is usable.

**How to achieve**:
- Break up long JavaScript tasks (< 50ms)
- Use code splitting and lazy loading
- Minimize JavaScript execution time
- Use web workers for heavy computations
- Defer non-critical JavaScript

**Note**: FID is being replaced by INP (Interaction to Next Paint) in 2024. We track both metrics.

### Cumulative Layout Shift (CLS)

**Budget: < 0.1**

CLS measures the sum of all unexpected layout shifts that occur during the entire lifespan of the page. A layout shift occurs when a visible element changes its position from one rendered frame to the next.

- **Good**: < 0.1
- **Needs Improvement**: 0.1 - 0.25
- **Poor**: > 0.25

**Why this matters**: Unexpected layout shifts are frustrating and can cause users to accidentally click the wrong thing.

**How to achieve**:
- Always include size attributes on images and videos
- Reserve space for ads and embeds
- Avoid inserting content above existing content
- Use CSS transforms for animations instead of properties that trigger layout
- Preload fonts and use `font-display: optional` or `swap`

### Time to First Byte (TTFB)

**Budget: < 800 milliseconds**

TTFB measures the time from the start of the navigation to when the browser receives the first byte of the response from the server.

- **Good**: < 800ms
- **Needs Improvement**: 800ms - 1800ms
- **Poor**: > 1800ms

**Why this matters**: A fast TTFB is the foundation for all other performance metrics. It indicates a responsive server.

**How to achieve**:
- Use a CDN for static assets
- Implement server-side caching
- Optimize database queries
- Use edge functions for dynamic content
- Minimize server processing time

### Interaction to Next Paint (INP)

**Budget: < 200 milliseconds**

INP measures the latency of all interactions throughout the page lifecycle. It's the successor to FID and provides a more comprehensive view of responsiveness.

- **Good**: < 200ms
- **Needs Improvement**: 200ms - 500ms
- **Poor**: > 500ms

**Why this matters**: INP captures the full interaction experience, not just the first input. It ensures the page remains responsive throughout the user's visit.

**How to achieve**:
- Same strategies as FID
- Optimize event handlers
- Debounce/throttle frequent events
- Use passive event listeners
- Minimize main thread work

## Lighthouse Score Budgets

Lighthouse provides comprehensive audits across multiple categories. We set minimum scores for each category.

### Performance Score

**Budget: ≥ 95 (out of 100)**

The Performance score is a weighted average of multiple performance metrics.

**Metric Weights**:
- LCP: 25%
- TBT (Total Blocking Time): 30%
- FCP: 10%
- Speed Index: 10%
- TTI (Time to Interactive): 10%
- CLS: 15%

### Accessibility Score

**Budget: ≥ 95 (out of 100)**

The Accessibility score measures how well the site follows accessibility best practices.

**Key areas**:
- ARIA attributes
- Color contrast (minimum 4.5:1 for normal text, 3:1 for large text)
- Keyboard navigation
- Screen reader compatibility
- Form labels and descriptions

### Best Practices Score

**Budget: ≥ 95 (out of 100)**

The Best Practices score measures adherence to web development best practices.

**Key areas**:
- HTTPS usage
- No browser errors in console
- Proper image aspect ratios
- No deprecated APIs
- Secure connections

### SEO Score

**Budget: ≥ 90 (out of 100)**

The SEO score measures how well the site is optimized for search engine results.

**Key areas**:
- Meta tags (title, description)
- Semantic HTML
- Mobile-friendly
- Crawlable links
- Valid structured data

## Bundle Size Budgets

Bundle size directly impacts load time, especially on slower networks. We set strict limits on JavaScript bundle sizes.

### Initial Bundle

**Budget: < 150 KB (gzipped)**

The initial bundle is the JavaScript required to render the first page. This should be as small as possible.

**Current size**: Check with `npm run bundle:check`

**How to achieve**:
- Use code splitting
- Lazy load non-critical components
- Tree-shake unused code
- Minimize dependencies
- Use dynamic imports

### Route Bundles

**Budget: < 50 KB per route (gzipped)**

Each route should have its own bundle that loads only the code needed for that route.

**How to achieve**:
- Use Next.js automatic code splitting
- Lazy load route-specific components
- Share common code in shared chunks
- Avoid importing large libraries in route files

### Total JavaScript

**Budget: < 250 KB (gzipped)**

The total JavaScript across all bundles should not exceed this limit.

**How to achieve**:
- Audit dependencies regularly
- Remove unused dependencies
- Use lighter alternatives (e.g., date-fns instead of moment.js)
- Implement virtual scrolling for large lists
- Use CSS instead of JavaScript for animations when possible

### Total Page Weight

**Budget: < 512 KB (all resources)**

The total weight of all resources (HTML, CSS, JS, images, fonts) for a page.

**How to achieve**:
- Optimize images (WebP, proper sizing, lazy loading)
- Minimize CSS (remove unused styles)
- Use system fonts or subset custom fonts
- Compress all text resources (gzip/brotli)
- Lazy load below-the-fold content

## Additional Performance Metrics

### Speed Index

**Budget: < 3.0 seconds**

Speed Index measures how quickly content is visually displayed during page load.

- **Good**: < 3.4s
- **Needs Improvement**: 3.4s - 5.8s
- **Poor**: > 5.8s

### Time to Interactive (TTI)

**Budget: < 3.5 seconds**

TTI measures the time from when the page starts loading to when it's fully interactive.

- **Good**: < 3.8s
- **Needs Improvement**: 3.8s - 7.3s
- **Poor**: > 7.3s

### Total Blocking Time (TBT)

**Budget: < 200 milliseconds**

TBT measures the total time between FCP and TTI where the main thread was blocked long enough to prevent input responsiveness.

- **Good**: < 200ms
- **Needs Improvement**: 200ms - 600ms
- **Poor**: > 600ms

### DOM Size

**Budget: < 1500 nodes**

The total number of DOM nodes on the page. Large DOMs increase memory usage and slow down rendering.

**How to achieve**:
- Use virtualization for long lists
- Lazy load off-screen content
- Simplify component structure
- Remove unnecessary wrapper elements

## Network Conditions

Our budgets are tested under the following network conditions:

### Desktop (Default)

- **Connection**: Fast 3G
- **RTT**: 40ms
- **Throughput**: 10 Mbps
- **CPU**: No throttling

### Mobile

- **Connection**: Slow 3G
- **RTT**: 150ms
- **Throughput**: 1.6 Mbps
- **CPU**: 4x slowdown

### Slow Network

- **Connection**: Slow 3G
- **RTT**: 300ms
- **Throughput**: 400 Kbps
- **CPU**: 6x slowdown

## Monitoring and Enforcement

### Continuous Monitoring

We monitor performance continuously through:

1. **Lighthouse CI**: Runs on every pull request
2. **Real User Monitoring (RUM)**: Web Vitals from actual users
3. **Synthetic Monitoring**: Scheduled Lighthouse audits
4. **Bundle Size Checks**: Automated checks on every build

### Enforcement

Performance budgets are enforced through:

1. **CI/CD Pipeline**: Builds fail if budgets are exceeded
2. **Pre-commit Hooks**: Local checks before committing
3. **Code Review**: Performance considerations in reviews
4. **Regular Audits**: Weekly performance reviews

### Budget Violations

When a budget is violated:

1. **Investigate**: Identify what caused the regression
2. **Fix**: Implement optimizations to meet the budget
3. **Document**: If budget adjustment is needed, document why
4. **Review**: Team review before adjusting budgets

## Performance Optimization Checklist

Use this checklist to ensure you're following performance best practices:

### Images

- [ ] Use Next.js Image component for all images
- [ ] Specify width and height for all images
- [ ] Use WebP format (automatic with Next.js Image)
- [ ] Implement lazy loading for below-the-fold images
- [ ] Use appropriate image sizes (don't load 4K images for thumbnails)
- [ ] Compress images (< 100KB for most images)

### JavaScript

- [ ] Use code splitting for large components
- [ ] Lazy load non-critical components
- [ ] Minimize third-party scripts
- [ ] Defer non-critical JavaScript
- [ ] Use tree-shaking to remove unused code
- [ ] Avoid large dependencies (check bundle size impact)

### CSS

- [ ] Remove unused CSS
- [ ] Minimize CSS file size
- [ ] Use CSS-in-JS efficiently (avoid runtime styles)
- [ ] Inline critical CSS
- [ ] Use CSS containment for isolated components

### Fonts

- [ ] Use system fonts when possible
- [ ] Subset custom fonts (include only needed characters)
- [ ] Use `font-display: swap` or `optional`
- [ ] Preload critical fonts
- [ ] Limit number of font weights and styles

### Data Fetching

- [ ] Use React Query for caching
- [ ] Implement stale-while-revalidate pattern
- [ ] Prefetch data for likely next pages
- [ ] Use pagination for large datasets
- [ ] Implement optimistic updates

### Rendering

- [ ] Use Server Components when possible (Next.js 13+)
- [ ] Implement static generation (SSG) for static pages
- [ ] Use incremental static regeneration (ISR) for semi-static pages
- [ ] Minimize client-side JavaScript
- [ ] Use virtualization for long lists

## Resources

### Tools

- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [WebPageTest](https://www.webpagetest.org/)
- [Chrome DevTools Performance Panel](https://developer.chrome.com/docs/devtools/performance/)
- [Next.js Bundle Analyzer](https://www.npmjs.com/package/@next/bundle-analyzer)
- [web-vitals Library](https://github.com/GoogleChrome/web-vitals)

### Documentation

- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse Scoring](https://web.dev/performance-scoring/)
- [Next.js Performance](https://nextjs.org/docs/advanced-features/measuring-performance)
- [React Performance](https://react.dev/learn/render-and-commit)

### Learning

- [web.dev Performance](https://web.dev/fast/)
- [MDN Performance](https://developer.mozilla.org/en-US/docs/Web/Performance)
- [Google Performance Best Practices](https://developers.google.com/web/fundamentals/performance/why-performance-matters)

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-11-11 | 1.0 | Initial performance budgets defined | System |

## Budget Review Schedule

Performance budgets should be reviewed:

- **Quarterly**: Review all budgets and adjust based on data
- **After Major Features**: Review impact of new features
- **When Violated**: Investigate and fix or adjust budget
- **Industry Changes**: Update based on new recommendations

## Notes

- These budgets are targets, not absolute limits. Context matters.
- Real user data should inform budget adjustments.
- Performance is a feature, not an afterthought.
- Small improvements compound over time.
- Measure, optimize, repeat.

---

**Last Updated**: November 11, 2024  
**Next Review**: February 11, 2025
