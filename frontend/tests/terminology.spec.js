const { test, expect } = require('@playwright/test');

test.describe('Terminology Tests - "Cases" vs "Units"', () => {
  test.use({ storageState: 'auth.json' });

  const screens = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Sales Analysis', path: '/sales-analysis' },
    { name: 'Customer Analysis', path: '/customer-analysis' },
    { name: 'Category Analysis', path: '/category-analysis' },
  ];

  for (const screen of screens) {
    test(`${screen.name} should use "Cases" terminology`, async ({ page }) => {
      await page.goto(screen.path);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Get all text content
      const pageContent = await page.textContent('body');
      
      // Should NOT contain "Units" (except in variable names which users don't see)
      // Check for common "Units" phrases that users would see
      const unitsPhrases = [
        'Total Units',
        'Units sold',
        'Units by',
        ' units',
      ];
      
      for (const phrase of unitsPhrases) {
        expect(pageContent).not.toContain(phrase);
      }
      
      // Should contain "Cases" terminology
      const casesPhrases = [
        'Total Cases',
        'Cases sold',
        'Cases by',
        ' cases',
      ];
      
      let hasCasesTerminology = false;
      for (const phrase of casesPhrases) {
        if (pageContent.includes(phrase)) {
          hasCasesTerminology = true;
          break;
        }
      }
      
      // At least one "Cases" phrase should be present if the screen shows quantity data
      // (Some screens might not show quantity, so this is optional)
      if (pageContent.includes('Total') || pageContent.includes('sold')) {
        // If screen shows totals or sold data, it should use Cases
        expect(hasCasesTerminology || !pageContent.match(/total|sold/i)).toBeTruthy();
      }
    });
  }

  test('Chart titles should use "Cases" not "Units"', async ({ page }) => {
    await page.goto('/customer-analysis');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    const pageContent = await page.textContent('body');
    
    // Should not have "Units by Channel"
    expect(pageContent).not.toContain('Units by Channel');
    
    // Should have "Cases by Channel"
    expect(pageContent).toContain('Cases by Channel');
  });
});

