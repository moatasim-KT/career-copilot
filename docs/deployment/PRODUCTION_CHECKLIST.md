# Production Deployment Checklist

This checklist should be followed before every deployment to production to ensure a smooth and safe release.

## Pre-Deployment

- [ ] All new features have been tested in a staging environment.
- [ ] All new features have been approved by the product owner.
- [ ] All new code has been reviewed and approved by at least one other developer.
- [ ] All new code is covered by unit and integration tests.
- [ ] All tests are passing in the CI/CD pipeline.
- [ ] The application builds successfully.
- [ ] All required environment variables are set in the production environment.
- [ ] A database backup has been created (if applicable).
- [ ] The rollback plan has been reviewed and is up-to-date.

## Deployment

- [ ] The application has been deployed to production.
- [ ] The new version is live and accessible to users.

## Post-Deployment

- [ ] The production environment is being monitored for errors.
- [ ] Analytics are being monitored to ensure the new features are being used as expected.
- [ ] The deployment has been communicated to the team.
