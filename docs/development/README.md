# Development Documentation

> **Developer Hub**: Development guides, patterns, and best practices.

**Quick Links**: [[/index|Documentation Hub]] | [[/testing/TESTING_GUIDE|Testing Guide]]

---

## Key Documents

* **[[DEVELOPER_GUIDE|Developer Guide]]** - Comprehensive development documentation
* **[[DESIGN_SYSTEM|Design System]]** - UI/UX design guidelines and component standards
* **[[COMPONENT_LIBRARY_INVENTORY|Component Library]]** - Complete component catalog
* **[[ERROR_HANDLING_GUIDE|Error Handling]]** - Error handling patterns and best practices
* **[[DEVELOPMENT|Development Workflow]]** - Git workflow, branching, commits
* **[[workflow|Development Practices]]** - Development best practices
* **[[code-patterns|Code Patterns]]** - Common patterns and conventions
* **[[workflow-documentation|Workflow Documentation]]** - Process documentation

---

## Quick Reference

### Development Workflow
```bash
# Start development environment
docker-compose up -d

# Backend development
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Frontend development
cd frontend && npm run dev
```

### Code Quality
```bash
# Run all quality checks
make quality-check

# Format code
make format

# Run linters
make lint
```

---

## Related Documentation

- **Getting Started**: [[/GETTING_STARTED|Setup Guide]]
- **Testing**: [[/TESTING_GUIDE|Testing Guide]]
- **Architecture**: [[/architecture/README|Architecture Docs]]
- **Contributing**: [[/CONTRIBUTING|Contributing Guidelines]]

---

**Last Updated**: November 2025
