# Requirements

This document lists the functional and non-functional requirements for a coursework web application that generates personalised city travel itineraries. The scope is suitable for a Flask API and simple frontend website. All requirements below must be met for acceptance.

---

## Functional requirements

1. API endpoints and basic contract
   - Expose GET /health that returns 200 OK and a small JSON status object (e.g., { "status": "ok" }).
   - Expose POST /api/itinerary that accepts a JSON body with:
     - destination (string, required)
     - days (integer, required, 1 <= days <= 14)
     - budget (string enum: "low" | "medium" | "high", required)
     - interests (array of strings, required, 1..6 items)
     - travel_style (string, optional, e.g., "relaxed", "active", "family")
   - Invalid input must return HTTP 400 with a JSON error object:
     - Example: { "error": "Invalid request", "details": { "days": "must be between 1 and 14" } }

2. Stable API response schema (POST /api/itinerary success)
   - Response HTTP 200 with JSON containing these top-level keys:
     - destination (string)
     - days (integer)
     - budget (string) — echo the input value
     - interests (array of strings)
     - travel_style (string)
     - overview (string)
     - itinerary (array) — length must equal the requested `days`
     - tips (array of strings)
   - Each itinerary item (one per day) must be an object with these keys:
     - day (integer, 1-based)
     - theme (string) — a short human-readable theme or planning focus for the day
     - morning (activity object or string)
     - afternoon (activity object or string)
     - evening (activity object or string)
     - budget_note (number) — numeric estimated cost for that day (currency units), adjusted by budget

3. Activity data
   - Activity fields visible to clients:
     - title (string)
     - description (string)
     - estimated_cost (number) — numeric, scaled by budget level
     - optional: duration_minutes (integer), location_hint (string), note (string)
   - The API may include additional keys for internal use, but all visible fields must be human-readable strings or numbers (never raw objects displayed as [object Object]).
   - If an activity is returned as a string (simple fallback), the frontend must render readable text; however the API should prefer structured activity objects.

4. Activity generation and repetition rules (stable generation contract)
   - Expand each interest into several concrete activities before building the itinerary. For example:
     - "food" expands to [ "breakfast: street-food lane", "local market tasting", "signature restaurant meal", "dessert & tea stop", "evening snack street" ].
     - "outdoor" expands to [ "lakefront walk", "city park reset", "scenic viewpoint", "garden/nature trail" ].
   - For a multi-day trip the itinerary must not visibly repeat the same small set of activities each day:
     - Rotate activities by using a deterministic scheme that depends on destination, day number, time slot (morning/afternoon/evening), and the user's interests.
     - Each day should have a different theme or planning focus where possible.
     - Generic fallbacks must be varied across time slots and days; do not return the same fallback text for morning every day.
   - The itinerary array length must equal the `days` input.

5. Budget handling
   - Input budget is an enum ("low", "medium", "high").
   - The API must convert budget level into numeric multipliers internally and return numeric estimated_cost and budget_note per day.
   - budget_note must be a numeric value (no "low/medium/high" strings).

6. Frontend rendering contract / stable DOM and functions
   - The generated frontend must include the following stable element IDs:
     - plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage
   - The frontend JavaScript must define the following stable functions (exact names required):
     - collectFormData()
     - validateFormData(formData)
     - setLoading(isLoading)
     - showError(message)
     - renderItinerary(responseJson)
     - renderDay(dayObject)
     - renderActivity(activityObject, timeSlot)
     - formatActivityText(activityObject)
   - The frontend must never display raw JS objects such as [object Object]. All activity fields must be formatted into readable text (use formatActivityText for this purpose).
   - The generated frontend must NOT create its own image preview area or attempt to fetch or render AI images. Image integration will be handled later by a separate frontend image contract agent. However, the frontend should provide a clear hook where an image preview could be inserted (e.g., a per-activity container with a stable ID pattern) but must leave it empty.

7. Image generation / AI integration (integration points only)
   - The API MAY optionally return image_prompts (array) or per-activity prompt text for later image generation, but must not include or embed images directly.
   - All image handling and rendering is out of scope for this coursework and will be performed by the frontend image contract agent. The app must not attempt to generate or preview images in the current release.

8. Error handling
   - All validation errors must return HTTP 400 with JSON error object.
   - Server errors should return HTTP 500 with JSON { "error": "Internal server error" }.
   - The frontend must surface validation error messages in formMessage or errorMessage elements.

---

## Non-functional requirements

1. Determinism and testability
   - Itinerary generation must be deterministic for the same inputs. If any randomness is used, it must be driven by a seed derived from input fields (e.g., hash of destination+days+budget+interests+travel_style).
   - Deterministic outputs are required so automated pytest checks can validate content, counts, and rotation rules.

2. Performance
   - Typical response time for POST /api/itinerary (for reasonable inputs, <=7 days) should be under 2 seconds on a modern student laptop. No long-running blocking tasks.
   - GET /health must respond in <100ms.

