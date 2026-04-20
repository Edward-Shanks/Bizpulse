# How to verify which database answered the chatbot

## Two different flows

| Endpoint | Data source | Used by |
|----------|-------------|--------|
| **POST /api/insights/chat** | **MongoDB Atlas** (business_data) | View Insights chat (AIAssistant, InsightModal, AIInsightModal) |
| **POST /api/ai/chatbot/chat** | **ClickHouse** (Mac Studio, sales_analytics) | AI Chatbot with RBAC/cache (separate UI or API calls) |

The **current UI** (View Insights chat) calls `/api/insights/chat`, so answers are from **MongoDB**. To get answers from **ClickHouse**, call **POST /api/ai/chatbot/chat** (e.g. from a different screen or after wiring the frontend to this endpoint).

## Logs to look for

- **MongoDB path:** `DATA_SOURCE=MongoDB` and `response_ms=...` in backend logs when using View Insights chat.
- **ClickHouse path:** `DATA_SOURCE=ClickHouse` and `query_ms=...` / `response_ms=...` when using the AI chatbot endpoint.

Response payloads now include:
- **Insights chat:** `data.data_source` = `"MongoDB"`, `data.response_ms` = number.
- **AI chatbot:** `data_source` = `"ClickHouse"`, `response_ms` = number.

## Testing ClickHouse AI chatbot from PowerShell

The app runs from **server.py**; the route is **POST /api/ai/chatbot/chat**. Use **Invoke-RestMethod** (PowerShell’s `curl` is an alias and uses different syntax):

```powershell
Invoke-RestMethod -Method POST "http://localhost:8000/api/ai/chatbot/chat" `
  -Headers @{
    "Content-Type"="application/json"
    "Authorization"="Bearer YOUR_JWT_TOKEN"
  } `
  -Body '{"question":"Show revenue for Food business last 6 months"}'
```

Replace `YOUR_JWT_TOKEN` with your actual JWT (e.g. from login response). If you get `Not Found`, ensure the backend was restarted after registering the v1 router in server.py.

## Bug fixes applied

- `data_context.py`: Removed redundant `import re` inside the function that caused "cannot access local variable 're' where it is not associated with a value". The module already imports `re` at the top.

## Q1 year-over-year and charts (ClickHouse chatbot)

- **Partial years:** When the user asks for "Q1 2022, 2023, 2024" and 2022 has no data, the chatbot now shows 2023 and 2024 and states that 2022 has no data (prompt rule + optional context when data is empty).
- **Intent:** For multi-year/Q1 comparisons, intent uses `time_range.type = "lifetime"` and `filters.year` + `filters.quarter` so the query uses only year/quarter filters; default time filter is not applied. Fallback parser sets lifetime when both year(s) and quarter are present.
- **Default time filter:** `clickhouse_client` skips adding the default time filter when the query contains `quarter IN (` (in addition to `year IN (`).
- **Charts/tables:** The ClickHouse chatbot response now includes `pivot_table`: rows are mapped to frontend shape (Year, Revenue, Gross_Profit, Cases, Margin_%) so the same chart/table component as the live insights chat can render.

## "Compare brand X with other brands" (match live behaviour)

- **Live:** Removes Brand filter so the pivot shows all brands (top N); the LLM compares the mentioned brand with others.
- **Local (ClickHouse):** Intent and normalization now treat "compare brand X with other brands" (and "X vs other brands", "compare X to other brands", same for business/category) as: **do not filter by that entity**. So `filters.brand` is set to `[]`, `dimensions` includes `brand`, and `limit` is 20 or 25. The query returns all brands (subject to RBAC); the LLM gets the full list and can compare Bonne Maman (or the mentioned brand) with others.
- **Intent prompt rule 12:** Instructs the LLM to leave `filters.brand` empty for compare-with-other-brands questions.
- **Normalization:** After parsing, if the question contains phrases like "with other brands", "vs other brands", etc., we clear the corresponding entity filter and set dimension + limit.
- **Fallback intent:** Default intent is passed through `_normalize_intent(question)` so the same compare-with-others logic applies when the LLM fails.

## "Compare brand A and B" (two or more named brands)

- **Live:** For "Compare brand Killeen and Koka brand" the live chatbot shows **all** (or top) brands and the narrative compares Killeen vs Koka in context—it does not filter to only those two.
- **Local:** We now distinguish two cases:
  - **"Compare X with other brands"** (e.g. "Compare Bonne Maman with other brands"): clear `filters.brand`, dimensions = ["brand"], limit = 20 → query returns all brands; answer compares the named one to others.
  - **"Compare brand A, B, C and D"** (e.g. "compare brand KOKA, Green Aware, Kinetica and Powerforce"): do **not** clear the filter. Parse brand names from the question via `_parse_multiple_brands_from_question()` and set `filters.brand = [A, B, C, D]` so the query returns only those brands and the answer focuses on how those four are performing. Typos like "Poweforce" are normalized to "Powerforce".
