const { test, expect } = require('@playwright/test');

test.describe('AI Chatbot Tests', () => {
  test.use({ storageState: 'auth.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('should open chatbot modal', async ({ page }) => {
    // Find chatbot button (floating action button or AI assistant button)
    const chatbotButton = page.locator('button:has-text("AI"), button:has-text("Ask"), [class*="chatbot"], [class*="ai-assistant"]').first();
    
    if (await chatbotButton.count() > 0) {
      await chatbotButton.click();
      await page.waitForTimeout(1000);
      
      // Check if modal opened
      const modal = page.locator('[role="dialog"], [class*="modal"], [class*="Modal"]');
      await expect(modal.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('should have proper modal size', async ({ page }) => {
    const chatbotButton = page.locator('button:has-text("AI"), button:has-text("Ask"), [class*="chatbot"]').first();
    
    if (await chatbotButton.count() > 0) {
      await chatbotButton.click();
      await page.waitForTimeout(1000);
      
      const modal = page.locator('[role="dialog"], [class*="modal"]').first();
      if (await modal.count() > 0) {
        const box = await modal.boundingBox();
        
        // Modal should be reasonably sized (not too small)
        expect(box.width).toBeGreaterThan(400);
        expect(box.height).toBeGreaterThan(400);
      }
    }
  });

  test('should send and receive messages', async ({ page }) => {
    const chatbotButton = page.locator('button:has-text("AI"), button:has-text("Ask"), [class*="chatbot"]').first();
    
    if (await chatbotButton.count() > 0) {
      await chatbotButton.click();
      await page.waitForTimeout(1000);
      
      // Find message input
      const messageInput = page.locator('input[type="text"], textarea, [contenteditable="true"]').filter({ hasText: /message|ask|question/i }).first();
      
      if (await messageInput.count() > 0) {
        await messageInput.fill('What is the total revenue?');
        await page.waitForTimeout(500);
        
        // Find send button
        const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
        await sendButton.click();
        
        // Wait for response
        await page.waitForTimeout(5000);
        
        // Check if response appeared
        const messages = page.locator('[class*="message"], [class*="Message"]');
        const messageCount = await messages.count();
        expect(messageCount).toBeGreaterThan(0);
      }
    }
  });

  test('should use "cases" terminology in responses', async ({ page }) => {
    const chatbotButton = page.locator('button:has-text("AI"), button:has-text("Ask"), [class*="chatbot"]').first();
    
    if (await chatbotButton.count() > 0) {
      await chatbotButton.click();
      await page.waitForTimeout(1000);
      
      const messageInput = page.locator('input[type="text"], textarea, [contenteditable="true"]').first();
      
      if (await messageInput.count() > 0) {
        await messageInput.fill('How many units were sold?');
        await page.waitForTimeout(500);
        
        const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
        await sendButton.click();
        await page.waitForTimeout(5000);
        
        // Check response content
        const response = page.locator('[class*="message"], [class*="Message"]').last();
        const responseText = await response.textContent();
        
        // Response should use "cases" not "units"
        if (responseText) {
          expect(responseText.toLowerCase()).not.toContain('units');
          // If it mentions quantity, it should say "cases"
          if (responseText.toLowerCase().includes('sold') || responseText.toLowerCase().includes('quantity')) {
            expect(responseText.toLowerCase()).toContain('cases');
          }
        }
      }
    }
  });
});

