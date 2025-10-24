describe('Job Management Workflow', () => {
  beforeEach(() => {
    // Assuming a test user exists or is created via API
    cy.visit('http://localhost:3000/login');
    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="password"]').type('testpassword');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard'); // Or wherever successful login redirects
    cy.visit('http://localhost:3000/jobs');
  });

  it('should allow adding a new job', () => {
    cy.get('button').contains('Add Job').click();
    cy.get('h2').contains('Add New Job').should('be.visible');

    cy.get('input[placeholder="Enter company name"]').type('Cypress Test Company');
    cy.get('input[placeholder="Enter job title"]').type('Cypress QA Engineer');
    cy.get('input[placeholder="e.g., San Francisco, CA or Remote"]').type('Remote');
    cy.get('input[placeholder="https://..."]').type('https://www.cypress.io');
    cy.get('textarea[placeholder="Full job description..."]').type('This is a test job description.');

    cy.get('button').contains('Add Job').click(); // Click the submit button in the modal

    cy.contains('Cypress QA Engineer').should('be.visible');
    cy.contains('Cypress Test Company').should('be.visible');
  });

  it('should allow editing an existing job', () => {
    // Assuming a job already exists from previous test or seed data
    cy.contains('Cypress QA Engineer').closest('[data-testid="job-card"]').within(() => {
      cy.get('button[title="Edit Job"]').click();
    });

    cy.get('h2').contains('Edit Job').should('be.visible');
    cy.get('input[placeholder="Enter job title"]').clear().type('Updated Cypress QA Engineer');
    cy.get('button').contains('Update Job').click();

    cy.contains('Updated Cypress QA Engineer').should('be.visible');
    cy.contains('Cypress QA Engineer').should('not.exist');
  });

  it('should allow deleting a job', () => {
    cy.contains('Updated Cypress QA Engineer').closest('[data-testid="job-card"]').within(() => {
      cy.get('button[title="Delete Job"]').click();
    });

    cy.on('window:confirm', () => true); // Confirm the deletion alert

    cy.contains('Updated Cypress QA Engineer').should('not.exist');
  });
});