3. Reliability and correctness
   - The API must validate and sanitize inputs; reject malformed or out-of-range values with HTTP 400.
   - Maximum days must be enforced (e.g., 14 days) to keep generation deterministic and fast.

4. Maintainability and code quality
   - Code must be modular with clear separation: API handlers, itinerary generation logic, interest-expansion logic, cost calculation, and frontend rendering utilities.
   - Write clear docstrings and brief README showing how to run locally, run tests, and build Docker image.

5. Security
   - No server-side template injection or insecure use of user input in shell commands.
   - Escape or sanitize any user-provided strings before rendering into HTML templates.
   - Do not enable debug mode in production Docker image.

6. Accessibility and UX
   - The frontend form must be usable with keyboard navigation and have appropriate labels connected to the stable IDs.
   - Provide clear error messages.

7. Testing requirements
   - Unit tests (pytest) covering:
     - API contract tests for GET /health and POST /api/itinerary with valid and invalid inputs.
     - Schema validation for response (top-level keys, itinerary length equal to days, numeric costs).
     - Determinism tests: same input => same output.
     - Activity rotation tests: verify that repeated-day outputs are varied according to day/time slot.
     - Interest expansion tests: interests must expand into multiple concrete activities.
   - Frontend tests:
     - JavaScript unit tests (e.g., Jest) for utility functions: formatActivityText, validateFormData, renderActivity (or similarly testable functions).
     - Integration smoke test that submits the form to a running test server and checks resultsContainer receives readable text (no [object Object]).
   - CI must run all tests on each push/PR.

8. Continuous integration (CI)
   - Provide CI configuration (e.g., GitHub Actions) that:
     - Installs Python dependencies and JavaScript dev dependencies.
     - Runs linters (flake8 or pylint for Python; eslint for JS).
     - Runs all tests (pytest and npm test).
     - Builds a Docker image and optionally verifies it runs and serves /health.
   - CI must fail the build on lint/test failure.

9. Docker deployment
   - Provide a Dockerfile suitable for coursework deployment:
     - Multi-stage build recommended: builder + small runtime image.
     - Expose a configurable PORT via environment variable (default 8000).
     - Use a production-ready WSGI server (e.g., gunicorn) for the app in the container.
     - Container must respond to GET /health.
   - Provide docker-compose.yml for local development (optional) that maps a host port and passes env vars.
   - Docker image build must be reproducible for the same repo state.

10. Logging and observability
    - Log request start/end and key errors to stdout in a simple structured (JSON or key=value) format suitable for CI logs.
    - Do not log sensitive user data (e.g., no PII).

11. Documentation
    - README must include:
      - API contract (endpoint list and JSON schema).
      - How to run locally, run tests, run lint, and build Docker image.
      - How to run CI locally (if applicable).

---

## Acceptance criteria (short checklist)

- [ ] GET /health returns 200 JSON status.
- [ ] POST /api/itinerary accepts the required fields and returns the exact top-level keys: destination, days, budget, interests, travel_style, overview, itinerary, tips.
- [ ] itinerary array length equals days; each day contains day, theme, morning, afternoon, evening, budget_note.
- [ ] Activity titles/descriptions are human-readable strings; no [object Object] appears in frontend rendering.
- [ ] Estimated costs are numeric and adjusted by budget (low/medium/high mapping to multipliers).
- [ ] Activities are expanded from interests and rotated per day/time slot (deterministic).
- [ ] Invalid inputs produce HTTP 400 with JSON error object.
- [ ] Frontend contains the required stable IDs and implements the required stable function names.
- [ ] Frontend does not create or render an image preview area.
- [ ] Tests (pytest + JS unit tests) cover contracts and pass in CI.
- [ ] Dockerfile builds an image that serves /health and can be deployed.

---

## Example (compact) JSON success response schema

{
  "destination": "Example City",
  "days": 3,
  "budget": "medium",
  "interests": ["food","outdoor"],
  "travel_style": "relaxed",
  "overview": "A relaxed 3-day visit focused on food and outdoor highlights.",
  "itinerary": [
    {
      "day": 1,
      "theme": "Local Flavors",
      "morning": { "title": "Breakfast: street-food lane", "description": "Try local pastries...", "estimated_cost": 8.5 },
      "afternoon": { "title": "Market tasting", "description": "Sample cheese & spice stalls...", "estimated_cost": 15.0 },
      "evening": { "title": "Signature restaurant meal", "description": "Reserve ahead...", "estimated_cost": 45.0 },
      "budget_note": 68.5
    },
    ...
  ],
  "tips": ["Carry a refillable water bottle.", "Buy tickets in advance for the viewpoint."]
}

---

If you want, I can convert these requirements into:
- a machine-checkable JSON Schema for the API response,
- a checklist of pytest and frontend tests to implement,
- or a minimal README + Dockerfile template to jump-start the coursework.