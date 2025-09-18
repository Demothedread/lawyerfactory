// Debug script to capture console errors and check React initialization
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ 
    headless: false,
    devtools: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Capture console messages
  page.on('console', msg => {
    console.log(`CONSOLE ${msg.type()}: ${msg.text()}`);
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    console.log(`PAGE ERROR: ${error.message}`);
  });
  
  // Capture failed requests
  page.on('requestfailed', request => {
    console.log(`FAILED REQUEST: ${request.url()} - ${request.failure().errorText}`);
  });
  
  try {
    console.log('Navigating to page...');
    await page.goto('http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html', {
      waitUntil: 'networkidle0',
      timeout: 10000
    });
    
    console.log('Page loaded. Checking for React...');
    
    // Check if React is available
    const reactExists = await page.evaluate(() => {
      return typeof window.React !== 'undefined';
    });
    console.log('React available:', reactExists);
    
    // Check if ReactDOM is available
    const reactDOMExists = await page.evaluate(() => {
      return typeof window.ReactDOM !== 'undefined';
    });
    console.log('ReactDOM available:', reactDOMExists);
    
    // Check if our root element exists
    const rootExists = await page.evaluate(() => {
      return document.getElementById('root') !== null;
    });
    console.log('Root element exists:', rootExists);
    
    // Check if any React components are rendered
    const hasReactComponents = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    });
    console.log('React components rendered:', hasReactComponents);
    
    // Get the actual HTML content of the root
    const rootHTML = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root ? root.innerHTML : 'No root element';
    });
    console.log('Root HTML:', rootHTML.substring(0, 200) + '...');
    
    // Check for script errors
    const scriptErrors = await page.evaluate(() => {
      return window.errorLog || [];
    });
    console.log('Script errors:', scriptErrors);
    
    console.log('\nWaiting for manual inspection. Press Ctrl+C to close.');
    await new Promise(() => {}); // Keep browser open
    
  } catch (error) {
    console.error('Error during page load:', error);
  } finally {
    await browser.close();
  }
})();