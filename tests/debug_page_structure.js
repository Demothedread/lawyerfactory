// Debug script to inspect the actual page structure
const puppeteer = require('puppeteer');

const TEST_URL = 'http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html';

(async () => {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    try {
        await page.goto(TEST_URL, { waitUntil: 'networkidle2' });
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait for React to initialize
        
        console.log('🔍 Inspecting page structure...\n');
        
        // Check for main container structure
        const bodyClasses = await page.$eval('body', el => el.className);
        console.log('Body classes:', bodyClasses);
        
        const factoryContainer = await page.$('.factory-container');
        console.log('Factory container exists:', !!factoryContainer);
        
        // Check panel structure
        const panels = await page.$$eval('div[class*="panel"]', panels => 
            panels.map(p => ({ class: p.className, id: p.id || 'no-id' }))
        );
        console.log('Panels found:', panels);
        
        // Check for metal panels
        const metalPanels = await page.$$('.metal-panel');
        console.log('Metal panels count:', metalPanels.length);
        
        // Check for gauges
        const gauges = await page.$$('.analog-gauge');
        console.log('Analog gauges count:', gauges.length);
        
        // Check for toggle switches
        const toggles = await page.$$('.toggle-switch');
        console.log('Toggle switches count:', toggles.length);
        
        // Check for phase elements
        const phaseElements = await page.$$eval('[class*="phase"]', elements =>
            elements.map(el => ({ class: el.className, text: el.textContent.slice(0, 50) }))
        );
        console.log('Phase elements:', phaseElements);
        
        // Check for grid elements
        const gridElements = await page.$$eval('[class*="ag-"]', elements =>
            elements.map(el => el.className)
        );
        console.log('ag-Grid elements:', gridElements);
        
        // Check specific selectors from failed tests
        const leftPanelCheck = await page.$('.panel-left');
        const rightPanelCheck = await page.$('.panel-right');
        const centerPanelCheck = await page.$('.panel-center');
        
        console.log('\nPanel checks:');
        console.log('Left panel exists:', !!leftPanelCheck);
        console.log('Right panel exists:', !!rightPanelCheck);
        console.log('Center panel exists:', !!centerPanelCheck);
        
        // Get actual panel structure
        const actualStructure = await page.evaluate(() => {
            const root = document.getElementById('root');
            if (!root) return 'No root element found';
            
            function getStructure(element, depth = 0) {
                if (depth > 3) return '...'; // Limit depth
                
                const children = Array.from(element.children);
                return {
                    tag: element.tagName.toLowerCase(),
                    class: element.className,
                    id: element.id,
                    children: children.length > 0 ? children.map(child => getStructure(child, depth + 1)) : undefined
                };
            }
            
            return getStructure(root);
        });
        
        console.log('\nActual DOM structure:');
        console.log(JSON.stringify(actualStructure, null, 2));
        
    } catch (error) {
        console.error('Error:', error);
    }
    
    console.log('\nPage inspection complete. Browser will stay open for manual inspection.');
    console.log('Press Ctrl+C to close.');
    
    // Keep browser open for manual inspection
    await new Promise(() => {});
})();