1) Role: Budget backpacker (solo leisure traveler)
- Goal: Pack maximum local experiences into a short, affordable trip.
- Main concern: Clear, varied daily plans and realistic numeric cost estimates so budgeting is simple.
- Acceptance expectation: The itinerary must provide day-count-matching entries with morning/afternoon/evening slots, human-readable activity titles/descriptions, and numeric estimated costs (no low/medium/high strings); activities must not repeat the same generic fallback each day.

2) Role: Family trip planner (parent organizing a multi-day holiday)
- Goal: Create a kid-friendly, well-paced itinerary that balances activities and rest.
- Main concern: Readable day-by-day schedule, distinct daily themes, and practical tips (transport, meals, child accommodations).
- Acceptance expectation: Each day must include day, morning, afternoon, evening, and budget_note fields with clear text (no [object Object]) and varied activities so children don’t see the same three items repeated.

3) Role: Travel agent staff (small agency employee using the web app for clients)
- Goal: Quickly generate professional itineraries to present to clients and edit as needed.
- Main concern: Stable, deterministic API and frontend behavior for repeatable proposals and automated tests.
- Acceptance expectation: The system must expose /health and POST /api/itinerary accepting destination, days, budget, interests, travel_style, and return the required top-level fields (overview, itinerary, tips) with itinerary length equal to days and clear, printable day entries.

4) Role: Solo business traveler (short work trip with spare time)
- Goal: Fit efficient sightseeing and good food into limited free hours around meetings.
- Main concern: Precise timing (morning/afternoon/evening slots), concise activity descriptions, and quick visual references later.
- Acceptance expectation: The itinerary must provide distinct slots per day with human-readable activity text and numeric cost; image handling should be delegated—the frontend must not create its own image preview area so images can be integrated later by the image service.