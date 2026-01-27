# Reports Troubleshooting Guide

## ❌ Common Error: "No data found for the selected filters"

### What This Means:
When you see this error, it means your filter combination doesn't match any data in the database.

---

## 🔍 Why This Happens

### Scenario 1: Invalid Filter Combination
The filters you selected don't have any matching records.

**Example:**
- You selected: Year=2023, Month=Jan, Business=Kinetica, Brand=Goddards
- But: Kinetica doesn't sell Goddards brand products

### Scenario 2: Month Name Format
The month filter might be using abbreviated names (Jan, Feb) but the database has full names (January, February)

### Scenario 3: Special Characters in Names
Business names with commas, ampersands, or special characters might cause issues:
- "Brillo, Goddards & KMPL" contains comma and ampersand
- These might be parsed differently by the backend

---

## ✅ How to Fix

### Solution 1: Clear Filters
1. Click the **"Clear Filters"** button
2. Start with NO filters (this will show all data)
3. Click a report to download - this should work!

### Solution 2: Use Fewer Filters
Instead of selecting 6 filters, try:
1. Start with just **Year** (e.g., 2024)
2. Generate report - if it works, gradually add more filters
3. Add **Business** next
4. Then **Brand**, etc.

### Solution 3: Use the Dynamic Filters Correctly
The filters are dynamic - they update based on your selections:
1. Select **Year = 2024**
2. **Wait** for other dropdowns to update
3. Now select from the **updated** Business dropdown (only businesses with 2024 data)
4. Continue this pattern

### Solution 4: Try Pre-defined Reports First
Pre-defined reports are more robust:
1. Clear all filters
2. Click "Executive Summary Report" - should work with all data
3. If you want filtered data, select just 1-2 filters before clicking

---

## 🎯 Best Practices

### ✅ Do This:
1. **Start broad, then narrow down**:
   - First: Year only → Generate report
   - Then: Year + Business → Generate report
   - Finally: Year + Business + Brand → Generate report

2. **Watch the filter counter**:
   - "2 filter(s) applied" = reasonable
   - "6 filter(s) applied" = might be too specific

3. **Use multi-select wisely**:
   - Selecting multiple years = MORE data ✅
   - Selecting 1 year + 1 brand = LESS data ⚠️

4. **Test without filters first**:
   - Click report with NO filters applied
   - If it works, add filters one by one

### ❌ Avoid This:
1. **Don't select too many specific filters at once**
   - Bad: Year + Month + Business + Brand + Channel + Category
   - Good: Year + Business

2. **Don't select incompatible filters**
   - E.g., Brand that doesn't belong to selected Business
   - The dynamic filters should prevent this, but just in case

3. **Don't use abbreviated month names if they don't work**
   - If "Jan" doesn't work, the database might use "January"

---

## 🐛 Debugging Steps

### Step 1: Test with NO filters
```
1. Click "Clear Filters"
2. Click "Executive Summary Report"
3. Does it work? → YES = Filters are the issue
                  → NO = Different problem
```

### Step 2: Test with ONE filter only
```
1. Clear filters
2. Select ONLY Year = 2024
3. Click "Executive Summary Report"
4. Does it work? → YES = Add one more filter
                  → NO = Check if 2024 has data
```

### Step 3: Check filter combinations
```
1. Select Year = 2024
2. Wait for Business dropdown to update
3. Select a Business from the UPDATED list
4. Wait for Brand dropdown to update
5. Select a Brand from the UPDATED list
6. Generate report
```

---

## 📊 Understanding Your Error

Looking at your error:
```
years=2023&months=Jan&businesses=Brillo, Goddards & KMPL&
channels=Grocery,Wholesale&brands=Goddards&categories=Cloths,Polish
```

**Potential Issues:**
1. ✅ Multiple filters (6 filters applied) - might be too specific
2. ⚠️ Business name has comma and ampersand: "Brillo, Goddards & KMPL"
3. ⚠️ Month is "Jan" - database might have "January"
4. ⚠️ Very specific combination might not exist in 2023

**Recommended Fix:**
1. Clear all filters
2. Select ONLY: Year = 2023, Business = "Brillo, Goddards & KMPL"
3. Try generating report
4. If it works, add Brand = Goddards
5. Continue adding filters one by one

---

## 💡 Quick Fixes

### Fix 1: Clear Filters Button
```
Click "Clear Filters" → Generate report → Should work!
```

### Fix 2: Use Fewer Filters
```
Instead of 6 filters, use 2-3 maximum
```

### Fix 3: Let Dynamic Filters Guide You
```
Don't manually type or force selections
Use ONLY the options shown in updated dropdowns
```

### Fix 4: Try Different Report Types
```
Some reports work better with certain filters:
- Executive Summary: Works best with Year + Business
- Brand Analysis: Needs Year + Business + Brand
- YoY Comparison: Needs at least 2 years selected
```

---

## 🎓 Understanding Dynamic Filters

### How They Work:
1. You select Year = 2024
2. API fetches: "What businesses have data in 2024?"
3. Business dropdown shows ONLY those businesses
4. You select Business = Kinetica
5. API fetches: "What brands does Kinetica have in 2024?"
6. Brand dropdown shows ONLY Kinetica's brands

### Why "No Data Found"?
If you somehow bypass this system or select incompatible combinations, you'll get no data.

**Example of Bad Combination:**
- Year = 2023
- Brand = NewBrand2024 (which only exists in 2024)
- Result = NO DATA (NewBrand2024 doesn't exist in 2023)

---

## 🔧 Technical Details

### Backend Error:
```
ERROR - Error generating custom report: No data found for the selected filters
```

This means the MongoDB query returned 0 documents.

### Frontend Error:
```
AxiosError: Request failed with status code 500
```

This is shown to the user as:
```
"No data found for the selected filters. Please try different filter 
combinations or clear filters to see all data."
```

---

## ✅ Summary

### To Generate Reports Successfully:

1. **Start Simple**
   - Clear filters or use 1-2 filters only
   - Test with broad filters first

2. **Trust the Dynamic Filters**
   - Only select from updated dropdown options
   - Don't force specific combinations

3. **Use Clear Filters**
   - When in doubt, clear and start over
   - All data = always works

4. **Add Filters Gradually**
   - Year → Test → Add Business → Test → Add Brand → Test

5. **Watch for Error Messages**
   - "No data found" = try fewer/different filters
   - Duration is 5 seconds for these messages

---

## 🎉 Expected Behavior After Fixes

Now when you get "No data found" error:
- ✅ Clear, helpful error message (5 seconds)
- ✅ Tells you to try different filters
- ✅ Suggests clearing filters
- ✅ No confusing 500 error

Just follow the suggestions in the error message!
