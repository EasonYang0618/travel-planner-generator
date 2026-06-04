- Role: Solo leisure traveller (young professional)
  - Goal: Quickly generate a personalised, easy-to-follow day-by-day plan for a short city trip.
  - Main concern: Itineraries that repeat the same vague activities or show costs as non‑numeric labels.
  - Acceptance expectation: Each day must present distinct morning/afternoon/evening human‑readable activities (no [object Object] text), numeric estimated costs, and no repeated generic fallback items.

- Role: Parent planning a family holiday
  - Goal: Create a kid‑friendly, manageable multi‑day itinerary with varied themes each day.
  - Main concern: Overcrowded or late schedules and unclear activity descriptions that aren’t suitable for children.
  - Acceptance expectation: Every day includes day/morning/afternoon/evening and a budget_note, with varied, family‑appropriate activity titles and descriptions; the frontend must not generate its own image previews (image integration happens later).

- Role: Budget backpacker
  - Goal: Maximise experience on a tight budget by prioritising low‑cost local activities.
  - Main concern: Ambiguous cost guidance and hidden expenses.
  - Acceptance expectation: Estimated costs are numeric and scaled by budget level (so I can compare days); activity lists should rotate and expand interests so the trip doesn’t reuse the same three items.

- Role: Travel agency operator (staff)
  - Goal: Produce deterministic itineraries via the API/website to include in client proposals and reuse across clients.
  - Main concern: Inconsistent API responses, missing top‑level fields, or UI rendering that breaks automated workflows.
  - Acceptance expectation: POST /api/itinerary returns the required top‑level fields (destination, days, budget, interests, travel_style, overview, itinerary, tips), itinerary length equals days, activity texts are human‑readable, and the frontend exposes stable IDs/functions for integration while leaving image previewing to the image contract agent.