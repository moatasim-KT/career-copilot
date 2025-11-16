# Accessibility Testing Guide

## Overview

This guide covers accessibility (a11y) testing for Career Copilot, ensuring WCAG 2.1 AA compliance across all features.

## Table of Contents

- [Quick Start](#quick-start)
- [Testing Tools](#testing-tools)
- [Automated Testing](#automated-testing)
- [Manual Testing](#manual-testing)
- [WCAG 2.1 AA Checklist](#wcag-21-aa-checklist)
- [Common Issues & Fixes](#common-issues--fixes)
- [CI/CD Integration](#cicd-integration)

## Quick Start

```bash
# Install dependencies (if not already installed)
cd frontend
npm install @axe-core/puppeteer puppeteer --save-dev

# Run automated accessibility audit
npm run accessibility:audit

# Run with verbose output
npm run accessibility:audit:verbose

# Run specific page
npm run accessibility:audit -- --url=http://localhost:3000/jobs

# Run unit tests with a11y checks
npm run test:a11y
```

## Testing Tools

### 1. axe-core (Automated)
- **Purpose**: Automated WCAG 2.1 testing
- **Usage**: Integrated in audit script and unit tests
- **Coverage**: ~57% of WCAG 2.1 AA rules

### 2. jest-axe (Unit Tests)
- **Purpose**: Component-level accessibility testing
- **Location**: `src/components/**/__tests__/*.a11y.test.tsx`
- **Example**:
```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Button should have no a11y violations', async () => {
  const { container } = render(<Button>Click me</Button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### 3. eslint-plugin-jsx-a11y (Static Analysis)
- **Purpose**: Catch a11y issues during development
- **Configuration**: Already enabled in ESLint config
- **Checks**: ARIA roles, keyboard accessibility, labels, etc.

### 4. Screen Readers (Manual)
- **NVDA** (Windows - Free): https://www.nvaccess.org/
- **JAWS** (Windows - Commercial): https://www.freedomscientific.com/products/software/jaws/
- **VoiceOver** (macOS/iOS - Built-in): Cmd+F5 to enable
- **TalkBack** (Android - Built-in)

### 5. Browser DevTools
- **Chrome DevTools**: Lighthouse Accessibility Audit
- **Firefox DevTools**: Accessibility Inspector
- **Edge DevTools**: Issues tab with a11y checks

## Automated Testing

### Full Site Audit

Run comprehensive audit across all major pages:

```bash
npm run accessibility:audit
```

**Pages Audited:**
- Dashboard (/)
- Jobs List (/jobs)
- Job Details (/jobs/:id)
- Applications (/applications)
- Application Details (/applications/:id)
- Content Generator (/content)
- Interview Prep (/interview)
- Analytics (/analytics)
- Settings (/settings)
- Help (/help)

**Output:**
- JSON Report: `frontend/reports/accessibility/accessibility-audit-YYYY-MM-DD.json`
- Markdown Report: `frontend/reports/accessibility/accessibility-audit-YYYY-MM-DD.md`

### Violation Severity Levels

1. **🔴 CRITICAL**: Blocks users completely (e.g., no keyboard access)
2. **🟠 SERIOUS**: Major barrier (e.g., missing alt text on images)
3. **🟡 MODERATE**: Noticeable issue (e.g., low contrast)
4. **🟢 MINOR**: Inconvenience (e.g., missing ARIA labels)

### CI/CD Integration

Create `.github/workflows/accessibility.yml`:

```yaml
name: Accessibility Audit

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Build application
        working-directory: frontend
        run: npm run build
      
      - name: Start application
        working-directory: frontend
        run: |
          npm start &
          npx wait-on http://localhost:3000 --timeout 60000
      
      - name: Run accessibility audit
        working-directory: frontend
        run: npm run accessibility:audit
      
      - name: Upload accessibility report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: accessibility-report
          path: frontend/reports/accessibility/
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync(
              'frontend/reports/accessibility/accessibility-audit-*.json',
              'utf8'
            ));
            
            const { summary } = report;
            const status = summary.criticalViolations === 0 && summary.seriousViolations === 0 
              ? '✅ PASS' 
              : '❌ FAIL';
            
            const comment = `## 🔍 Accessibility Audit Results
            
            **Status:** ${status}
            
            | Severity   | Count                         |
            | ---------- | ----------------------------- |
            | 🔴 Critical | ${summary.criticalViolations} |
            | 🟠 Serious  | ${summary.seriousViolations}  |
            | 🟡 Moderate | ${summary.moderateViolations} |
            | 🟢 Minor    | ${summary.minorViolations}    |
            
            **Pages Audited:** ${summary.totalPages}
            **Total Violations:** ${summary.totalViolations}
            `;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

## Manual Testing

### Keyboard Navigation

Test that all interactive elements are accessible via keyboard:

```
Tab          - Move forward through interactive elements
Shift+Tab    - Move backward
Enter/Space  - Activate buttons/links
Arrow Keys   - Navigate within components (dropdowns, tabs, etc.)
Esc          - Close modals/dropdowns
```

**Checklist:**
- [ ] All interactive elements are reachable via Tab
- [ ] Focus indicator is visible on all elements
- [ ] Tab order follows logical reading order
- [ ] No keyboard traps (can Tab out of all components)
- [ ] Modals can be closed with Esc
- [ ] Dropdowns navigate with arrow keys
- [ ] Form submission works with Enter key

### Screen Reader Testing

#### VoiceOver (macOS)

```bash
# Enable: Cmd + F5
# Navigate: VO + Arrow keys (VO = Ctrl + Option)
# Interact: VO + Space
# Read all: VO + A
# Stop: Ctrl
```

**Test scenarios:**
1. Navigate through dashboard - verify all sections are announced
2. Complete job application form - verify labels and errors are read
3. Use data tables - verify column headers and cell relationships
4. Interact with modals - verify announcements and dismissal
5. Navigate between pages - verify page title changes are announced

#### NVDA (Windows)

```bash
# Start: Ctrl + Alt + N
# Stop: NVDA + Q
# Navigate: Arrow keys
# Read all: NVDA + Down Arrow
# Forms mode: NVDA + Space
```

### Color Contrast

Use browser DevTools or online tools to verify contrast ratios:

**WCAG AA Requirements:**
- Normal text (< 18pt): 4.5:1
- Large text (≥ 18pt or ≥ 14pt bold): 3:1
- UI components and graphical objects: 3:1

**Tools:**
- Chrome DevTools: Inspect element → Accessibility pane
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/)

### Focus Management

Verify focus behavior:

- [ ] Focus moves to error messages on form submission
- [ ] Focus moves to modal content when opened
- [ ] Focus returns to trigger element when modal closes
- [ ] Skip links move focus to main content
- [ ] Focus is never on non-interactive elements

## WCAG 2.1 AA Checklist

### Perceivable

#### 1.1 Text Alternatives
- [ ] All images have alt text
- [ ] Decorative images have empty alt (`alt=""`)
- [ ] Complex images (charts, graphs) have detailed descriptions
- [ ] Icons have accessible labels

#### 1.2 Time-based Media
- [ ] Videos have captions
- [ ] Audio content has transcripts
- [ ] Pre-recorded media has audio descriptions

#### 1.3 Adaptable
- [ ] Content structure uses semantic HTML (`<nav>`, `<main>`, `<article>`, etc.)
- [ ] Tables use proper markup (`<th>`, `scope`, `<caption>`)
- [ ] Form inputs have associated `<label>` elements
- [ ] Reading order is logical
- [ ] Content does not rely solely on sensory characteristics (shape, color, size)

#### 1.4 Distinguishable
- [ ] Color is not the only means of conveying information
- [ ] Text has sufficient contrast (4.5:1 for normal, 3:1 for large)
- [ ] UI components have 3:1 contrast against adjacent colors
- [ ] Text can be resized to 200% without loss of functionality
- [ ] Text is not justified
- [ ] Line height is at least 1.5
- [ ] Paragraph spacing is at least 2x font size

### Operable

#### 2.1 Keyboard Accessible
- [ ] All functionality available via keyboard
- [ ] No keyboard traps
- [ ] Keyboard shortcuts don't conflict with assistive technology
- [ ] Focus indicator is visible

#### 2.2 Enough Time
- [ ] Time limits can be extended or disabled
- [ ] Moving/blinking content can be paused
- [ ] Auto-updating content can be paused
- [ ] No time limits on user actions (or can be extended)

#### 2.3 Seizures and Physical Reactions
- [ ] No content flashes more than 3 times per second
- [ ] Animation can be disabled (prefers-reduced-motion)

#### 2.4 Navigable
- [ ] Skip links provided to bypass repetitive content
- [ ] Page titles are descriptive
- [ ] Focus order is logical
- [ ] Link purpose is clear from text or context
- [ ] Multiple ways to find pages (nav, search, sitemap)
- [ ] Headings and labels are descriptive
- [ ] Focus indicator is visible

#### 2.5 Input Modalities
- [ ] Pointer gestures have keyboard alternatives
- [ ] Pointer cancellation available (up-event activation)
- [ ] Labels match accessible names
- [ ] Motion actuation can be disabled

### Understandable

#### 3.1 Readable
- [ ] Page language declared (`lang` attribute)
- [ ] Language changes marked up (`lang` on inline elements)
- [ ] Unusual words defined
- [ ] Abbreviations expanded on first use

#### 3.2 Predictable
- [ ] Focus doesn't cause unexpected context changes
- [ ] Input doesn't cause unexpected context changes
- [ ] Navigation is consistent across pages
- [ ] Components are identified consistently

#### 3.3 Input Assistance
- [ ] Error messages are clear and specific
- [ ] Labels and instructions provided for inputs
- [ ] Error suggestions provided
- [ ] Form submissions can be reviewed before submitting
- [ ] Help is available

### Robust

#### 4.1 Compatible
- [ ] HTML validates
- [ ] Elements have unique IDs
- [ ] ARIA roles, states, and properties used correctly
- [ ] Status messages announced to screen readers

## Common Issues & Fixes

### Missing Alt Text

**Issue:** Images without alt attributes
```html
❌ <img src="logo.png">
✅ <img src="logo.png" alt="Career Copilot Logo">
✅ <img src="decoration.png" alt="" role="presentation">
```

### Low Color Contrast

**Issue:** Text doesn't meet 4.5:1 contrast ratio
```css
❌ color: #999; background: #fff; /* 2.8:1 */
✅ color: #666; background: #fff; /* 5.7:1 */
```

### Missing Form Labels

**Issue:** Inputs without associated labels
```html
❌ <input type="text" placeholder="Enter name">
✅ <label for="name">Name</label>
   <input id="name" type="text">
```

### Missing ARIA Labels

**Issue:** Icon buttons without accessible names
```html
❌ <button><Icon name="close" /></button>
✅ <button aria-label="Close dialog"><Icon name="close" /></button>
```

### Keyboard Traps

**Issue:** Focus gets stuck in component
```typescript
// ❌ Modal without proper focus management
const Modal = () => <div>{children}</div>;

// ✅ Modal with focus trap and restoration
const Modal = () => {
  const previousFocus = useRef(document.activeElement);
  
  useEffect(() => {
    // Move focus to modal
    modalRef.current?.focus();
    
    // Restore focus on unmount
    return () => previousFocus.current?.focus();
  }, []);
  
  return (
    <div 
      ref={modalRef} 
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === 'Escape') closeModal();
      }}
    >
      {children}
    </div>
  );
};
```

### Non-Semantic HTML

**Issue:** Using divs for everything
```html
❌ <div onclick="doSomething()">Click me</div>
✅ <button onClick={doSomething}>Click me</button>

❌ <div id="navigation">...</div>
✅ <nav>...</nav>
```

## Resources

### Official Guidelines
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Section 508](https://www.section508.gov/)

### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Browser Extension](https://wave.webaim.org/extension/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Pa11y](https://pa11y.org/)

### Learning Resources
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [Inclusive Components](https://inclusive-components.design/)

### Component Libraries
- [Radix UI](https://www.radix-ui.com/) - Accessible primitives
- [Headless UI](https://headlessui.com/) - Accessible components
- [Reach UI](https://reach.tech/) - Accessible React components

## Maintenance

### Regular Tasks

- **Weekly**: Run automated audit on develop branch
- **Per PR**: Review a11y impact of UI changes
- **Monthly**: Conduct manual keyboard/screen reader testing
- **Quarterly**: Full WCAG audit with manual testing
- **Annually**: Third-party accessibility audit

### Continuous Improvement

1. Monitor axe-core violations trends
2. Add a11y tests for new components
3. Keep dependencies updated (@axe-core/react, jest-axe, eslint-plugin-jsx-a11y)
4. Incorporate user feedback from assistive technology users
5. Stay updated with WCAG 2.2 and future versions
