# Manual Testing Checklist for Bizpulse Portal

## Pre-Testing Setup
- [ ] Backend server running on `http://localhost:8000`
- [ ] Frontend server running on `http://localhost:3000`
- [ ] MongoDB connected and populated with data
- [ ] Valid test user credentials available
- [ ] Browser console open to check for errors

## Authentication & Login
- [ ] Login page loads correctly
- [ ] Can login with valid credentials
- [ ] Error message shows for invalid credentials
- [ ] Session persists after page refresh
- [ ] Logout functionality works
- [ ] Redirects to login when not authenticated

## Dashboard Screen (`/dashboard`)
- [ ] Page loads without errors
- [ ] All 8 charts render correctly
- [ ] Summary cards show correct values
- [ ] Global filters (Year, Month, Business, Channel, Brand, Category) work
- [ ] Individual chart filters work and override global filters
- [ ] Global filter changes reset individual chart filters
- [ ] Charts update when filters change
- [ ] "Cases" terminology used (not "Units")
- [ ] No console errors

## Brand Analysis Screen (`/brand-analysis`)
- [ ] Page loads correctly
- [ ] All 4 charts render
- [ ] Global filters work
- [ ] Individual chart filters work
- [ ] Data matches selected filters
- [ ] Charts update when filters change
- [ ] "Cases" terminology used

## Category Analysis Screen (`/category-analysis`)
- [ ] Page loads correctly
- [ ] All 4 charts render
- [ ] Global filters work
- [ ] Category count matches filter count (48 for 2024)
- [ ] No duplicate categories in filter (e.g., "Compost Sacks" and "Compost sacks" should be merged)
- [ ] Individual chart filters work
- [ ] "Cases" terminology used
- [ ] Table shows "Cases" column header (not "Units")

## Customer Analysis Screen (`/customer-analysis`)
- [ ] Page loads correctly
- [ ] All 4 charts render
- [ ] Global filters work
- [ ] Individual chart filters work
- [ ] Top customers table displays
- [ ] Chart title shows "Cases by Channel" (not "Units by Channel")
- [ ] "Cases" terminology used throughout

## Sales Analysis Screen (`/sales-analysis`)
- [ ] Page loads correctly
- [ ] Charts render
- [ ] Global filters work
- [ ] Individual chart filters work
- [ ] Summary cards show "Total Cases" (not "Total Units")
- [ ] "Cases" terminology used

## Customer Deep Intelligence Screen (`/customer-insights`)
- [ ] Page loads within 10 seconds
- [ ] All 15+ charts render
- [ ] Summary cards display (Total Customers, Total Orders, Total Sales, Avg Order Value)
- [ ] Global filters (Year, Month) work
- [ ] Individual chart filters work for each chart
- [ ] No duplicate API calls (check Network tab)
- [ ] Charts update when filters change
- [ ] Page doesn't freeze or become unresponsive

## Root Cause Analysis Screen (`/root-cause-analysis`)
- [ ] Page loads correctly
- [ ] Issues display correctly
- [ ] Filters work
- [ ] Data updates when filters change

## Projects Screen (`/projects`)
- [ ] Page loads correctly
- [ ] All tabs work (Top Projects, Business Planner, Campaign Cockpit)
- [ ] Charts render
- [ ] Project cards display
- [ ] Filters work

## Cockpit Screen (`/cockpit`)
- [ ] Page loads correctly
- [ ] All widgets display
- [ ] Filters work
- [ ] Data updates correctly

## Reports Screen (`/reports`)
- [ ] Page loads correctly
- [ ] Reports list displays
- [ ] Can generate/view reports
- [ ] Filters work

## Global Filter Functionality (Test on All Screens)
- [ ] Filter options load correctly
- [ ] Dynamic/cascading filters work (selecting Year updates other filters)
- [ ] Multiple selections work
- [ ] "All" selections work correctly
- [ ] Filter selections persist when navigating between screens
- [ ] Clear filters button works (if available)

## Individual Chart Filters (Test on All Screens with Charts)
- [ ] Individual filters override global filters
- [ ] Chart data updates when individual filter changes
- [ ] Filter dropdowns show correct merged values
- [ ] Global filter changes reset individual filters
- [ ] "All" selection in individual filters works

## Navigation
- [ ] All menu items navigate correctly
- [ ] Active page highlighted in sidebar
- [ ] Can navigate between all screens
- [ ] Browser back/forward buttons work
- [ ] URLs are correct for each screen

## AI Chatbot
- [ ] Chatbot button visible (floating action button)
- [ ] Chatbot modal opens when clicked
- [ ] Modal is properly sized (not too small)
- [ ] Can type and send messages
- [ ] Responses appear correctly
- [ ] Chatbot uses "cases" terminology (not "units")
- [ ] Context filters work (if available)
- [ ] Suggested questions work
- [ ] Can close modal
- [ ] Content is scrollable if long

## Terminology Check (All Screens)
- [ ] "Cases" used instead of "Units" in:
  - [ ] Summary cards
  - [ ] Chart titles
  - [ ] Table headers
  - [ ] Tooltips
  - [ ] Chatbot responses
- [ ] No instances of "Total Units" visible
- [ ] No instances of "Units sold" visible
- [ ] No instances of "Units by Channel" visible

## Performance Checks
- [ ] Pages load within reasonable time (< 5 seconds for most, < 10 seconds for Customer Deep Intelligence)
- [ ] No excessive API calls (check Network tab)
- [ ] No memory leaks (check over time)
- [ ] Smooth scrolling
- [ ] Charts render smoothly
- [ ] No lag when changing filters

## Error Handling
- [ ] Error messages display for API failures
- [ ] Loading states show during data fetch
- [ ] Empty states display when no data
- [ ] Network errors handled gracefully
- [ ] Invalid filter combinations handled

## Browser Compatibility
- [ ] Chrome/Edge - All features work
- [ ] Firefox - All features work
- [ ] Safari - All features work (if on Mac)

## Responsive Design (Mobile/Tablet)
- [ ] Layout adapts to smaller screens
- [ ] Filters are accessible on mobile
- [ ] Charts are readable on mobile
- [ ] Navigation works on mobile
- [ ] Touch interactions work

## Data Accuracy
- [ ] Summary card totals match chart totals
- [ ] Filtered data matches filter selections
- [ ] Category count matches filter options
- [ ] No duplicate categories in filters
- [ ] Data updates correctly when filters change

## Security
- [ ] Cannot access protected routes without login
- [ ] Token expires appropriately
- [ ] API calls include authentication
- [ ] No sensitive data in console/logs

## Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader compatible (if applicable)
- [ ] Color contrast is sufficient
- [ ] Focus indicators visible

## Known Issues to Verify Fixed
- [ ] Category normalization works (no "Compost Sacks" vs "Compost sacks" duplicates)
- [ ] Category count shows 48 (not 47) for 2024
- [ ] "Cases" terminology used everywhere (not "Units")
- [ ] Customer Deep Intelligence loads quickly
- [ ] Individual chart filters work correctly
- [ ] Global filter changes reset individual filters

## Test Results Template

**Date:** _______________
**Tester:** _______________
**Browser:** _______________
**OS:** _______________

### Passed Tests: ___ / ___
### Failed Tests: ___ / ___
### Blocked Tests: ___ / ___

### Critical Issues Found:
1. 
2. 
3. 

### Minor Issues Found:
1. 
2. 
3. 

### Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

