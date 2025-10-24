describe('Job Recommendations and Skill Gap Analysis Workflow', () => {
  const testUsername = `testuser_${Date.now()}`;
  const testEmail = `test_${Date.now()}@example.com`;
  const testPassword = 'testpassword';

  before(() => {
    // Register a new user for these tests
    cy.visit('http://localhost:3000/register');
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="email"]').type(testEmail);
    cy.get('input[name="password"]').type(testPassword);
    cy.get('input[name="confirmPassword"]').type(testPassword);
    cy.get('button').contains('Create Account').click();
    cy.url().should('include', '/login');

    // Login with the new user
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="password"]').type(testPassword);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');

    // Add a job to ensure recommendations can be generated
    cy.visit('http://localhost:3000/jobs');
    cy.get('button').contains('Add Job').click();
    cy.get('input[placeholder="Enter company name"]').type('Cypress Rec Company');
    cy.get('input[placeholder="Enter job title"]').type('Cypress Rec Job');
    cy.get('input[placeholder="e.g., San Francisco, CA or Remote"]').type('Remote');
    cy.get('textarea[placeholder="Full job description..."]').type('This is a test job for recommendations.');
    cy.get('button').contains('Add Job').click();
    cy.contains('Cypress Rec Job').should('be.visible');
  });

  beforeEach(() => {
    // Login before each test to ensure authenticated state
    cy.visit('http://localhost:3000/login');
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="password"]').type(testPassword);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
    cy.visit('http://localhost:3000/recommendations');
  });

  it('should display job recommendations', () => {
    cy.contains('Job Recommendations').click();
    cy.contains('Cypress Rec Job').should('be.visible');
    cy.contains('Cypress Rec Company').should('be.visible');
    cy.contains('Match Score').should('be.visible');
  });

  it('should display skill gap analysis', () => {
    cy.contains('Skill Gap Analysis').click();
    cy.contains('Skill Coverage Overview').should('be.visible');
    cy.contains('Your Current Skills').should('be.visible');
    cy.contains('Skills to Learn').should('be.visible');
    cy.contains('Top Market Skills').should('be.visible');
  });

  it('should allow applying to a recommended job', () => {
    cy.contains('Job Recommendations').click();
    cy.contains('Cypress Rec Job').closest('.Card').within(() => {
      cy.get('button').contains('Apply').click();
    });
    cy.contains('Application created successfully!').should('be.visible');
    // After applying, the job should ideally disappear from recommendations
    cy.contains('Cypress Rec Job').should('not.exist');
  });
});
