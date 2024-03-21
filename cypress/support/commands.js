// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
Cypress.Commands.add('login', (username, password) => {
    cy.session(
        username,
        () => {
            cy.visit('/accounts/login')
            cy.get('#id_username').type(username)
            cy.get('#id_password').type(password)
            cy.get('button[type="submit"]').click()
        },
        {
            // validate: () => {
            //     //cy.getCookie('sessionid').should('exist')
            //     cy.visit("http://127.0.0.1:8000/list/account")
            // },
        }
      )
})
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })