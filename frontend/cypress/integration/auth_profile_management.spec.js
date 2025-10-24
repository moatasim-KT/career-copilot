describe('Authentication and Profile Management Workflow', () => {
  const testUsername = `testuser_${Date.now()}`;
  const testEmail = `test_${Date.now()}@example.com`;
  const testPassword = 'testpassword';

  it('should allow a user to register, login, and manage their profile', () => {
    // 1. Registration
    cy.visit('http://localhost:3000/register');
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="email"]').type(testEmail);
    cy.get('input[name="password"]').type(testPassword);
    cy.get('input[name="confirmPassword"]').type(testPassword);
    cy.get('button').contains('Create Account').click();
    cy.url().should('include', '/login');

    // 2. Login
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="password"]').type(testPassword);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');

    // 3. Profile Management
    cy.visit('http://localhost:3000/profile');
    cy.get('h1').contains('Profile').should('be.visible');

    cy.get('input[name="full_name"]').clear().type('Cypress Full Name');
    cy.get('input[name="experience_level"]').clear().type('Senior');
    cy.get('input[name="location"]').clear().type('San Francisco, CA');
    cy.get('input[name="skills"]').clear().type('Cypress, JavaScript, Testing');
    cy.get('button').contains('Save Profile').click();
    cy.contains('Profile updated successfully!').should('be.visible');

    // Verify updated profile data (re-fetch or re-visit page)
    cy.reload();
    cy.get('input[name="full_name"]').should('have.value', 'Cypress Full Name');
    cy.get('input[name="experience_level"]').should('have.value', 'Senior');
    cy.get('input[name="location"]').should('have.value', 'San Francisco, CA');
    cy.get('input[name="skills"]').should('have.value', 'Cypress, JavaScript, Testing');

    // 4. Logout (assuming a logout button exists somewhere, e.g., in a header/navbar)
    // This part might need adjustment based on actual UI structure
    // cy.get('button').contains('Logout').click(); 
    // cy.url().should('include', '/login');
  });
});
