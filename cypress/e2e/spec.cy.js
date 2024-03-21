const { cyan } = require("colorette")

function fill_construct() {
  cy.get('#choices thead').contains('a', 'head').click()
    cy.get('#inpName').type('Roof')
    cy.get('#choices').contains('a', 'FREEZE').click()

    cy.contains('tr', 'Roof').find('a').contains('head').click()
    cy.get('#inpName').type('Walls')

    cy.get('tr').find('textarea').parents('tr').find('a').contains('head').click()
    cy.get('#inpName').type('Floor')

    cy.contains('tr', 'Roof').find('a').contains('task').click()
    cy.get('#inpName').type('Left side')
    cy.get('#inpPrice').clear().type('200')
    cy.get('#inpQty').clear().type('6')
    cy.get('#inpUnits').clear().type('sqm')
    cy.get('#inpDayStart').clear().type('2024-01-19')
    cy.get('#inpPlanDays').clear().type('3')

    cy.get('tr').find('textarea').parents('tr').find('a').contains('task').click()
    cy.get('#inpName').type('Right side')
    cy.get('#inpPrice').clear().type('200')
    cy.get('#inpQty').clear().type('6')
    cy.get('#inpUnits').clear().type('m2')
    cy.get('#inpDayStart').clear().type('2024-01-22')
    cy.get('#inpPlanDays').clear().type('2')

    cy.contains('tr', 'Floor').find('a').contains('task').click()
    cy.get('#inpName').type('Linoleum')
    cy.get('#inpPrice').clear().type('100')
    cy.get('#inpQty').clear().type('20')
    cy.get('#inpUnits').clear().type('sqm')
    cy.get('#inpDayStart').clear().type('2024-01-24')
    cy.get('#inpPlanDays').clear().type('3')

    cy.contains('tr', 'Walls').find('a').contains('task').click()
    cy.get('#inpName').type('First wall')
    cy.get('#inpPrice').clear().type('50')
    cy.get('#inpQty').clear().type('30')
    cy.get('#inpUnits').clear().type('sqm')
    cy.get('#inpDayStart').clear().type('2024-01-27')
    cy.get('#inpPlanDays').clear().type('1')
    cy.get('#choices').contains('a', 'FREEZE').click()
    
    cy.contains('tr', 'First wall').find('a').contains('task').click()
    cy.get('#inpName').type('Second wall')
    cy.get('#inpPrice').clear().type('50')
    cy.get('#inpQty').clear().type('45')
    cy.get('#inpUnits').clear().type('sqm')
    cy.get('#inpDayStart').clear().type('2024-01-28')
    cy.get('#inpPlanDays').clear().type('2')
    cy.get('#choices').contains('a', 'FREEZE').click()
    
    // cy.debug()
    //cy.get('tr').find('textarea').parents('tr').find('a').contains('task').click()
    cy.contains('tr', 'Second wall').find('a').contains('task').click()
    cy.get('#inpName').type('Third wall')
    cy.get('#inpPrice').clear().type('50')
    cy.get('#inpQty').clear().type('33')
    cy.get('#inpUnits').clear().type('m2')
    cy.get('#inpDayStart').clear().type('2024-01-30')
    cy.get('#inpPlanDays').clear().type('1')
    cy.get('#choices').contains('a', 'FREEZE').click()
}