- **"Compare brand A and B"** (e.g. "compare brand Killeen and koka brand"): Parser now strips trailing " brand"/" brands" from each token so "koka brand" → "Koka" (matches DB). Normalization always runs the parser for compare-two-brands questions; if 2+ brands are parsed (e.g. Killeen, Koka), `filters.brand` is set to that cleaned list so the query returns both rows. This fixes the bug where only Killeen was returned because "Koka Brand" did not match the DB value "Koka".
- **"Compare A, B and C brands"** and **"Compare Q2 2023 revenue of A, B and C brands"**: Parser now supports (1) "compare brand X, Y and Z", (2) "compare X, Y and Z brands" (list then "brands" at end), and (3) "compare Q2 2023 revenue of X, Y and Z brands". For (2) and (3), a second regex captures the segment before " brands"; stop words (Q2, 2023, revenue, of, etc.) are stripped from each part so only entity names remain. **"Calli Calli"** is normalized to **"Cali Cali"** (DB value). Same logic is used for **business** and **category** (e.g. "compare business Food and Beverage", "compare category Snacks and Drinks") via `_parse_multiple_entities_from_question(question, word_pattern, strip_suffix, normalizations)`.
- **"Tell me all three brands Q2 2023 revenue of X, Y and Z"** (no "compare"): So that all requested brands are returned (e.g. Cali Cali, Bonne Maman, Green Aware), `_parse_brands_from_revenue_phrase(question)` extracts the brand list from "revenue of X, Y and Z" or "revenue for X, Y and Z" (or "revenue for brands X, Y and Z"). Normalization runs this when the question mentions "brand"/"brands" and we don't already have 2+ brands from the compare block, then sets `filters.brand` and `dimensions` so the query returns one row per requested brand.

## Response cache keyed by question (fix wrong cached answer)

- **Issue:** Two different questions ("compare KOKA, Green Aware, Kinetica and Powerforce" vs "compare Bonne Maman with other brands") can produce the same intent (dimensions=brand, filters.brand=[]) and same result (top 20 brands), so the response cache was returning the **first** question’s answer (e.g. Bonne Maman) for the **second** question.
- **Fix:** Response cache key now includes **question_hash** (hash of normalized question text). Cache lookup/set use `(tenant_id, permissions_hash, intent_hash, result_hash, question_hash)`. Different questions get different cached explanations even when intent and result are identical. Implemented in `ai_cache_service.get_cached_response` / `set_cached_response` and `ai_service.process_question`.

## Question clarification ("Did you mean:") — LLM understands any question

- **Goal:** The chatbot must handle **all kinds of questions** from thousands of users (business or not). It should **understand** whether a question is about business data we can answer; if not, return clarification with **only business-related** suggested questions.
- **Local (ClickHouse):** In `ai_clarity_service.py`, the **LLM is the primary decider**. One prompt asks: "Is this question about business data (revenue, profit, brands, businesses, categories, etc.) that this chatbot can answer?" Reply JSON: `is_business_question` true/false and `suggested_questions` (if false, 5–6 business-only questions). The prompt explicitly states that **stock market, share prices, trading, equity markets** are NOT our business data — we only answer about the company's own revenue, profit, brands, categories. **Fast paths** (no LLM): (1) obvious business patterns, (2) very short greetings, (3) **stock market / financial markets** — if the question contains phrases like "stock market", "share price", "trading", "nasdaq", "sensex", "crypto", we immediately return clarification with business-only suggestions so we never answer about the stock market. **Safeguard:** If a query returns no data and the question contains off-topic terms (e.g. stock, war, incident), the AI service returns a short refusal and business-only suggestions.

## Response speed (ClickHouse chatbot)

- **Bottleneck:** ClickHouse + data cache are fast (~100–200 ms). The slow part is the **LLM** (Ollama qwen2.5:32b) generating the explanation (~50+ seconds).
- **Faster LLM settings:** In `ai_response_service.py`, explanation uses `temperature=0.5` and `max_tokens=1000` (was 0.7 and 2000) so the model finishes sooner.
- **Response cache:** The full explanation text is cached in MongoDB collection `ai_response_cache` by `(tenant_id, permissions_hash, intent_hash, result_hash, question_hash)`. When the **same question** is asked again and the result data is unchanged, the cached explanation is returned and the **LLM is skipped** (near-instant response). Different questions never share a cached answer. TTL 24 hours.

Do not delete this folder.
