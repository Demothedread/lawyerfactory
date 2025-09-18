// Debug script to check React mounting and any JavaScript errors
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ 
    headless: false,
    devtools: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Capture all console messages
  page.on('console', msg => {
    const type = msg.type().toUpperCase();
    const text = msg.text();
    console.log(`[${type}] ${text}`);
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR] ${error.message}`);
    console.log(error.stack);
  });
  
  // Capture failed requests
  page.on('requestfailed', request => {
    console.log(`[FAILED REQUEST] ${request.url()} - ${request.failure().errorText}`);
  });
  
  // Capture response errors
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`[HTTP ERROR] ${response.status()} - ${response.url()}`);
    }
  });
  
  try {
    console.log('Navigating to page...');
    await page.goto('http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html', {
      waitUntil: 'networkidle0',
      timeout: 15000
    });
    
    console.log('Page loaded. Checking React status...');
    
    // Wait a moment for React to potentially mount
    await page.waitForFunction(() => true, {}, { timeout: 2000 }).catch(() => {});
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Check if React and dependencies are loaded
    const reactStatus = await page.evaluate(() => {
      return {
        react: typeof window.React !== 'undefined',
        reactDOM: typeof window.ReactDOM !== 'undefined',
        babel: typeof window.Babel !== 'undefined',
        framerMotion: typeof window.FramerMotion !== 'undefined',
        agGrid: typeof window.agGrid !== 'undefined'
      };
    });
    console.log('Dependencies loaded:', reactStatus);
    
    // Check if root element exists and has content
    const rootStatus = await page.evaluate(() => {
      const root = document.getElementById('root');
      return {
        exists: root !== null,
        hasChildren: root && root.children.length > 0,
        innerHTML: root ? root.innerHTML.substring(0, 500) : null,
        className: root ? root.className : null
      };
    });
    console.log('Root element status:', rootStatus);
    
    // Check for script tags and their loading status
    const scriptStatus = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script'));
      return scripts.map(script => ({
        src: script.src || 'inline',
        loaded: script.readyState === 'complete' || !script.src,
        hasError: script.onerror !== null
      }));
    });
    console.log('Script loading status:', scriptStatus);
    
    // Try to manually execute the React mounting code
    const mountingResult = await page.evaluate(() => {
      try {
        // Check if LawyerFactoryApp is defined
        if (typeof LawyerFactoryApp === 'undefined') {
          return { success: false, error: 'LawyerFactoryApp is not defined' };
        }
        
        // Try to create element
        const element = React.createElement(LawyerFactoryApp);
        const root = document.getElementById('root');
        
        if (!root) {
          return { success: false, error: 'Root element not found' };
        }
        
        // Try to render
        ReactDOM.render(element, root);
        return { success: true, error: null };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    console.log('Manual mounting result:', mountingResult);
    
    // Check final state
    await new Promise(resolve => setTimeout(resolve, 1000));
    const finalStatus = await page.evaluate(() => {
      const root = document.getElementById('root');
      return {
        hasContent: root && root.children.length > 0,
        htmlPreview: root ? root.innerHTML.substring(0, 200) : null
      };
    });
    console.log('Final status:', finalStatus);
    
    console.log('\nWaiting for manual inspection. Press Ctrl+C to close.');
    await new Promise(() => {}); // Keep browser open
    
  } catch (error) {
    console.error('Error during debugging:', error);
  } finally {
    await browser.close();
  }
})();