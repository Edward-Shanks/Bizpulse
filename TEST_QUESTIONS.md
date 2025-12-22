# Comprehensive Test Questions for Multi-Dimensional Chatbot

This document contains 40 test questions covering all combinations of dimensions, metrics, and query types to validate the chatbot's functionality.

## Basic Single Dimension Queries

1. **What is the gross sales for Food business in 2024?**
   - Tests: Business filter, Year filter, Gross Sales metric

2. **Show me the profit for KOKA brand in Q1 2024.**
   - Tests: Brand filter, Quarter filter, Profit metric

3. **What are the total cases sold in Grocery channel for November 2025?**
   - Tests: Channel filter, Month filter, Cases metric

4. **Tell me the revenue for Baking category in 2023.**
   - Tests: Category filter, Year filter, Revenue metric

5. **What is the gross sales for Dunnes customer in Q2 2024?**
   - Tests: Customer filter, Quarter filter, Gross Sales metric

## Two-Dimension Combinations

6. **Compare Q1 gross sales for Food business in 2023 and 2024.**
   - Tests: Business + Year, Quarter, Gross Sales, Year-over-year comparison

7. **Show me profit for Food business and KOKA brand in 2024.**
   - Tests: Business + Brand, Profit metric

8. **What is the revenue for Food business and Grocery channel in Q1 2024?**
   - Tests: Business + Channel, Quarter, Revenue

9. **Compare gross sales for Food business and Baking category across years.**
   - Tests: Business + Category, Year-over-year comparison

10. **Tell me the cases sold for Food business and Dunnes customer in 2024.**
    - Tests: Business + Customer, Cases metric

11. **What is the profit margin for KOKA brand and Grocery channel in 2023?**
    - Tests: Brand + Channel, Margin metric

12. **Show me gross sales for Baking category and KOKA brand in Q2 2024.**
    - Tests: Category + Brand, Quarter, Gross Sales

## Three-Dimension Combinations

13. **Compare Q1 gross sales for Food business, KOKA brand, and Grocery channel in 2023 and 2024.**
    - Tests: Business + Brand + Channel, Quarter, Year comparison

14. **What is the profit for Food business, Baking category, and KOKA brand in 2024?**
    - Tests: Business + Category + Brand, Profit

15. **Show me revenue for Food business, Grocery channel, and Dunnes customer in Q1 2024.**
    - Tests: Business + Channel + Customer, Quarter, Revenue

16. **Compare gross sales for Food business, Baking category, and Grocery channel across years.**
    - Tests: Business + Category + Channel, Year-over-year

17. **Tell me the cases sold for Food business, KOKA brand, and Grocery channel in 2024.**
    - Tests: Business + Brand + Channel, Cases

18. **What is the profit margin for Food business, Baking category, and KOKA brand in Q2 2024?**
    - Tests: Business + Category + Brand, Quarter, Margin

## Four-Dimension Combinations

19. **Compare Q1 gross sales for Food business, Baking category, KOKA brand, and Grocery channel in 2023 and 2024.**
    - Tests: Business + Category + Brand + Channel, Quarter, Year comparison

20. **Show me profit for Food business, Baking category, KOKA brand, and Dunnes customer in 2024.**
    - Tests: Business + Category + Brand + Customer, Profit

21. **What is the revenue for Food business, Baking category, Grocery channel, and Dunnes customer in Q1 2024?**
    - Tests: Business + Category + Channel + Customer, Quarter, Revenue

22. **Compare gross sales for Food business, Baking category, KOKA brand, and Grocery channel across years.**
    - Tests: Business + Category + Brand + Channel, Year-over-year

## Five-Dimension Combinations

23. **Compare Q1 gross sales for Food business, Baking category, KOKA brand, Grocery channel, and Dunnes customer in 2023 and 2024.**
    - Tests: Business + Category + Brand + Channel + Customer, Quarter, Year comparison

24. **Show me profit for Food business, Baking category, Cooking chocolate sub-category, KOKA brand, and Grocery channel in 2024.**
    - Tests: Business + Category + Sub-Category + Brand + Channel, Profit

## Sub-Category Queries

25. **What is the gross sales for Baking category and Cooking chocolate sub-category in 2024?**
    - Tests: Category + Sub-Category, Gross Sales

