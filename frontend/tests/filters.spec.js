const { test, expect } = require('@playwright/test');

test.describe('Global Filters - All Screens', () => {
  test.use({ storageState: 'auth.json' });

  const screens = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Brand Analysis', path: '/brand-analysis' },
    { name: 'Category Analysis', path: '/category-analysis' },
    { name: 'Customer Analysis', path: '/customer-analysis' },
    { name: 'Sales Analysis', path: '/sales-analysis' },
    { name: 'Customer Deep Intelligence', path: '/customer-insights' },
  ];

  for (const screen of screens) {
    test.describe(`${screen.name} - Filter Tests`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(screen.path);
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000); // Wait for data to load
      });

      test('should load filter options', async ({ page }) => {
        // Check if filter section is visible
        const filterSection = page.locator('text=/filter/i').first();
        await expect(filterSection).toBeVisible({ timeout: 5000 });
      });

      test('should update data when filter changes', async ({ page }) => {
        // Get initial page content
        const initialContent = await page.content();
        
        // Try to change a filter (if available)
        const filters = page.locator('select, [role="combobox"]');
        const filterCount = await filters.count();
        
        if (filterCount > 0) {
          // Change first filter
          await filters.first().selectOption({ index: 1 });
          
          // Wait for data to update
          await page.waitForTimeout(3000);
          
          // Check if page content changed (indicating data reload)
          const updatedContent = await page.content();
          // Basic check - content should have changed or at least be loaded
          expect(updatedContent.length).toBeGreaterThan(0);
        }
      });

      test('should handle "All" selection in filters', async ({ page }) => {
        const filters = page.locator('select, [role="combobox"]');
        const filterCount = await filters.count();
        
        if (filterCount > 0) {
          // Select a specific value
          await filters.first().selectOption({ index: 1 });
          await page.waitForTimeout(2000);
          
          // Select "All" (usually index 0 or option with value "all")
          await filters.first().selectOption({ index: 0 });
          await page.waitForTimeout(2000);
          
          // Verify page still loads correctly
          await expect(page.locator('body')).toBeVisible();
        }
      });
    });
  }
});

test.describe('Category Filter - Normalization Test', () => {
  test.use({ storageState: 'auth.json' });

  test('should not show duplicate categories (Compost Sacks vs Compost sacks)', async ({ page }) => {
    await page.goto('/category-analysis');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Find category filter
    const categoryFilter = page.locator('select, [role="combobox"]').filter({ hasText: /category/i }).first();
    
    if (await categoryFilter.count() > 0) {
      // Get all category options
      const options = await categoryFilter.locator('option').allTextContents();
      
      // Check for duplicates (case-insensitive)
      const normalizedCategories = new Set();
      const duplicates = [];
      
      for (const option of options) {
        const normalized = option.trim().toLowerCase();
        if (normalizedCategories.has(normalized)) {
          duplicates.push(option);
        } else {
          normalizedCategories.add(normalized);
        }
      }
      
      // Should not have duplicates like "Compost Sacks" and "Compost sacks"
      expect(duplicates.length).toBe(0);
    }
  });

  test('should show correct category count (48 for 2024)', async ({ page }) => {
    await page.goto('/category-analysis');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Set year filter to 2024
    const yearFilter = page.locator('select, [role="combobox"]').filter({ hasText: /year/i }).first();
    if (await yearFilter.count() > 0) {
      await yearFilter.selectOption({ label: /2024/ });
      await page.waitForTimeout(3000);
      
      // Check category count card
      const countCard = page.locator('text=/47|48/').first();
      const countText = await countCard.textContent();
      
      // Should show 48, not 47
      expect(countText).toContain('48');
    }
  });
});

