// Simple test to check if the UI is working
const puppeteer = require('puppeteer');

(async () => {
  console.log('Starting browser...');
  const browser = await puppeteer.launch({ 
    headless: false,
    devtools: false
  });
  
  const page = await browser.newPage();
  
  // Capture console messages
  page.on('console', msg => {
    console.log(`[CONSOLE] ${msg.text()}`);
  });
  
  // Capture errors
  page.on('pageerror', error => {
    console.log(`[ERROR] ${error.message}`);
  });
  
  try {
    console.log('Navigating to page...');
    await page.goto('http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });
    
    console.log('Page loaded successfully!');
    
    // Wait a bit for React to mount
    await page.waitForFunction(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    }, { timeout: 10000 }).catch(() => {
      console.log('React components did not mount within 10 seconds');
    });
    
    // Check if UI components are present
    const uiStatus = await page.evaluate(() => {
      const root = document.getElementById('root');
      const controlStation = document.querySelector('.control-station');
      const panels = document.querySelectorAll('.metal-panel');
      
      return {
        rootExists: !!root,
        rootHasContent: root && root.children.length > 0,
        controlStationExists: !!controlStation,
        panelCount: panels.length,
        bodyContent: document.body.innerHTML.length
      };
    });
    
    console.log('UI Status:', uiStatus);
    
    if (uiStatus.controlStationExists && uiStatus.panelCount > 0) {
      console.log('✅ SUCCESS: Soviet Control Panel UI is working!');
    } else {
      console.log('❌ ISSUE: UI components not fully loaded');
    }
    
    console.log('Test complete. Browser will stay open for 10 seconds...');
    await new Promise(resolve => setTimeout(resolve, 10000));
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();