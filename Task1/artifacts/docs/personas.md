1) Role: Emily — Solo Sightseer
- Goal: Maximise sightseeing in a short city break with a clear, easy-to-follow plan.
- Main concern: Confusing schedules or technical output (e.g., [object Object]) that make the itinerary unusable on the go.
- Acceptance expectation: The app returns a clear day-by-day itinerary whose length equals the requested days, with distinct morning/afternoon/evening human-readable activity titles/descriptions (no raw objects).

2) Role: Javier — Family Vacation Planner
- Goal: Create a multi-day, kid-friendly itinerary with variety so each day feels fresh.
- Main concern: Repeating the same few activities across days or inappropriate pacing for children.
- Acceptance expectation: Interests are expanded into multiple concrete activities and each day has a different theme so activities don’t repeat across days (readable strings, not generic fallbacks).

3) Role: Priya — Budget Backpacker
- Goal: See as much as possible on a tight budget while avoiding unexpected costs.
- Main concern: Vague cost labels that don’t translate into planning decisions.
- Acceptance expectation: Each day includes a numeric budget_note and activity estimated costs adjusted by the selected budget level so total daily affordability is clear.

4) Role: Ahmed — Travel Agent / Operator
- Goal: Quickly generate deterministic, shareable itineraries for clients and later add visual assets.
- Main concern: Unstable APIs/frontends or premature image handling that break automation or tests.
- Acceptance expectation: The system follows the stable contract (GET /health, POST /api/itinerary with required request/response fields), uses the specified stable frontend IDs/functions, produces deterministic output for automated checks, and the frontend does not create its own image preview area (image integration handled separately).