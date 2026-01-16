// Automated UI Testing Script for LawyerFactory Grid Framework Integration
// Tests site at http://localhost:3000 following MANUAL_TESTING_GUIDE.md
// Uses Puppeteer MCP server for browser automation

const testResults = {
  timestamp: new Date().toISOString(),
  url: 'http://localhost:3000',
  browser: 'Chrome',
  sections: {},
  summary: {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0
  }
};

// Test execution wrapper
async function runTest(testName, testFn) {
  testResults.summary.total++;
  try {
    const result = await testFn();
    if (result) {
      testResults.summary.passed++;
      console.log(`✅ PASS: ${testName}`);
      return { status: 'PASS', testName, details: result };
    } else {
      testResults.summary.failed++;
      console.log(`❌ FAIL: ${testName}`);
      return { status: 'FAIL', testName, details: 'Test returned false' };
    }
  } catch (error) {
    testResults.summary.failed++;
    console.log(`❌ FAIL: ${testName} - ${error.message}`);
    return { status: 'FAIL', testName, error: error.message };
  }
}

// Section 1: Evidence Workspace Tests
async function testEvidenceWorkspace() {
  console.log('\n=== Testing Evidence Workspace ===\n');
  const sectionResults = [];

  // TC1.1: 2-Column Grid Rendering
  sectionResults.push(await runTest('TC1.1: 2-Column Grid Rendering', async () => {
    const hasGridContainer = await page.evaluate(() => {
      const container = document.querySelector('.grid-container, [class*="GridContainer"]');
      if (!container) return false;
      const styles = window.getComputedStyle(container);
      return styles.display === 'grid' || styles.gridTemplateColumns;
    });
    return hasGridContainer;
  }));

  // TC1.2: No Vertical Scrollbar
  sectionResults.push(await runTest('TC1.2: No Vertical Scrollbar', async () => {
    const hasNoScroll = await page.evaluate(() => {
      const workspace = document.querySelector('.workspace-container, main, [class*="workspace"]');
      if (!workspace) return false;
      return workspace.scrollHeight <= workspace.clientHeight;
    });
    return hasNoScroll;
  }));

  // TC1.3: Collapsible Section Behavior
  sectionResults.push(await runTest('TC1.3: Collapsible Section Test', async () => {
    const hasCollapsible = await page.evaluate(() => {
      const headers = document.querySelectorAll('[class*="grid-section-header"], .collapsible-header');
      return headers.length > 0;
    });
    return hasCollapsible;
  }));

  testResults.sections.evidenceWorkspace = sectionResults;
  return sectionResults;
}

// Section 2: Responsive Breakpoints Tests
async function testResponsiveBreakpoints() {
  console.log('\n=== Testing Responsive Breakpoints ===\n');
  const sectionResults = [];

  const viewports = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 1024, height: 768 },
    { name: 'Desktop', width: 1920, height: 1080 }
  ];

  for (const viewport of viewports) {
    sectionResults.push(await runTest(`TC4: ${viewport.name} Layout (${viewport.width}x${viewport.height})`, async () => {
      await page.setViewport({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(500); // Allow reflow

      const layoutValid = await page.evaluate(() => {
        const container = document.querySelector('.grid-container, [class*="GridContainer"]');
        if (!container) return false;
        const rect = container.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
      return layoutValid;
    }));
  }

  testResults.sections.responsiveBreakpoints = sectionResults;
  return sectionResults;
}

// Section 3: Accessibility Tests
async function testAccessibility() {
  console.log('\n=== Testing Accessibility ===\n');
  const sectionResults = [];

  // TC9.1: Keyboard Navigation
  sectionResults.push(await runTest('TC9.1: Interactive Elements Focusable', async () => {
    const hasFocusableElements = await page.evaluate(() => {
      const focusable = document.querySelectorAll('button, a, input, [tabindex]:not([tabindex="-1"])');
      return focusable.length > 0;
    });
    return hasFocusableElements;
  }));

  // TC9.4: ARIA Attributes
  sectionResults.push(await runTest('TC9.4: ARIA Attributes Present', async () => {
    const hasAria = await page.evaluate(() => {
      const ariaElements = document.querySelectorAll('[aria-label], [aria-expanded], [role]');
      return ariaElements.length > 0;
    });
    return hasAria;
  }));

  testResults.sections.accessibility = sectionResults;
  return sectionResults;
}

// Section 4: Performance Tests
async function testPerformance() {
  console.log('\n=== Testing Performance ===\n');
  const sectionResults = [];

  // TC8.3: Page Load Time
  sectionResults.push(await runTest('TC8.3: Page Load Time < 3s', async () => {
    const metrics = await page.evaluate(() => {
      const perfData = performance.getEntriesByType('navigation')[0];
      if (!perfData) return null;
      return {
        loadTime: perfData.loadEventEnd - perfData.fetchStart,
        domInteractive: perfData.domInteractive - perfData.fetchStart
      };
    });
    
    if (!metrics) return false;
    console.log(`   Load time: ${metrics.loadTime}ms, DOM Interactive: ${metrics.domInteractive}ms`);
    return metrics.loadTime < 3000;
  }));

  testResults.sections.performance = sectionResults;
  return sectionResults;
}

// Main test execution
async function runAllTests() {
  console.log('🚀 LawyerFactory Automated UI Testing');
  console.log('=====================================\n');
  console.log(`Target URL: ${testResults.url}`);
  console.log(`Started at: ${testResults.timestamp}\n`);

  try {
    // Test 1: Evidence Workspace
    await testEvidenceWorkspace();

    // Test 2: Responsive Breakpoints
    await testResponsiveBreakpoints();

    // Test 3: Accessibility
    await testAccessibility();

    // Test 4: Performance
    await testPerformance();

    // Generate summary
    console.log('\n\n📊 Test Summary');
    console.log('================');
    console.log(`Total Tests: ${testResults.summary.total}`);
    console.log(`✅ Passed: ${testResults.summary.passed} (${Math.round(testResults.summary.passed/testResults.summary.total*100)}%)`);
    console.log(`❌ Failed: ${testResults.summary.failed} (${Math.round(testResults.summary.failed/testResults.summary.total*100)}%)`);
    console.log(`⏭️  Skipped: ${testResults.summary.skipped}`);

    // Save results to file
    const fs = require('fs');
    const resultsPath = './tests/test-results.json';
    fs.writeFileSync(resultsPath, JSON.stringify(testResults, null, 2));
    console.log(`\n📝 Results saved to: ${resultsPath}`);

    return testResults;
  } catch (error) {
    console.error('❌ Test execution failed:', error);
    throw error;
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runAllTests, testResults };
}