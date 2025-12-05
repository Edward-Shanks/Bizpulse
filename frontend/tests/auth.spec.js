const { test, expect } = require('@playwright/test');

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
  });

  test('should display login page correctly', async ({ page }) => {
    // Check if login form elements are visible
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
    
    await emailInput.fill('invalid@example.com');
    await passwordInput.fill('wrongpassword');
    await submitButton.click();
    
    // Wait for error message (adjust selector based on your error display)
    await page.waitForTimeout(2000);
    // Check for error message (adjust based on your implementation)
    const errorMessage = page.locator('text=/invalid|error|incorrect/i');
    await expect(errorMessage.first()).toBeVisible({ timeout: 5000 });
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Replace with your test credentials
    const TEST_EMAIL = process.env.TEST_EMAIL || 'test@example.com';
    const TEST_PASSWORD = process.env.TEST_PASSWORD || 'testpassword';
    
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
    
    await emailInput.fill(TEST_EMAIL);
    await passwordInput.fill(TEST_PASSWORD);
    await submitButton.click();
    
    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard**', { timeout: 10000 });
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/.*dashboard.*/i);
  });

  test('should persist login session', async ({ page, context }) => {
    // Login first
    const TEST_EMAIL = process.env.TEST_EMAIL || 'test@example.com';
    const TEST_PASSWORD = process.env.TEST_PASSWORD || 'testpassword';
    
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
    
    await emailInput.fill(TEST_EMAIL);
    await passwordInput.fill(TEST_PASSWORD);
    await submitButton.click();
    await page.waitForURL('**/dashboard**', { timeout: 10000 });
    
    // Save storage state
    await context.storageState({ path: 'auth.json' });
    
    // Create new context with saved state
    const newContext = await context.browser().newContext({ storageState: 'auth.json' });
    const newPage = await newContext.newPage();
    
    // Navigate to dashboard - should be logged in
    await newPage.goto('/dashboard');
    await expect(newPage).toHaveURL(/.*dashboard.*/i);
    
    await newContext.close();
  });
});

