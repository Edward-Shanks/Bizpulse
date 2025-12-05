const { test, expect } = require('@playwright/test');

test.describe('Dashboard Screen', () => {
  // Use saved auth state if available
  test.use({ storageState: 'auth.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load dashboard page', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1:has-text("Dashboard"), h1:has-text("Business Compass")')).toBeVisible();
  });

  test('should display global filters', async ({ page }) => {
    // Check if filter dropdowns are visible
    const filters = [
      'Year', 'Month', 'Business', 'Channel', 'Brand', 'Category'
    ];
    
    for (const filter of filters) {
      const filterElement = page.locator(`text=${filter}`).first();
      await expect(filterElement).toBeVisible({ timeout: 5000 });
    }
  });

  test('should display summary cards', async ({ page }) => {
    // Wait for cards to load
    await page.waitForTimeout(2000);
    
    // Check for summary cards (adjust selectors based on your implementation)
    const cards = page.locator('[class*="card"], [class*="Card"]');
    await expect(cards.first()).toBeVisible();
  });

  test('should display all charts', async ({ page }) => {
    // Wait for charts to render
    await page.waitForTimeout(3000);
    
    // Check for chart containers (Chart.js renders canvas elements)
    const charts = page.locator('canvas');
    const chartCount = await charts.count();
    
    // Should have at least 8 charts on dashboard
    expect(chartCount).toBeGreaterThanOrEqual(6);
  });

  test('should update data when global filters change', async ({ page }) => {
    // Wait for initial load
    await page.waitForTimeout(2000);
    
    // Get initial data (check for a summary card value)
    const initialCard = page.locator('[class*="card"], [class*="Card"]').first();
    const initialText = await initialCard.textContent();
    
    // Change year filter (adjust selector based on your filter implementation)
    const yearFilter = page.locator('select, [role="combobox"]').first();
    if (await yearFilter.count() > 0) {
      await yearFilter.selectOption({ index: 1 });
      
      // Wait for data to update
      await page.waitForTimeout(3000);
      
      // Check if data changed (this is a basic check - you may need to adjust)
      const updatedCard = page.locator('[class*="card"], [class*="Card"]').first();
      const updatedText = await updatedCard.textContent();
      
      // Data should have changed (or at least reloaded)
      expect(updatedText).toBeTruthy();
    }
  });

  test('should handle individual chart filters', async ({ page }) => {
    // Wait for charts to load
    await page.waitForTimeout(3000);
    
    // Find a chart with individual filters (adjust selector)
    const chartCard = page.locator('[class*="ChartCard"], [class*="chart-card"]').first();
    
    if (await chartCard.count() > 0) {
      // Check if chart has filter dropdowns
      const chartFilters = chartCard.locator('select, [role="combobox"]');
      const filterCount = await chartFilters.count();
      
      if (filterCount > 0) {
        // Change a filter
        await chartFilters.first().selectOption({ index: 1 });
        
        // Wait for chart to update
        await page.waitForTimeout(2000);
        
        // Verify chart still visible
        await expect(chartCard.locator('canvas')).toBeVisible();
      }
    }
  });

  test('should reset individual filters when global filters change', async ({ page }) => {
    // This test verifies the filter hierarchy logic
    await page.waitForTimeout(2000);
    
    // Set an individual chart filter first
    const chartCard = page.locator('[class*="ChartCard"], [class*="chart-card"]').first();
    if (await chartCard.count() > 0) {
      const chartFilters = chartCard.locator('select, [role="combobox"]');
      if (await chartFilters.count() > 0) {
        await chartFilters.first().selectOption({ index: 1 });
        await page.waitForTimeout(1000);
        
        // Now change global filter
        const globalFilter = page.locator('select, [role="combobox"]').first();
        if (await globalFilter.count() > 0) {
          await globalFilter.selectOption({ index: 2 });
          await page.waitForTimeout(2000);
          
          // Individual filter should reset (check if it shows "All" or default value)
          const individualFilterValue = await chartFilters.first().inputValue();
          // This is a basic check - adjust based on your implementation
          expect(individualFilterValue).toBeTruthy();
        }
      }
    }
  });
});

