
describe('Login Flow', () => {
  it('should allow a user to login', () => {
    cy.visit('http://localhost:3000/login');

    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="password"]').type('password');
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
  });

  it('should load dashboard data after login', () => {
    cy.visit('http://localhost:3000/login');

    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="password"]').type('password');
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.contains('Total Jobs');
    cy.contains('Applications');
    cy.contains('Interviews');
    cy.contains('Offers');
  });
});
