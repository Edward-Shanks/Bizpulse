# Comprehensive Testing Guide for Bizpulse Portal

## Overview
This guide provides a complete testing strategy for the Bizpulse Portal, including automated end-to-end tests, manual testing checklists, and testing tools.

## Testing Tools Recommended

### 1. **Playwright** (Recommended for E2E Testing)
- **Why**: Modern, fast, reliable, supports all browsers (Chrome, Firefox, Safari, Edge)
- **Features**: 
  - Auto-waiting for elements
  - Screenshot/video recording
  - Network interception
  - Multi-browser testing
  - Mobile device emulation

### 2. **Jest + React Testing Library** (For Component Testing)
- **Why**: Standard for React component testing
- **Features**: Unit tests, component rendering tests

### 3. **Postman/Newman** (For API Testing)
- **Why**: Comprehensive API testing
- **Features**: Automated API endpoint testing

## Installation & Setup

### Step 1: Install Playwright
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

### Step 2: Create Test Configuration
See `playwright.config.js` (will be created)

### Step 3: Run Tests
```bash
# Run all tests
npx playwright test

# Run tests in UI mode (interactive)
npx playwright test --ui

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test tests/dashboard.spec.js

# Generate test report
npx playwright show-report
```

## Test Coverage Plan

### Screens to Test:
1. ✅ Login Page
2. ✅ Dashboard (DashboardNew.js)
3. ✅ Brand Analysis (BrandAnalysisNew.js)
4. ✅ Category Analysis (CategoryAnalysisNew.js)
5. ✅ Customer Analysis (CustomerAnalysisNew.js)
6. ✅ Sales Analysis (SalesAnalysis.js)
7. ✅ Customer Deep Intelligence (CustomerInsights.js)
8. ✅ Root Cause Analysis (RootCauseAnalysis.js)
9. ✅ Projects (ProjectsNew.js)
10. ✅ Cockpit (CockpitNew.js)
11. ✅ Reports (Reports.js)

### Test Scenarios Per Screen:

#### 1. **Login & Authentication**
- ✅ Valid login
- ✅ Invalid credentials
- ✅ Token persistence
- ✅ Logout functionality

#### 2. **Global Filters** (All Screens)
- ✅ Filter options load correctly
- ✅ Dynamic/cascading filters work
- ✅ Filter selections update data
- ✅ "All" selections work correctly
- ✅ Multiple selections work

#### 3. **Individual Chart Filters** (All Screens with Charts)
- ✅ Individual filters override global filters
- ✅ Chart data updates when individual filter changes
- ✅ Global filter changes reset individual filters
- ✅ Filter dropdowns show correct merged values

#### 4. **Data Display**
- ✅ Charts render correctly
- ✅ Tables display data
- ✅ Summary cards show correct values
- ✅ Loading states work
- ✅ Error states handled

#### 5. **Navigation**
- ✅ All menu items navigate correctly
- ✅ Active page highlighted
- ✅ Breadcrumbs work (if any)

#### 6. **AI Chatbot**
- ✅ Chatbot opens/closes
- ✅ Messages send/receive
- ✅ Context filters work
- ✅ Responses are relevant

## Manual Testing Checklist

### Pre-Testing Setup
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 3000
- [ ] MongoDB connected and populated
- [ ] Valid test user credentials available

### Screen-by-Screen Checklist

#### Dashboard
- [ ] Page loads without errors
- [ ] All 8 charts render
- [ ] Global filters work
- [ ] Individual chart filters work
- [ ] Summary cards show correct totals
- [ ] Charts update when filters change

#### Brand Analysis
- [ ] Page loads
- [ ] All 4 charts render
- [ ] Filters work (Year, Month, Business, Channel, Brand, Category)
- [ ] Individual chart filters work
- [ ] Data matches selected filters

#### Category Analysis
- [ ] Page loads
- [ ] Category count matches filter count (48 categories)
- [ ] All charts render
- [ ] Filters work
- [ ] Category normalization works (no duplicates like "Compost Sacks" vs "Compost sacks")

#### Customer Analysis
- [ ] Page loads
- [ ] All 4 charts render
- [ ] Filters work
- [ ] Top customers table displays
- [ ] "Cases" terminology used (not "Units")

#### Sales Analysis
- [ ] Page loads
- [ ] Charts render
- [ ] Filters work
- [ ] "Cases" terminology used

#### Customer Deep Intelligence
- [ ] Page loads quickly (< 5 seconds)
- [ ] All 15+ charts render
- [ ] Filters work (Year, Month)
- [ ] Individual chart filters work
- [ ] No duplicate API calls

#### Root Cause Analysis
- [ ] Page loads
- [ ] Issues display correctly
- [ ] Filters work

#### Projects
- [ ] Page loads
- [ ] All tabs work
- [ ] Charts render
- [ ] Project cards display

## Automated Test Structure

Tests are organized in `tests/` directory:
- `tests/auth.spec.js` - Authentication tests
- `tests/dashboard.spec.js` - Dashboard tests
- `tests/brand-analysis.spec.js` - Brand Analysis tests
- `tests/category-analysis.spec.js` - Category Analysis tests
- `tests/customer-analysis.spec.js` - Customer Analysis tests
- `tests/sales-analysis.spec.js` - Sales Analysis tests
- `tests/customer-insights.spec.js` - Customer Deep Intelligence tests
- `tests/filters.spec.js` - Global filter tests
- `tests/chatbot.spec.js` - AI Chatbot tests

## Running Tests

### Full Test Suite
```bash
npx playwright test
```

### Specific Screen
```bash
npx playwright test tests/dashboard.spec.js
```

### With Screenshots
```bash
npx playwright test --screenshot=on
```

### Generate HTML Report
```bash
npx playwright show-report
```

## Continuous Integration

Tests can be integrated into CI/CD pipeline:
- GitHub Actions
- GitLab CI
- Jenkins
- Azure DevOps

## Performance Testing

### Load Testing
- Use Playwright's performance metrics
- Test with large datasets
- Monitor API response times

### Lighthouse CI
```bash
npm install -D @lhci/cli
lhci autorun
```

## Bug Reporting Template

When reporting bugs, include:
1. Screen name
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Screenshots/videos
6. Browser/OS information
7. Console errors (if any)