26. **Compare Q1 profit for Food business, Baking category, and Cooking chocolate sub-category in 2023 and 2024.**
    - Tests: Business + Category + Sub-Category, Quarter, Year comparison

27. **Show me revenue for Baking category, Cooking chocolate sub-category, and KOKA brand in Q2 2024.**
    - Tests: Category + Sub-Category + Brand, Quarter, Revenue

## Advanced Metric Queries

28. **What is the price downs for Food business in 2024?**
    - Tests: Price Downs metric, Business filter

29. **Show me the permanent discount for KOKA brand in Q1 2024.**
    - Tests: Perm Disc metric, Brand filter, Quarter

30. **What is the group cost for Food business and Grocery channel in 2023?**
    - Tests: Group Cost metric, Business + Channel

31. **Tell me the LTA for Food business, Baking category, and KOKA brand in 2024.**
    - Tests: LTA metric, Business + Category + Brand

32. **What is the fGP for Food business, KOKA brand, and Grocery channel in Q1 2024?**
    - Tests: fGP metric, Business + Brand + Channel, Quarter

## Margin and Calculated Metrics

33. **What is the profit margin for Food business in 2024?**
    - Tests: Margin calculation, Business filter

34. **Compare profit margin for Food business and KOKA brand across years.**
    - Tests: Margin calculation, Business + Brand, Year comparison

35. **Show me the margin for Food business, Baking category, and Grocery channel in Q1 2024.**
    - Tests: Margin calculation, Business + Category + Channel, Quarter

## Complex Comparison Queries

36. **Compare Q1 gross sales for Food business and KOKA brand in 2023 and 2024.**
    - Tests: Business + Brand, Quarter, Year-by-year breakdown

37. **Compare Q1 gross sales for Food business and Baking category in 2023 and 2024.**
    - Tests: Business + Category, Quarter, Year-by-year breakdown

38. **Compare Q1 gross sales for Food business and Grocery channel in 2023 and 2024.**
    - Tests: Business + Channel, Quarter, Year-by-year breakdown

39. **Compare Q1 gross sales for Food business, KOKA brand, and Grocery channel in 2023 and 2024.**
    - Tests: Business + Brand + Channel, Quarter, Year-by-year breakdown

40. **Compare Q1 gross sales for Food business, Baking category, KOKA brand, and Grocery channel in 2023 and 2024.**
    - Tests: Business + Category + Brand + Channel, Quarter, Year-by-year breakdown

## Testing Checklist

For each question, verify:
- [ ] Correct dimension filters are applied (Business, Category, Sub-Category, Brand, Channel, Customer, Year, Quarter, Month)
- [ ] Correct metric is used (Gross Sales, Profit, Margin, Cases, Price Downs, Perm Disc, Group Cost, LTA, fGP)
- [ ] Multi-dimensional breakdown shows separate values for each dimension combination
- [ ] Year-over-year comparisons show separate values for each year
- [ ] Quarter queries correctly map to months (Q1 = Jan, Feb, Mar)
- [ ] Output format is correct (currency for sales, units for cases, percentage for margin)
- [ ] No "data not available" errors when data exists
- [ ] Hierarchical relationships are respected (Business→Category→Sub-Category→Brand, Channel→Customer)

## Expected Behavior

1. **Dimension Detection**: All mentioned dimensions should be detected and included in the breakdown
2. **Metric Extraction**: The correct metric should be identified and used in aggregations
3. **Multi-Dimensional Grouping**: When multiple dimensions are mentioned, the breakdown should group by all of them
4. **Year-by-Year Breakdown**: Comparison queries should show separate values for each year, not combined totals
5. **Quarter Mapping**: Q1/Q2/Q3/Q4 should correctly map to their respective months
6. **Output Formatting**: Metrics should be formatted correctly (€ for currency, units for cases, % for margin)

## Notes

- Replace "Food", "KOKA", "Baking", "Cooking chocolate", "Grocery", "Dunnes" with actual values from your database
- Adjust years (2023, 2024, 2025) based on available data
- Some metrics (Price Downs, Perm Disc, Group Cost, LTA, fGP) may not exist in all databases - verify field names match your schema
- Test with both abbreviated and full month names (Jan vs January, Nov vs November)
- Test with various phrasings (e.g., "sub-category" vs "subcategory" vs "sub category")

