# Live AI Chatbot: Prompt and Flow (Insights Service)

This document summarizes how the **live** View Insights chatbot (`/api/insights/chat`, MongoDB + `insights_service.py`) is designed to answer business questions correctly.

## Data flow (live)

1. **Request**: `message`, `chart_title`, `context` (filters from UI).
2. **Query building**: `build_mongodb_query_from_context(context)` + `parse_query_from_natural_language(message)` → merged filters. For "compare brand X with other brands" or "compare brand A and B", **Brand filter is removed** so the query returns all brands.
3. **Data context**: `get_comprehensive_data_context(query, message, db, ...)` → long formatted string (aggregations, totals, breakdowns) from MongoDB.
4. **Pivot table**: `_generate_pivot_table(...)` → list of dicts (e.g. Brand, Revenue, Gross_Profit, Cases, Margin_%) for year/category/brand/customer. Used for charts and **injected into the LLM prompt** so the model sees the exact list.
5. **System message** (very long): quarterly rules, data-only restriction, handling unavailable data, no technical terms, **must provide (1) Key insights (2) What numbers mean (3) 3–5 Recommendations with why/how (4) Risks or opportunities (5) Next steps**, exact numbers, question independence, etc.
6. **User prompt**: Chart context, **QUERY INTENT** (quarter, business, years, metric), **PIVOT TABLE NOTE** ("CRITICAL: PIVOT TABLE DATA - YOU MUST USE THIS DATA", top 10 rows formatted, "START your response by listing the EXACT brands/entities..."), then **BUSINESS DATA** (full data_context), then instructions to only use this data and handle incomplete data, then "User Question: {message}".
7. **LLM**: `query_perplexity(user_prompt, conversation_history, custom_system_message=system_context)`.

## Why the live chatbot answers “any” question well

- **Single source of truth**: The model is given one clear “Business Data” / pivot block and told to use **only** that. No mixing with external knowledge.
- **Strong “list first” rule**: The prompt says: start by listing the **exact** entities from the data (names + Revenue, Profit, margin, Cases). That forces the model to ground the answer in the actual rows.
- **No “data not available” when data exists**: Multiple rules say: if the data context shows any aggregated values or rows, do **not** say “data not available”; treat the numbers as authoritative.
- **Comprehensive structure**: System message requires (1) Key insights, (2) What these numbers mean, (3) 3–5 Recommendations with why/how, (4) Risks/opportunities, (5) Next steps. So answers are always analytical, not just a list.
- **Query intent in prompt**: Quarter, business, years, metric are summarized so the model knows what the user asked for (e.g. Q1, Food, 2023–2024).
- **Question independence**: Each question is treated as standalone; “all brands” is not filtered by a previous “top 10 brands” question.
- **Comparison handling**: For “compare X and Y” or “X with other brands”, the **Brand** (or Business/Category) filter is removed so the backend returns the full list; the model then compares the named entities in that list.

## Local (ClickHouse) chatbot alignment

The local chatbot (`/api/ai/chatbot/chat`) uses ClickHouse + intent → query → result → LLM. To align with the live behavior:

- **Intent/normalization**: “Compare brand A and B” and “compare X with other brands” clear the brand filter and return all brands (done in `ai_intent_service.py`).
- **Response prompt**: Mirrors the live “CRITICAL INSTRUCTIONS”: (1) Start by listing exact entities from the data with Revenue, Profit (margin %), Cases; (2) Key Insights; (3) Performance Analysis; (4) Recommendations; (5) Next Steps. Use only provided data; never say “data not available” when rows are provided (`ai_response_service.py`).
- **System message**: Data-only, exact numbers, no “data not available” when data is provided, required sections, business language only, no technical terms.

See `backend/app/services/ai/ai_response_service.py` for the local prompt and system message.

Do not delete this folder.
