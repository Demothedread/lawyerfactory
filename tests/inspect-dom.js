#!/usr/bin/env node
// DOM inspection script to understand actual page structure

const puppeteer = require('puppeteer');

async function inspectDOM() {
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: '/Users/jreback/chrome/mac_arm-136.0.7103.94/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  try {
    console.log('🔍 Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0', timeout: 30000 });
    
    console.log('\n📊 Page Structure Analysis:\n');
    
    // Get all classes used on the page
    const allClasses = await page.evaluate(() => {
      const classes = new Set();
      document.querySelectorAll('*').forEach(el => {
        el.classList.forEach(cls => classes.add(cls));
      });
      return Array.from(classes).sort();
    });
    
    console.log('All CSS classes found:', allClasses.filter(c => c.includes('grid') || c.includes('Grid')));
    
    // Check for GridContainer
    const gridInfo = await page.evaluate(() => {
      const containers = document.querySelectorAll('.grid-container');
      const items = document.querySelectorAll('.grid-item');
      const sections = document.querySelectorAll('.grid-section');
      
      const mainPanel = document.querySelector('.main-panel-content');
      const sampleHTML = mainPanel ? mainPanel.innerHTML.substring(0, 1000) : '';
      
      return {
        containers: containers.length,
        items: items.length,
        sections: sections.length,
        mainPanelHTML: sampleHTML,
        containerClasses: Array.from(containers).map(c => c.className),
        itemClasses: Array.from(items).slice(0, 3).map(i => i.className)
      };
    });
    
    console.log('\n📦 Grid Components:');
    console.log('  Containers:', gridInfo.containers);
    console.log('  Items:', gridInfo.items);
    console.log('  Sections:', gridInfo.sections);
    
    if (gridInfo.containerClasses.length > 0) {
      console.log('\n  Container classes:', gridInfo.containerClasses);
    }
    
    if (gridInfo.itemClasses.length > 0) {
      console.log('  Item classes (first 3):', gridInfo.itemClasses);
    }
    
    console.log('\n📄 Main Panel Content (first 1000 chars):');
    console.log(gridInfo.mainPanelHTML);
    
    // Check current view
    const viewInfo = await page.evaluate(() => {
      const tabs = document.querySelectorAll('.navigation-tabs button');
      const activeTab = Array.from(tabs).find(t => 
        t.style.backgroundColor && t.style.backgroundColor.includes('green')
      );
      return {
        currentView: activeTab ? activeTab.textContent.trim() : 'unknown',
        allTabs: Array.from(tabs).map(t => t.textContent.trim())
      };
    });
    
    console.log('\n🎯 Current View:', viewInfo.currentView);
    console.log('Available tabs:', viewInfo.allTabs);
    
    // Navigate to different views to find grid containers
    console.log('\n🔄 Checking different views for grid containers...');
    
    for (const view of ['evidence', 'pipeline', 'orchestration']) {
      console.log(`\n  Switching to ${view} view...`);
      
      await page.evaluate((viewName) => {
        const button = Array.from(document.querySelectorAll('.navigation-tabs button'))
          .find(b => b.textContent.toLowerCase().includes(viewName));
        if (button) button.click();
      }, view);
      
      await page.waitForTimeout(500);
      
      const viewGrids = await page.evaluate(() => {
        return {
          containers: document.querySelectorAll('.grid-container').length,
          items: document.querySelectorAll('.grid-item').length,
          sections: document.querySelectorAll('.grid-section').length
        };
      });
      
      console.log(`    ${view}: containers=${viewGrids.containers}, items=${viewGrids.items}, sections=${viewGrids.sections}`);
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
  }
}

inspectDOM();