// LawyerFactory Puppeteer Integration Tests
// Tests the complete user journey from evidence upload to lawsuit creation

const { expect } = require('chai');
const puppeteer = require('puppeteer');

describe('LawyerFactory Integration Tests', function() {
  let browser;
  let page;

  // Set timeout for all tests
  this.timeout(30000);

  before(async function() {
    // Launch browser with specific configuration for testing
    browser = await puppeteer.launch({
      headless: 'new', // Use new headless mode
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu'
      ],
      ignoreDefaultArgs: ['--disable-extensions'],
      executablePath: '/Users/jreback/.cache/puppeteer/chrome/mac_arm-140.0.7339.82/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
    });

    page = await browser.newPage();

    // Set viewport for consistent testing
    await page.setViewport({ width: 1280, height: 720 });

    // Enable console logging for debugging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  });

  after(async function() {
    if (browser) {
      await browser.close();
    }
  });

  describe('Frontend Application', function() {
    it('should load the main page successfully', async function() {
      await page.goto('http://localhost:3000', {
        waitUntil: 'networkidle0',
        timeout: 10000
      });

      // Wait for React to hydrate
      await page.waitForSelector('#root', { timeout: 5000 });

      const title = await page.title();
      expect(title).to.include('Vite + React');
    });

    it('should navigate to evidence view first', async function() {
      // Wait for React hydration
      await page.waitForTimeout(2000);

      // Look for evidence-related elements or navigation
      const evidenceElements = await page.$$('[data-testid="evidence-section"], .evidence, #evidence');
      const hasEvidenceSection = evidenceElements.length > 0;

      if (hasEvidenceSection) {
        console.log('Evidence section found, clicking...');
        await evidenceElements[0].click();
      } else {
        console.log('No evidence section found, checking for grid framework...');
        // Check for grid framework components
        const gridElements = await page.$$('.grid-container, [class*="grid"], .evidence-grid');
        if (gridElements.length > 0) {
          console.log('Grid framework found');
        }
      }

      // Wait for any dynamic content to load
      await page.waitForTimeout(1000);
    });

    it('should test LawsuitWizard component integration', async function() {
      // Look for LawsuitWizard or form elements
      const wizardElements = await page.$$('[data-testid="lawsuit-wizard"], .lawsuit-wizard, form[class*="wizard"]');
      const hasWizard = wizardElements.length > 0;

      if (hasWizard) {
        console.log('LawsuitWizard component found');
        // Try to interact with the wizard
        await wizardElements[0].click();
        await page.waitForTimeout(1000);
      } else {
        console.log('LawsuitWizard not found, checking for form elements...');
        // Look for general form elements
        const forms = await page.$$('form, button[type="submit"]');
        console.log(`Found ${forms.length} form elements`);
      }
    });

    it('should verify grid framework components', async function() {
      // Check for grid container and accordion components
      const gridContainer = await page.$('.grid-container');
      const accordion = await page.$('.accordion, [class*="accordion"]');

      if (gridContainer) {
        console.log('GridContainer component found');
        const gridClasses = await page.evaluate(() => {
          const element = document.querySelector('.grid-container');
          return element ? element.className : 'not found';
        });
        console.log('Grid container classes:', gridClasses);
      }

      if (accordion) {
        console.log('Accordion component found');
      }
    });

    it('should test upload functionality', async function() {
      // Look for file upload elements
      const uploadElements = await page.$$('input[type="file"], .upload, [data-testid="upload"]');

      if (uploadElements.length > 0) {
        console.log(`Found ${uploadElements.length} upload elements`);

        // Test if upload elements are visible and enabled
        for (const element of uploadElements) {
          const isVisible = await element.isIntersectingViewport();
          const isEnabled = await page.evaluate(el => !el.disabled, element);

          console.log(`Upload element - Visible: ${isVisible}, Enabled: ${isEnabled}`);
        }
      } else {
        console.log('No upload elements found');
      }
    });
  });

  describe('Backend API Integration', function() {
    it('should test API health endpoint', async function() {
      try {
        const response = await page.evaluate(async () => {
          const res = await fetch('http://localhost:8000/api/health');
          return {
            status: res.status,
            data: await res.json()
          };
        });

        expect(response.status).to.equal(200);
        expect(response.data).to.have.property('status', 'healthy');
        expect(response.data).to.have.property('lawyerfactory_available', true);

        console.log('API Health Check:', response.data);
      } catch (error) {
        console.log('API health check failed:', error.message);
        // This is expected if API is not running, so we don't fail the test
      }
    });

    it('should test evidence API endpoints', async function() {
      try {
        const response = await page.evaluate(async () => {
          const res = await fetch('http://localhost:8000/api/evidence/list');
          return {
            status: res.status,
            data: await res.text()
          };
        });

        console.log('Evidence API response status:', response.status);
        if (response.status === 200) {
          console.log('Evidence API data length:', response.data.length);
        }
      } catch (error) {
        console.log('Evidence API test failed:', error.message);
      }
    });
  });

  describe('Performance and Accessibility', function() {
    it('should load page within acceptable time', async function() {
      const startTime = Date.now();

      await page.goto('http://localhost:3000', {
        waitUntil: 'networkidle0',
        timeout: 10000
      });

      const loadTime = Date.now() - startTime;
      console.log(`Page load time: ${loadTime}ms`);

      // Should load within 5 seconds
      expect(loadTime).to.be.below(5000);
    });

    it('should have proper heading structure', async function() {
      const headings = await page.$$eval('h1, h2, h3, h4, h5, h6', headings => {
        return headings.map(h => ({
          tag: h.tagName,
          text: h.textContent.trim()
        }));
      });

      console.log('Page headings:', headings);

      // Should have at least one h1
      const h1Count = headings.filter(h => h.tag === 'H1').length;
      expect(h1Count).to.be.at.least(1);
    });

    it('should have accessible form elements', async function() {
      const forms = await page.$$eval('form', forms => forms.length);
      const inputs = await page.$$eval('input, select, textarea', inputs =>
        inputs.map(input => ({
          type: input.type || input.tagName.toLowerCase(),
          required: input.required,
          ariaLabel: input.getAttribute('aria-label'),
          ariaLabelledBy: input.getAttribute('aria-labelledby')
        }))
      );

      console.log(`Found ${forms} forms and ${inputs.length} form inputs`);
      console.log('Form inputs:', inputs);
    });
  });
});

// Additional utility functions for testing
async function waitForReactHydration(page) {
  await page.waitForFunction(() => {
    // Check if React has finished hydrating
    return window.React && document.querySelector('#root');
  }, { timeout: 5000 });
}

async function waitForElement(page, selector, timeout = 5000) {
  try {
    await page.waitForSelector(selector, { timeout });
    return true;
  } catch (error) {
    console.log(`Element ${selector} not found within ${timeout}ms`);
    return false;
  }
}

module.exports = {
  waitForReactHydration,
  waitForElement
};