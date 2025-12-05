#!/usr/bin/env node

/**
 * Quick test runner script for Bizpulse Portal
 * Usage: node run-tests.js [options]
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🧪 Bizpulse Portal - Test Runner\n');

// Check if Playwright is installed
const playwrightInstalled = fs.existsSync(
  path.join(__dirname, 'node_modules', '@playwright', 'test')
);

if (!playwrightInstalled) {
  console.log('❌ Playwright not installed. Installing...');
  execSync('npm install -D @playwright/test', { stdio: 'inherit' });
  console.log('✅ Installing Playwright browsers...');
  execSync('npx playwright install', { stdio: 'inherit' });
}

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0] || 'all';

const commands = {
  all: 'npx playwright test',
  ui: 'npx playwright test --ui',
  headed: 'npx playwright test --headed',
  dashboard: 'npx playwright test tests/dashboard.spec.js',
  auth: 'npx playwright test tests/auth.spec.js',
  filters: 'npx playwright test tests/filters.spec.js',
  category: 'npx playwright test tests/category-analysis.spec.js',
  customer: 'npx playwright test tests/customer-insights.spec.js',
  chatbot: 'npx playwright test tests/chatbot.spec.js',
  report: 'npx playwright show-report',
  help: () => {
    console.log(`
Available commands:
  all        - Run all tests (default)
  ui         - Run tests in interactive UI mode
  headed     - Run tests with visible browser
  dashboard  - Run dashboard tests only
  auth       - Run authentication tests only
  filters    - Run filter tests only
  category   - Run category analysis tests only
  customer   - Run customer insights tests only
  chatbot    - Run chatbot tests only
  report     - Show test report
  help       - Show this help message

Examples:
  node run-tests.js
  node run-tests.js ui
  node run-tests.js dashboard
    `);
    process.exit(0);
  }
};

if (command === 'help') {
  commands.help();
} else {
  const testCommand = commands[command] || commands.all;
  console.log(`Running: ${testCommand}\n`);
  
  try {
    execSync(testCommand, { stdio: 'inherit' });
  } catch (error) {
    console.error('\n❌ Tests failed');
    process.exit(1);
  }
}