describe('Tests after login', () => {
  beforeEach(() => {
    // cy.visit('/list')
    // cy.get('#id_username').type('yury')
    // cy.get('#id_password').type('Tp-iMfsS2004')
    // cy.get('button[type="submit"]').click()
    cy.login('yury', 'Tp-iMfsS2004')
  })

  it("Creates a new User Group", () => {
    cy.visit("/list/account")
    // cy.contains('List of projects.').click()
    cy.contains('Admin page.').should('exist').click()
    cy.visit("/admin/auth/group/add/")
    cy.get('#id_name').type('Client')
    cy.get('input[type="submit"].default[value="Save"]').should('exist').click()
  })

  it("Creates a new Client", () => {
    cy.visit("/list/account")
    // cy.contains('List of projects.').click()
    cy.contains('Admin page.').should('exist').click()
    cy.visit("/admin/list/user/add/")
    cy.get('#id_username').type('cypress')
    cy.get('#id_email').type('cypress@cypress.com')
    cy.get('#id_password1').type('s3cr3tAbC')
    cy.get('#id_password2').type('s3cr3tAbC')
    cy.get('#id_first_name').type('Cypress')
    cy.get('#id_last_name').type('Ivanovich')
    cy.get('#id_groups_0').check()
    cy.get('#id_groups_0').check().should('be.checked')
    cy.get('input[type="submit"].default[value="Save"]').click()
    cy.get('input[type="submit"].default[value="Save"]').should('exist').click()
  })

  it("Create Categories", () => {
    cy.visit("admin/list/category/add/")
    cy.get('#id_name').type('Active')
    cy.get('#id_priority').clear().type('0')
    cy.get('#id_color').clear().type('pink')
    cy.get('input[type="submit"].default[value="Save"]').should('exist').click()

    cy.visit("admin/list/category/add/")
    cy.get('#id_name').type('Done')
    cy.get('#id_priority').clear().type('1')
    cy.get('#id_color').clear().type('grey')
    cy.get('input[type="submit"].default[value="Save"]').should('exist').click()

    cy.visit("admin/list/category/add/")
    cy.get('#id_name').type('No-Cat')
    cy.get('#id_priority').clear().type('2')
    cy.get('#id_color').clear().type('yellow')
    cy.get('input[type="submit"].default[value="Save"]').should('exist').click()
  })

  it("Creates a new Construct", () => {
    cy.visit("/list/account")
    cy.contains('Admin page.').should('exist').click()
    cy.get('a[href="/admin/list/construct/add/"]').click()
    cy.get('#id_title_text').type('Cypress Test Project')
    cy.get('#id_address_text').type('10 Cypress Way')
    cy.get('#id_owner_name_text').type('Cypress')
    cy.get('#id_client_user').select('cypress')
    cy.get('input[type="submit"].default[value="Save"]').click()
  })

  it("Creates 'on-top profit' Construct", () => {
    cy.visit("/list/account")
    cy.contains('Admin page.').should('exist').click()
    cy.get('a[href="/admin/list/construct/add/"]').click()
    cy.get('#id_title_text').type('Cypress On-Top Test Project')
    cy.get('#id_address_text').type('10 Cypress Way')
    cy.get('#id_owner_name_text').type('Cypress')
    cy.get('#id_ontop_profit_percent_num').type('20')
    cy.get('#id_client_user').select('cypress')
    cy.get('input[type="submit"].default[value="Save"]').click()
  })

  it("Fills in the new Construct", () => {
    cy.visit("/list/1")
    
    fill_construct()

    cy.get('#project_total').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 9,800')
    })

    cy.get('#project_total_profit_vat').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 11,834')
    })

    cy.get('input[type="submit"]').click()

    cy.visit("/list/1") // reload the page to update numbers

    cy.get('#project_total').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 9,800')
    })

    cy.get('#project_total_profit_vat').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 11,834')
    })

    cy.get('#id_expected_deposit').invoke('text').should('contain', '£ 1,775.03')
  })

  
  it("Fills in the 'on-top profit' Construct", () => {
    cy.visit("/list/2")
    
    fill_construct()

    cy.get('#project_total').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 9,800')
    })

    cy.get('#project_total_profit_vat').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 11,834')
    })

    cy.get('input[type="submit"]').click()

    cy.visit("/list/2") // reload the page to update numbers

    cy.get('#project_total').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 9,800')
    })

    cy.get('#project_total_profit_vat').invoke('text').then((text) => {
      expect(text.trim()).to.equal('£ 11,834')
    })

    cy.get('#id_expected_deposit').invoke('text').should('contain', '£ 2,130.03')
  })

  it("Open the project list", () => {
    // cy.contains('back to the project list').should('exist').click()
    cy.visit("/list")
  })

  // it("Open Gantt Chart", () => {
  //   cy.visit("/gantt/1")
  // })

  it("Check the Client View page", () => {
    cy.visit("/list/1")
    cy.wait(2000);
    cy.contains('a', 'Client view').click();
    cy.contains('td', 'Total:').next().should('contain', '£ 11,270')
    cy.contains('td', 'Total + VAT:').next().should('contain', '£ 11,833.50')
    cy.contains('td', 'Deposit:').next().should('contain', '£ 1,775.03')
  })

  it("Check the Maintenance page", () => {
    cy.visit("/list/1")
    cy.wait(2000);
    cy.contains('a', 'Maintenance view').click();
    cy.contains('td', 'Total:').next().should('contain', '£ 11,833.50')
  })

  it("Check the On-Top Client View page", () => {
    cy.visit("/list/2")
    cy.wait(2000);
    cy.contains('a', 'Client view').click();
    cy.contains('td', 'Total:').next().should('contain', '£ 13,524.00')
    cy.contains('td', 'Total + VAT:').next().should('contain', '£ 14,200.20')
    cy.contains('td', 'Deposit:').next().should('contain', '£ 2,130.03')
  })

  it("Check the On-Top Maintenance page", () => {
    cy.visit("/list/2")
    cy.wait(2000);
    cy.contains('a', 'Maintenance view').click();
    cy.contains('td', 'Total:').next().should('contain', '£ 14,200.20')
  })

})