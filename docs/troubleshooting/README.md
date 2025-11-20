# Troubleshooting

> **Help Hub**: Common issues, solutions, and operations runbook.
> - Consolidates: `troubleshooting/COMMON_ISSUES.md`, `troubleshooting/RUNBOOK.md`, `/ERROR_HANDLING_GUIDE.md`

**Quick Links**: [[/index|Documentation Hub]] | [[/GETTING_STARTED|Getting Started]]

---

## Quick Fixes

### Services Won't Start
```bash
docker-compose down && docker-compose up -d
```

### Database Connection Lost
```bash
docker-compose restart backend
alembic upgrade head
```

### Frontend Build Errors
```bash
cd frontend && rm -rf .next && npm run dev
```

---

## Documentation

* **[[COMMON_ISSUES|Common Issues]]** - Frequently encountered problems and solutions
* **[[RUNBOOK|Operations Runbook]]** - Procedures for common operational tasks
* **Error Handling**: See [[/ERROR_HANDLING_GUIDE|Error Handling Guide]] (root level)

---

## Support Resources

- **Setup Issues**: [[/GETTING_STARTED#troubleshooting|Getting Started Troubleshooting]]
- **Test Failures**: [[/TESTING_GUIDE|Testing Guide]]
- **Deployment Problems**: [[/deployment/README#troubleshooting|Deployment Troubleshooting]]
- **GitHub Issues**: https://github.com/moatasim-KT/career-copilot/issues

---

**Last Updated**: November 2025
