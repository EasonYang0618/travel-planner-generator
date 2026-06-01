- Role: Solo budget traveler (backpacker)
  - Goal: Maximise daily experiences in a new city on a shoestring budget.
  - Main concern: Hidden or vague costs and repetitive, generic suggestions that waste time.
  - Acceptance expectation: Receives a clear day-by-day itinerary with days equal to the requested length, numeric estimated costs adjusted for a low budget, no repeated fallback activities, and human-readable activity titles/descriptions.

- Role: Family trip planner (parent)
  - Goal: Build a kid-friendly, easy-to-follow multi-day schedule that balances sights and downtime.
  - Main concern: Confusing output or raw objects that are hard to read for non-technical family members.
  - Acceptance expectation: Each day shows distinct morning/afternoon/evening entries and a budget_note, with readable strings (no [object Object]) so the family can follow the plan easily; image generation will be handled later (no image previews in the frontend).

- Role: Luxury traveller
  - Goal: Curated, high-quality experiences and dining each day with clear distinctions between themes.
  - Main concern: Repetition and low-detail activity descriptions that don’t justify the higher spend.
  - Acceptance expectation: Multi-day itinerary where each day has a different theme, activities expanded from interests into varied concrete options, and activity descriptions are rich and human-readable; if visual assets are needed later, the itinerary includes image metadata/placeholders but the frontend does not render image previews.

- Role: Travel agency staff (itinerary generator)
  - Goal: Quickly generate deterministic, client-ready itineraries via the web app/API for multiple clients.
  - Main concern: Unstable API/formatting that breaks automation or frontend rendering.
  - Acceptance expectation: API and frontend outputs conform to the quality contract (POST /api/itinerary returns required top-level fields, itinerary length equals days, rotating morning/afternoon/evening activities, numeric costs, stable IDs/functions), enabling reliable automated checks and downstream image integration.