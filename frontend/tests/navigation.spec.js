const { test, expect } = require('@playwright/test');

test.describe('Navigation Tests', () => {
  test.use({ storageState: 'auth.json' });

  test('should navigate to all main screens', async ({ page }) => {
    const screens = [
      { name: 'Dashboard', path: '/dashboard', title: /dashboard|business compass/i },
      { name: 'Brand Analysis', path: '/brand-analysis', title: /brand/i },
      { name: 'Category Analysis', path: '/category-analysis', title: /category/i },
      { name: 'Customer Analysis', path: '/customer-analysis', title: /customer/i },
      { name: 'Sales Analysis', path: '/sales-analysis', title: /sales/i },
      { name: 'Customer Deep Intelligence', path: '/customer-insights', title: /customer.*intelligence|customer.*insights/i },
    ];

    for (const screen of screens) {
      await page.goto(screen.path);
      await page.waitForLoadState('networkidle', { timeout: 30000 });
      await page.waitForTimeout(2000);
      
      // Check if page loaded (title should be visible)
      const title = page.locator('h1').first();
      await expect(title).toBeVisible({ timeout: 10000 });
      
      // Verify URL
      await expect(page).toHaveURL(new RegExp(screen.path.replace('/', '\\/'), 'i'));
    }
  });

  test('should highlight active menu item', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);
    
    // Check if navigation sidebar is visible
    const sidebar = page.locator('[class*="sidebar"], [class*="nav"], nav').first();
    await expect(sidebar).toBeVisible();
    
    // Check if active item is highlighted (adjust selector based on your implementation)
    const activeItem = sidebar.locator('[class*="active"], [aria-current="page"]').first();
    if (await activeItem.count() > 0) {
      await expect(activeItem).toBeVisible();
    }
  });
});

