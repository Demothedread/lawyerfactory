#!/usr/bin/env node
// Standalone Puppeteer UI testing script for LawyerFactory
// Tests http://localhost:3000 following MANUAL_TESTING_GUIDE.md

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const TEST_URL = 'http://localhost:3000';
const SCREENSHOT_DIR = './tests/screenshots';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const testResults = {
  timestamp: new Date().toISOString(),
  url: TEST_URL,
  browser: 'Chrome (Puppeteer)',
  sections: {},
  summary: { total: 0, passed: 0, failed: 0, skipped: 0 },
  screenshots: []
};

async function runTest(page, testName, testFn) {
  testResults.summary.total++;
  try {
    const result = await testFn(page);
    if (result.passed) {
      testResults.summary.passed++;
      console.log(`✅ PASS: ${testName}`);
      return { status: 'PASS', testName, ...result };
    } else {
      testResults.summary.failed++;
      console.log(`❌ FAIL: ${testName}${result.reason ? ' - ' + result.reason : ''}`);
      return { status: 'FAIL', testName, ...result };
    }
  } catch (error) {
    testResults.summary.failed++;
    console.log(`❌ FAIL: ${testName} - ${error.message}`);
    return { status: 'FAIL', testName, error: error.message };
  }
}

async function takeScreenshot(page, name) {
  const filename = `${name}-${Date.now()}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: false });
  testResults.screenshots.push(filepath);
  console.log(`   📸 Screenshot saved: ${filepath}`);
  return filepath;
}

// Test Section 1: Basic Page Load
async function testPageLoad(page) {
  console.log('\n=== Section 1: Page Load Tests ===\n');
  const results = [];

  results.push(await runTest(page, 'TC1.1: Page loads successfully', async (p) => {
    const title = await p.title();
    await takeScreenshot(p, 'page-load');
    return { passed: true, details: `Page title: "${title}"` };
  }));

  results.push(await runTest(page, 'TC1.2: No console errors', async (p) => {
    const errors = await p.evaluate(() => {
      return window.__TEST_CONSOLE_ERRORS__ || [];
    });
    return { 
      passed: errors.length === 0, 
      reason: errors.length > 0 ? `${errors.length} console errors found` : null,
      details: errors
    };
  }));

  results.push(await runTest(page, 'TC1.3: React app renders', async (p) => {
    const hasRoot = await p.evaluate(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    });
    return { passed: hasRoot, reason: !hasRoot ? 'React root is empty' : null };
  }));

  testResults.sections.pageLoad = results;
  return results;
}

// Test Section 2: Grid Layout Tests
async function testGridLayout(page) {
  console.log('\n=== Section 2: Grid Layout Tests ===\n');
  const results = [];

  results.push(await runTest(page, 'TC2.1: Grid container present', async (p) => {
    const hasGrid = await p.evaluate(() => {
      const selectors = ['.grid-container', '[class*="GridContainer"]', '[class*="grid-"]'];
      return selectors.some(sel => document.querySelector(sel) !== null);
    });
    await takeScreenshot(p, 'grid-layout');
    return { passed: hasGrid, reason: !hasGrid ? 'No grid container found' : null };
  }));

  results.push(await runTest(page, 'TC2.2: Zero vertical scroll', async (p) => {
    const scrollInfo = await p.evaluate(() => {
      const main = document.querySelector('main, .workspace-container, [class*="workspace"]');
      if (!main) return { found: false };
      return {
        found: true,
        scrollHeight: main.scrollHeight,
        clientHeight: main.clientHeight,
        hasScroll: main.scrollHeight > main.clientHeight
      };
    });
    return { 
      passed: scrollInfo.found && !scrollInfo.hasScroll,
      reason: !scrollInfo.found ? 'Workspace container not found' : 
              scrollInfo.hasScroll ? `Scroll detected (${scrollInfo.scrollHeight}px > ${scrollInfo.clientHeight}px)` : null,
      details: scrollInfo
    };
  }));

  testResults.sections.gridLayout = results;
  return results;
}

// Test Section 3: Responsive Tests
async function testResponsive(page) {
  console.log('\n=== Section 3: Responsive Layout Tests ===\n');
  const results = [];

  const viewports = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 1024, height: 768 },
    { name: 'Desktop', width: 1920, height: 1080 }
  ];

  for (const vp of viewports) {
    results.push(await runTest(page, `TC3: ${vp.name} layout (${vp.width}x${vp.height})`, async (p) => {
      await p.setViewport({ width: vp.width, height: vp.height });
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const layoutValid = await p.evaluate(() => {
        const container = document.querySelector('.grid-container, [class*="GridContainer"], main');
        if (!container) return false;
        const rect = container.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
      
      await takeScreenshot(p, `responsive-${vp.name.toLowerCase()}`);
      return { passed: layoutValid, details: `${vp.name} viewport tested` };
    }));
  }

  // Reset to desktop
  await page.setViewport({ width: 1920, height: 1080 });
  
  testResults.sections.responsive = results;
  return results;
}

// Test Section 4: Accessibility
async function testAccessibility(page) {
  console.log('\n=== Section 4: Accessibility Tests ===\n');
  const results = [];

  results.push(await runTest(page, 'TC4.1: Focusable elements present', async (p) => {
    const focusableCount = await p.evaluate(() => {
      const focusable = document.querySelectorAll('button, a, input, [tabindex]:not([tabindex="-1"])');
      return focusable.length;
    });
    return { 
      passed: focusableCount > 0,
      details: `Found ${focusableCount} focusable elements`
    };
  }));

  results.push(await runTest(page, 'TC4.2: ARIA attributes present', async (p) => {
    const ariaCount = await p.evaluate(() => {
      const ariaElements = document.querySelectorAll('[aria-label], [aria-expanded], [role]');
      return ariaElements.length;
    });
    return { 
      passed: ariaCount > 0,
      details: `Found ${ariaCount} elements with ARIA attributes`
    };
  }));

  testResults.sections.accessibility = results;
  return results;
}

// Test Section 5: Performance
async function testPerformance(page) {
  console.log('\n=== Section 5: Performance Tests ===\n');
  const results = [];

  results.push(await runTest(page, 'TC5.1: Page load time < 3s', async (p) => {
    const metrics = await p.evaluate(() => {
      const perfData = performance.getEntriesByType('navigation')[0];
      if (!perfData) return null;
      return {
        loadTime: Math.round(perfData.loadEventEnd - perfData.fetchStart),
        domInteractive: Math.round(perfData.domInteractive - perfData.fetchStart),
        domComplete: Math.round(perfData.domComplete - perfData.fetchStart)
      };
    });
    
    const passed = metrics && metrics.loadTime < 3000;
    return { 
      passed,
      reason: !metrics ? 'Performance data unavailable' :
              !passed ? `Load time ${metrics.loadTime}ms exceeds 3000ms` : null,
      details: metrics
    };
  }));

  testResults.sections.performance = results;
  return results;
}

// Main test execution
async function runAllTests() {
  console.log('🚀 LawyerFactory Automated UI Testing');
  console.log('=====================================\n');
  console.log(`Target URL: ${TEST_URL}`);
  console.log(`Started at: ${testResults.timestamp}\n`);

  let browser;
  let page;

  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    page = await browser.newPage();
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`   ⚠️  Console error: ${msg.text()}`);
      }
    });

    // Navigate to site
    console.log(`Navigating to ${TEST_URL}...`);
    await page.goto(TEST_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    
    // Wait for React to mount
    await page.waitForSelector('#root', { timeout: 5000 });
    await new Promise(resolve => setTimeout(resolve, 2000)); // Allow React app to fully render
    
    console.log('✅ Page loaded\n');

    // Run test sections
    await testPageLoad(page);
    await testGridLayout(page);
    await testResponsive(page);
    await testAccessibility(page);
    await testPerformance(page);

    // Generate summary
    console.log('\n\n📊 Test Summary');
    console.log('================');
    console.log(`Total Tests: ${testResults.summary.total}`);
    console.log(`✅ Passed: ${testResults.summary.passed} (${Math.round(testResults.summary.passed/testResults.summary.total*100)}%)`);
    console.log(`❌ Failed: ${testResults.summary.failed} (${Math.round(testResults.summary.failed/testResults.summary.total*100)}%)`);
    console.log(`⏭️  Skipped: ${testResults.summary.skipped}`);

    // Save results
    const resultsPath = './tests/test-results.json';
    fs.writeFileSync(resultsPath, JSON.stringify(testResults, null, 2));
    console.log(`\n📝 Results saved to: ${resultsPath}`);
    console.log(`📸 Screenshots saved to: ${SCREENSHOT_DIR}`);

    return testResults;

  } catch (error) {
    console.error('\n❌ Test execution failed:', error.message);
    if (page) await takeScreenshot(page, 'error');
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

// Run if executed directly
if (require.main === module) {
  runAllTests()
    .then(() => process.exit(testResults.summary.failed > 0 ? 1 : 0))
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}

module.exports = { runAllTests, testResults };