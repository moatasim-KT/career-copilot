# Testing Documentation

> **Testing Hub**: All testing documentation, strategies, and guides.

**Quick Links**: [[/index|Documentation Hub]] | [[/development/DEVELOPER_GUIDE|Developer Guide]]

---

## Testing Documentation

* **[[TESTING_GUIDE|Testing Guide]]** - Comprehensive testing documentation
  - Testing pyramid
  - Backend testing (pytest)
  - Frontend testing (Jest, Playwright)
  - Accessibility testing (jest-axe, WCAG 2.1 AA)
  - End-to-end testing
  - Performance testing
  - CI/CD integration
* **[[ACCESSIBILITY_TESTING|Accessibility Testing]]** - Detailed accessibility testing guide

---

## Quick Commands

```bash
# Run all tests
make test

# Backend tests
cd backend && pytest -v

# Frontend tests
cd frontend && npm test

# Accessibility tests
cd frontend && npm run test:a11y

# E2E tests
cd frontend && npm run test:e2e
```

---

## Related Documentation

- **Development**: [[/development/DEVELOPER_GUIDE|Developer Guide]]
- **Architecture**: [[/architecture/README|Architecture Overview]]
- **Troubleshooting**: [[/troubleshooting/README|Troubleshooting Hub]]

---

**Last Updated**: November 2025
