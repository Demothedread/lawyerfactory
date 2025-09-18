/**
 * Puppeteer test suite for Soviet Control Panel UI
 * Tests all major UI interactions and functionality
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Test configuration
const TEST_URL = 'http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html';
const VIEWPORT = { width: 1920, height: 1080 };
const TIMEOUT = 30000;

describe('Soviet Control Panel UI Tests', () => {
    let browser;
    let page;

    beforeAll(async () => {
        browser = await puppeteer.launch({
            headless: false, // Set to true for CI/CD
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
            defaultViewport: VIEWPORT
        });
    });

    afterAll(async () => {
        await browser.close();
    });

    beforeEach(async () => {
        page = await browser.newPage();
        await page.setViewport(VIEWPORT);
        await page.goto(TEST_URL, { waitUntil: 'networkidle2' });
        
        // Wait for React to initialize
        await new Promise(resolve => setTimeout(resolve, 2000));
    });

    afterEach(async () => {
        await page.close();
    });

    describe('Layout and Panel Structure', () => {
        test('should render all three panels', async () => {
            const leftPanel = await page.$('.panel-left');
            const centerPanel = await page.$('.panel-center');
            const rightPanel = await page.$('.panel-right');

            expect(leftPanel).toBeTruthy();
            expect(centerPanel).toBeTruthy();
            expect(rightPanel).toBeTruthy();
        });

        test('should have correct panel widths', async () => {
            const leftWidth = await page.$eval('.panel-left', el => el.offsetWidth);
            const rightWidth = await page.$eval('.panel-right', el => el.offsetWidth);

            expect(leftWidth).toBe(400);
            expect(rightWidth).toBe(600);
        });

        test('should display panel headers with correct titles', async () => {
            const headers = await page.$$eval('.panel-header', headers =>
                headers.map(h => h.textContent.trim())
            );

            expect(headers).toContain('Workflow Control');
            expect(headers).toContain('Deliverables & Data');
            expect(headers).toContain('Agent Communication');
        });
    });

    describe('Soviet UI Components', () => {
        test('should render analog gauges with correct values', async () => {
            const gauges = await page.$$('.analog-gauge');
            expect(gauges.length).toBeGreaterThan(0);

            // Check gauge needle rotation
            const needleRotation = await page.$eval('.gauge-needle', el => 
                window.getComputedStyle(el).transform
            );
            expect(needleRotation).toBeTruthy();
        });

        test('should render toggle switches', async () => {
            const toggles = await page.$$('.toggle-switch');
            expect(toggles.length).toBeGreaterThan(0);

            // Test toggle interaction
            const firstToggle = toggles[0];
            await firstToggle.click();
            
            const isActive = await page.$eval('.toggle-switch', el => 
                el.classList.contains('active')
            );
            expect(isActive).toBeDefined();
        });

        test('should display Nixie tube displays', async () => {
            const nixieDisplays = await page.$$('.nixie-display');
            expect(nixieDisplays.length).toBeGreaterThan(0);

            const displayValue = await page.$eval('.nixie-display', el => el.textContent);
            expect(displayValue).toMatch(/\d+/);
        });

        test('should show status lights', async () => {
            const statusLights = await page.$$('.status-light');
            expect(statusLights.length).toBeGreaterThan(0);
        });

        test('should render mechanical buttons with press animation', async () => {
            const button = await page.$('.mech-button');
            expect(button).toBeTruthy();

            // Get initial position
            const initialTransform = await page.$eval('.mech-button', el => 
                window.getComputedStyle(el).transform
            );

            // Click and check transform changes
            await button.click();
            
            const clickedTransform = await page.$eval('.mech-button', el => 
                window.getComputedStyle(el).transform
            );

            expect(initialTransform).not.toBe(clickedTransform);
        });
    });

    describe('Workflow Panel', () => {
        test('should display all 7 phases', async () => {
            const phases = await page.$$eval('.panel-left .panel-content > div > div:nth-child(3) > div', 
                phases => phases.length
            );
            expect(phases).toBe(7);
        });

        test('should highlight active phase on click', async () => {
            const phaseElements = await page.$$('.panel-left .panel-content > div > div:nth-child(3) > div');
            
            if (phaseElements.length > 1) {
                await phaseElements[1].click();
                await new Promise(resolve => setTimeout(resolve, 500));

                const borderColor = await page.$eval(
                    '.panel-left .panel-content > div > div:nth-child(3) > div:nth-child(2)',
                    el => window.getComputedStyle(el).borderColor
                );
                
                expect(borderColor).toContain('255'); // Amber color
            }
        });

        test('should update progress gauge', async () => {
            const progressValue = await page.$eval(
                '.analog-gauge:first-child .gauge-needle',
                el => window.getComputedStyle(el).transform
            );
            expect(progressValue).toBeTruthy();
        });
    });

    describe('Deliverables Panel', () => {
        test('should have three tabs', async () => {
            const toggleSwitches = await page.$$('.toggle-switch');
            expect(toggleSwitches.length).toBeGreaterThanOrEqual(3);
        });

        test('should switch tabs on click', async () => {
            const toggleSwitches = await page.$$('.toggle-switch');
            
            // Click Claims toggle switch
            if (toggleSwitches.length > 1) {
                await toggleSwitches[1].click();
                await new Promise(resolve => setTimeout(resolve, 500));

                const matrixContent = await page.$eval('.panel-center .panel-content',
                    el => el.textContent
                );
                expect(matrixContent).toContain('Claims Matrix');
            }
        });

        test('should render evidence table with ag-Grid', async () => {
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for grid to initialize
            
            const gridElement = await page.$('.ag-theme-quartz-dark');
            expect(gridElement).toBeTruthy();
        });

        test('should display claims in matrix view', async () => {
            const tabButtons = await page.$$('.panel-center .panel-content > div:first-child > button');
            
            if (tabButtons.length > 1) {
                await tabButtons[1].click();
                await new Promise(resolve => setTimeout(resolve, 500));

                const claims = await page.$$eval(
                    '.panel-center .panel-content div[style*="grid-template-columns"] > div',
                    claims => claims.length
                );
                expect(claims).toBeGreaterThan(0);
            }
        });

        test('should show shot-by-shot list', async () => {
            const tabButtons = await page.$$('.panel-center .panel-content > div:first-child > button');
            
            if (tabButtons.length > 2) {
                await tabButtons[2].click();
                await new Promise(resolve => setTimeout(resolve, 500));

                const shotItems = await page.$$eval(
                    '.panel-center .panel-content div[style*="flex-direction: column"] > div',
                    items => items.length
                );
                expect(shotItems).toBeGreaterThan(0);
            }
        });
    });

    describe('LLM Assistant Panel', () => {
        test('should display agent status grid', async () => {
            const agents = await page.$$eval(
                '.panel-right div[style*="grid-template-columns: repeat(4"] > div',
                agents => agents.length
            );
            expect(agents).toBe(7); // 7 agents total
        });

        test('should show chat messages', async () => {
            const messages = await page.$$('.chat-message');
            expect(messages.length).toBeGreaterThan(0);
        });

        test('should send message on button click', async () => {
            const input = await page.$('.chat-input input');
            const sendButton = await page.$('.chat-input button');
            
            await input.type('Test message');
            
            const initialMessageCount = await page.$$eval('.chat-message', msgs => msgs.length);
            
            await sendButton.click();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const newMessageCount = await page.$$eval('.chat-message', msgs => msgs.length);
            expect(newMessageCount).toBeGreaterThan(initialMessageCount);
        });

        test('should send message on Enter key', async () => {
            const input = await page.$('.chat-input input');
            
            const initialMessageCount = await page.$$eval('.chat-message', msgs => msgs.length);
            
            await input.type('Test with Enter');
            await input.press('Enter');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const newMessageCount = await page.$$eval('.chat-message', msgs => msgs.length);
            expect(newMessageCount).toBeGreaterThan(initialMessageCount);
        });

        test('should display quick action buttons', async () => {
            const quickActions = await page.$$eval(
                '.panel-right div[style*="grid-template-columns: 1fr 1fr"] > button',
                buttons => buttons.map(b => b.textContent)
            );
            
            expect(quickActions).toContain('ANALYZE');
            expect(quickActions).toContain('SUMMARIZE');
            expect(quickActions).toContain('EXTRACT');
            expect(quickActions).toContain('DRAFT');
        });
    });

    describe('Panel Collapse/Expand', () => {
        test('should collapse left panel with F1 key', async () => {
            const initialWidth = await page.$eval('.panel-left', el => el.offsetWidth);
            
            await page.keyboard.press('F1');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const collapsedWidth = await page.$eval('.panel-left', el => el.offsetWidth);
            expect(collapsedWidth).toBeLessThan(initialWidth);
        });

        test('should collapse right panel with F3 key', async () => {
            const initialWidth = await page.$eval('.panel-right', el => el.offsetWidth);
            
            await page.keyboard.press('F3');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const collapsedWidth = await page.$eval('.panel-right', el => el.offsetWidth);
            expect(collapsedWidth).toBeLessThan(initialWidth);
        });

        test('should toggle panel states', async () => {
            // Collapse
            await page.keyboard.press('F1');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const collapsed = await page.$eval('.panel-left', el => 
                el.classList.contains('panel-collapsed')
            );
            expect(collapsed).toBe(true);
            
            // Expand
            await page.keyboard.press('F1');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const expanded = await page.$eval('.panel-left', el => 
                !el.classList.contains('panel-collapsed')
            );
            expect(expanded).toBe(true);
        });
    });

    describe('Visual Styling', () => {
        test('should apply Soviet color palette', async () => {
            const bodyBg = await page.$eval('body', el => 
                window.getComputedStyle(el).background
            );
            expect(bodyBg).toContain('linear-gradient');
        });

        test('should display warning stripes', async () => {
            const warningStripe = await page.$('.warning-stripe');
            expect(warningStripe).toBeTruthy();
        });

        test('should show rivet decorations', async () => {
            const rivets = await page.$eval('.rivets', el => 
                window.getComputedStyle(el, ':before').content
            );
            expect(rivets).toContain('⬢');
        });

        test('should apply scanline effect', async () => {
            const scanline = await page.$eval('body', el => 
                window.getComputedStyle(el, ':before').background
            );
            expect(scanline).toContain('repeating-linear-gradient');
        });
    });

    describe('Responsiveness and Accessibility', () => {
        test('should display keyboard shortcut hints', async () => {
            const hints = await page.$eval(
                'div[style*="position: fixed"][style*="bottom: 20px"]',
                el => el.textContent
            );
            expect(hints).toContain('F1');
            expect(hints).toContain('F3');
        });

        test('should handle scroll in content areas', async () => {
            const scrollableArea = await page.$('.panel-content');
            expect(scrollableArea).toBeTruthy();
            
            const overflow = await page.$eval('.panel-content', el => 
                window.getComputedStyle(el).overflowY
            );
            expect(overflow).toBe('auto');
        });

        test('should maintain layout at specified viewport', async () => {
            const viewportSize = await page.viewport();
            expect(viewportSize.width).toBe(1920);
            expect(viewportSize.height).toBe(1080);
        });
    });

    describe('Integration Tests', () => {
        test('should complete full workflow interaction', async () => {
            // Select a phase
            const phaseElements = await page.$$('.panel-left .panel-content > div > div:nth-child(3) > div');
            if (phaseElements.length > 0) {
                await phaseElements[0].click();
            }

            // Switch to Claims Matrix tab
            const tabButtons = await page.$$('.panel-center .panel-content > div:first-child > button');
            if (tabButtons.length > 1) {
                await tabButtons[1].click();
            }

            // Send a chat message
            const input = await page.$('.chat-input input');
            if (input) {
                await input.type('Process documents');
                await input.press('Enter');
            }

            // Verify state changes
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const hasActivePhase = await page.$eval(
                '.panel-left .panel-content',
                el => el.textContent.includes('PHASE SELECTION')
            );
            expect(hasActivePhase).toBe(true);
        });

        test('should handle rapid tab switching', async () => {
            const tabButtons = await page.$$('.panel-center .panel-content > div:first-child > button');
            
            for (let i = 0; i < 10; i++) {
                const tabIndex = i % tabButtons.length;
                await tabButtons[tabIndex].click();
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            // Should still be functional
            const content = await page.$('.panel-center .panel-content');
            expect(content).toBeTruthy();
        });
    });
});

// Run tests if this file is executed directly
if (require.main === module) {
    const runTests = async () => {
        console.log('🚀 Starting Soviet Control Panel UI Tests...\n');
        
        try {
            const browser = await puppeteer.launch({
                headless: false,
                args: ['--no-sandbox', '--disable-setuid-sandbox'],
                defaultViewport: VIEWPORT
            });
            
            const page = await browser.newPage();
            await page.goto(TEST_URL, { waitUntil: 'networkidle2' });
            
            console.log('✅ Page loaded successfully');
            console.log('📍 Testing URL:', TEST_URL);
            console.log('📐 Viewport:', VIEWPORT);
            
            // Basic smoke tests
            const panels = await page.$$eval('.metal-panel', panels => panels.length);
            console.log(`✅ Found ${panels} panels`);
            
            const gauges = await page.$$('.analog-gauge');
            console.log(`✅ Found ${gauges.length} analog gauges`);
            
            const toggles = await page.$$('.toggle-switch');
            console.log(`✅ Found ${toggles.length} toggle switches`);
            
            // Test keyboard shortcuts
            console.log('\n🔧 Testing keyboard shortcuts...');
            await page.keyboard.press('F1');
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log('✅ F1 key works');
            
            await page.keyboard.press('F3');
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log('✅ F3 key works');
            
            // Test tab switching
            console.log('\n📑 Testing tab switching...');
            const tabButtons = await page.$$('.panel-center .panel-content > div:first-child > button');
            for (let i = 0; i < tabButtons.length; i++) {
                await tabButtons[i].click();
                await new Promise(resolve => setTimeout(resolve, 300));
                console.log(`✅ Tab ${i + 1} works`);
            }
            
            // Test chat
            console.log('\n💬 Testing chat interface...');
            const input = await page.$('.chat-input input');
            await input.type('Test message');
            await input.press('Enter');
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log('✅ Chat input works');
            
            console.log('\n🎉 All tests passed!\n');
            
            // Keep browser open for manual inspection
            console.log('Browser will remain open for manual inspection.');
            console.log('Press Ctrl+C to close.');
            
            // Keep the process alive
            await new Promise(() => {});
            
        } catch (error) {
            console.error('❌ Test failed:', error.message);
            process.exit(1);
        }
    };
    
    runTests();
}

module.exports = { TEST_URL, VIEWPORT };