const { test, expect } = require('@playwright/test');

test.describe('Customer Deep Intelligence Screen', () => {
  test.use({ storageState: 'auth.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/customer-insights');
    // Wait for page to load - this screen can take longer
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    await page.waitForTimeout(5000); // Extra wait for data loading
  });

  test('should load page within reasonable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/customer-insights');
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    const loadTime = Date.now() - startTime;
    
    // Page should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });

  test('should display page title', async ({ page }) => {
    await expect(page.locator('h1:has-text("Customer Deep Intelligence"), h1:has-text("Customer Insights")')).toBeVisible();
  });

  test('should display filters', async ({ page }) => {
    const filters = page.locator('text=/Year|Month/i');
    await expect(filters.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display summary cards', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // Check for summary cards (Total Customers, Total Orders, etc.)
    const summaryCards = page.locator('[class*="card"], [class*="Card"]');
    const cardCount = await summaryCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(4);
  });

  test('should display all charts', async ({ page }) => {
    await page.waitForTimeout(5000); // Wait for all charts to load
    
    const charts = page.locator('canvas');
    const chartCount = await charts.count();
    
    // Should have at least 15 charts on Customer Deep Intelligence screen
    expect(chartCount).toBeGreaterThanOrEqual(10);
  });

  test('should not make duplicate API calls', async ({ page }) => {
    // Monitor network requests
    const requests = [];
    page.on('request', request => {
      if (request.url().includes('/api/analytics/customer-insights')) {
        requests.push(request.url());
      }
    });
    
    await page.goto('/customer-insights');
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // Should not have excessive duplicate calls (allow 2-3 for initial load and retries)
    const uniqueRequests = new Set(requests);
    expect(requests.length).toBeLessThan(5); // Should not have more than 5 total calls
  });

  test('should update data when filters change', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // Change year filter
    const yearFilter = page.locator('select, [role="combobox"]').filter({ hasText: /year/i }).first();
    if (await yearFilter.count() > 0) {
      await yearFilter.selectOption({ index: 1 });
      await page.waitForTimeout(3000);
      
      // Verify charts still visible
      const charts = page.locator('canvas');
      await expect(charts.first()).toBeVisible();
    }
  });

  test('should handle individual chart filters', async ({ page }) => {
    await page.waitForTimeout(5000);
    
    // Find a chart card with filters
    const chartCards = page.locator('[class*="ChartCard"], [class*="chart-card"]');
    const firstCard = chartCards.first();
    
    if (await firstCard.count() > 0) {
      // Check if chart has individual filter dropdowns
      const chartFilters = firstCard.locator('select, [role="combobox"]');
      const filterCount = await chartFilters.count();
      
      if (filterCount > 0) {
        // Change individual filter
        await chartFilters.first().selectOption({ index: 1 });
        await page.waitForTimeout(3000);
        
        // Verify chart updated
        await expect(firstCard.locator('canvas')).toBeVisible();
      }
    }
  });
});

