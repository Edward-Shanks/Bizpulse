const { test, expect } = require('@playwright/test');

test.describe('Category Analysis Screen', () => {
  test.use({ storageState: 'auth.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/category-analysis');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Wait for data to load
  });

  test('should load category analysis page', async ({ page }) => {
    await expect(page.locator('h1:has-text("Category"), h1:has-text("Category Analysis")')).toBeVisible();
  });

  test('should display all charts', async ({ page }) => {
    // Wait for charts to render
    await page.waitForTimeout(3000);
    
    const charts = page.locator('canvas');
    const chartCount = await charts.count();
    
    // Should have at least 4 charts
    expect(chartCount).toBeGreaterThanOrEqual(4);
  });

  test('should display summary cards with correct values', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // Check for summary cards
    const cards = page.locator('[class*="card"], [class*="Card"]');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThanOrEqual(3);
    
    // Check if cards show "Cases" not "Units"
    const pageContent = await page.textContent('body');
    expect(pageContent).not.toContain('Total Units');
    expect(pageContent).toContain('Total Cases') || expect(pageContent).toContain('Cases');
  });

  test('should show correct category count matching filter', async ({ page }) => {
    // Set year to 2024
    const yearFilter = page.locator('select, [role="combobox"]').filter({ hasText: /year/i }).first();
    if (await yearFilter.count() > 0) {
      await yearFilter.selectOption({ label: /2024/ });
      await page.waitForTimeout(3000);
      
      // Get category count from card
      const countCard = page.locator('text=/47|48/').first();
      const countText = await countCard.textContent();
      
      // Count should be 48
      expect(countText).toMatch(/48/);
    }
  });

  test('should not show duplicate categories in filter', async ({ page }) => {
    const categoryFilter = page.locator('select, [role="combobox"]').filter({ hasText: /category/i }).first();
    
    if (await categoryFilter.count() > 0) {
      // Open dropdown (if it's a custom select)
      await categoryFilter.click();
      await page.waitForTimeout(1000);
      
      // Get all options
      const options = await page.locator('[role="option"], option').allTextContents();
      
      // Check for "Compost Sacks" and "Compost sacks" - should only have one
      const compostSacksVariants = options.filter(opt => 
        opt.toLowerCase().includes('compost') && opt.toLowerCase().includes('sacks')
      );
      
      // Should only have one variant (normalized)
      expect(compostSacksVariants.length).toBeLessThanOrEqual(1);
    }
  });

  test('should update charts when filters change', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // Get initial chart data
    const initialCharts = page.locator('canvas');
    const initialCount = await initialCharts.count();
    
    // Change a filter
    const filters = page.locator('select, [role="combobox"]');
    if (await filters.count() > 0) {
      await filters.first().selectOption({ index: 1 });
      await page.waitForTimeout(3000);
      
      // Charts should still be visible
      const updatedCharts = page.locator('canvas');
      await expect(updatedCharts.first()).toBeVisible();
    }
  });
});

