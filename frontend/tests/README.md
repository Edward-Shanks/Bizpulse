# Bizpulse Portal - Test Suite

This directory contains end-to-end tests for the Bizpulse Portal using Playwright.

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install -D @playwright/test
   npx playwright install
   ```

2. **Set Up Test Credentials**
   Create a `.env.test` file in the frontend directory:
   ```
   TEST_EMAIL=your-test-email@example.com
   TEST_PASSWORD=your-test-password
   ```

3. **Start Servers**
   - Backend: `cd backend && uvicorn server:app --reload`
   - Frontend: `cd frontend && npm start`

## Running Tests

### Run All Tests
```bash
npx playwright test
```

### Run Specific Test File
```bash
npx playwright test tests/dashboard.spec.js
```

### Run Tests in UI Mode (Interactive)
```bash
npx playwright test --ui
```

### Run Tests in Headed Mode (See Browser)
```bash
npx playwright test --headed
```

### Run Tests for Specific Browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run Tests with Screenshots
```bash
npx playwright test --screenshot=on
```

### Generate HTML Report
```bash
npx playwright show-report
```

## Test Files

- `auth.spec.js` - Authentication and login tests
- `dashboard.spec.js` - Dashboard screen tests
- `filters.spec.js` - Global filter functionality tests
- `category-analysis.spec.js` - Category Analysis screen tests
- `customer-insights.spec.js` - Customer Deep Intelligence tests
- `navigation.spec.js` - Navigation and routing tests
- `chatbot.spec.js` - AI Chatbot functionality tests
- `terminology.spec.js` - "Cases" vs "Units" terminology tests

## Test Structure

Each test file follows this structure:
```javascript
const { test, expect } = require('@playwright/test');

test.describe('Feature Name', () => {
  test.use({ storageState: 'auth.json' }); // Use saved auth state

  test.beforeEach(async ({ page }) => {
    // Setup before each test
  });

  test('should do something', async ({ page }) => {
    // Test implementation
  });
});
```

## Writing New Tests

1. Create a new file in `tests/` directory
2. Import Playwright test utilities
3. Use `test.use({ storageState: 'auth.json' })` for authenticated tests
4. Write descriptive test names
5. Use `await expect()` for assertions
6. Add appropriate waits for async operations

## Debugging Tests

### Run in Debug Mode
```bash
npx playwright test --debug
```

### Use Playwright Inspector
```bash
PWDEBUG=1 npx playwright test
```

### View Trace
```bash
npx playwright show-trace trace.zip
```

## CI/CD Integration

Tests can be run in CI/CD pipelines. Example GitHub Actions:

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices

1. **Use data-testid attributes** for reliable element selection
2. **Wait for network idle** before assertions
3. **Use page.waitForTimeout() sparingly** - prefer waiting for specific conditions
4. **Keep tests independent** - each test should be able to run alone
5. **Use descriptive test names** that explain what is being tested
6. **Clean up after tests** if needed (logout, reset state, etc.)

## Troubleshooting

### Tests failing due to timing
- Increase `waitForTimeout` values
- Use `page.waitForSelector()` instead of `waitForTimeout`
- Check for loading indicators before assertions

### Element not found
- Check if element is in an iframe
- Verify element is visible (not hidden)
- Check if element needs scrolling into view

### Authentication issues
- Run login test first to generate `auth.json`
- Check if token expires
- Verify backend is running

