# Requirements

This document defines functional and non-functional requirements for a coursework Flask API + website that generates personalised city travel itineraries for a small travel agency. Scope is intentionally limited to fit a coursework project while meeting the provided quality contract.

---

## Overview / Goals
- Allow users to submit destination, trip length, budget level, interests, and travel style and receive a clear day-by-day itinerary.
- Provide both a RESTful Flask API and a single-page website frontend that consumes the API.
- Ensure a stable, machine- and test-friendly contract (endpoints, fields, IDs, and function names).
- Keep the system deterministic enough for automated tests and Docker deployment.

---

## Functional Requirements

1. Endpoints and basic behavior
   - GET /health
     - Returns HTTP 200 with JSON: { "status": "ok" } when the app is healthy.
   - POST /api/itinerary
     - Accepts JSON request body containing:
       - destination (string)
       - days (integer, 1..14)
       - budget (string enum: "low", "medium", "high") — used to scale numeric cost estimates
       - interests (array of strings)
       - travel_style (string enum: e.g., "relaxed", "active", "family", "honeymoon")
     - On success returns HTTP 200 and a JSON response (see API response schema below).
     - On invalid input returns HTTP 400 and a JSON error object (see Error format).

2. API response schema (stable)
   - Top-level JSON object MUST include these keys:
     - destination (string)
     - days (integer)
     - budget (string — echo of request)
     - interests (array of strings — echo of request or normalized)
     - travel_style (string)
     - overview (string) — a short, human-readable summary of the trip plan
     - itinerary (array) — length must equal days; see Day object below
     - tips (array of strings) — general travel tips for this destination/trip
   - Day object (each element of itinerary) MUST include:
     - day (integer, 1-based)
     - morning (activity or activity object)
     - afternoon (activity or activity object)
     - evening (activity or activity object)
     - budget_note (string) — short, human-readable note about that day's costs
   - Activity representation:
     - Activities may be either:
       - string (a human-readable activity title/summary), or
       - object/dictionary with readable fields:
         - title (string)
         - description (string)
         - estimated_cost (numeric, e.g., 12.50) — numeric value adjusted by request budget
         - duration_minutes (optional integer)
         - location_hint (optional string)
     - The response MUST NOT use encoded values that will render in the frontend as "[object Object]" verbatim; fields should be plain strings/numbers so frontend can render human-readable text.
   - Additional rules:
     - itinerary array length must equal days.
     - Each day should have a different theme or planning focus where possible.
     - For repeated interests, the server must expand each interest into several concrete activities before filling daily slots, to avoid visible repetition across days (see "Interest expansion" below).
     - Activities should rotate across morning/afternoon/evening so the same generic fallback does not appear in the same time slot each day; rotation may depend on destination, day number, time slot and interests (deterministic).
     - Estimated costs MUST be numeric values, not strings like "low/medium/high".
     - The API should return deterministic results for the same normalized input (see Non-functional: Determinism).

3. Request validation rules
   - destination: non-empty string, maximum length (e.g., 100 chars).
   - days: integer between 1 and 14 (inclusive).
   - budget: one of allowed values ("low", "medium", "high").
   - interests: non-empty array of strings, each trimmed and validated against allowed interest categories where possible (for coursework a free-text list is acceptable but must not be empty).
   - travel_style: one of allowed values.
   - If validation fails return HTTP 400 with a JSON error object (see Error format).

4. Interest expansion and activity selection (business logic)
   - Each declared interest must be expanded server-side into several concrete activities (examples provided in the quality contract: e.g., "food" => breakfast street-food lane, local market tasting, signature restaurant meal, dessert and tea stop, evening snack street).
   - The pool of concrete activities used to build multi-day itineraries must be large enough to avoid obvious repetition (i.e., do not simply reuse the same three items each day).
   - Assignment of activities to morning/afternoon/evening should rotate deterministically across days using a stable algorithm that can be seeded by normalized inputs (destination + days + budget + interests + travel_style).
   - Each day must have a distinct theme or focus if possible (e.g., "historic centre", "food & markets", "parks & viewpoints").

5. Frontend rendering requirements (contract)
   - The generated website must provide a form with stable element IDs:
     - plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage
   - Frontend must expose or implement these stable functions (global or attached to a predictable module):
     - collectFormData — reads form fields and returns a JSON-ready object matching the API request shape
     - validateFormData — returns { valid: boolean, errors: [...] } and enforces same validation rules as server
     - setLoading — toggles a loading state in the UI
     - showError — displays error messages in errorMessage element
     - renderItinerary — given the API JSON response, populates resultsContainer and daysContainer
     - renderDay — renders a single day view and appends to daysContainer
     - renderActivity — given an activity (string or object) returns a human-readable DOM/text fragment
     - formatActivityText — returns plain string for display (never returns [object Object] or raw JSON)
   - The frontend must never create its own image preview area; image integration is handled later by a dedicated frontend image contract agent. The UI should, however, expose stable hooks (e.g., data-attributes or element IDs) where an image agent could later attach previews (but must not show a preview by default).

6. Error format (400)
   - When rejecting bad input, return HTTP 400 and JSON:
     - { "error": { "message": "<human-readable>", "code": "<machine-code>", "fields": { "<field>": "<reason>" } } }
   - Examples of error code values: invalid_input, missing_field, out_of_range.

7. Health and observability
   - GET /health must be implemented and return 200 JSON for container health checks.

---

## Non-Functional Requirements

1. Determinism and repeatability
   - For the same normalized request payload the API must return the same itinerary. Any randomization must be seeded deterministically from the normalized input (e.g., hash of inputs).
   - Determinism is required so automated pytest checks can validate outputs.

2. Performance
   - Typical response time target: < 500 ms for simple itinerary generation on student-grade hardware. (This is a guideline for implementation; CI should run tests within reasonable timeouts.)
   - The API must respond within reasonable timeouts; the frontend should show a loading indicator via setLoading if request takes noticeable time.

3. Security & input safety
   - Validate and sanitize all inputs to avoid injection in any exported strings.
   - Do not embed raw HTML from inputs into responses without escaping.
   - No secrets should be hard-coded in source code; use environment variables for config in Docker.

4. Usability & accessibility
   - Form must be usable with keyboard controls and basic screen reader support (semantic labels).
   - All activity titles/descriptions must be human-readable plain strings.

5. Testability
   - Provide unit tests (pytest) for:
     - POST /api/itinerary validation behavior (400 cases)
     - POST /api/itinerary success response schema and content rules (days length, numeric costs, no repetition, interest expansion)
     - GET /health
     - Frontend contract existence tests: presence of stable IDs and stable functions (can be validated by parsing generated HTML/JS).
   - Tests must be automated and runnable in CI.

6. Logging and errors
   - Log high-level errors and request summaries (do not log PII).
   - On server-side validation failure, include field-level hints in error response.

7. Maintainability
   - Code should be modular with clear separation between:
     - request validation
     - interest expansion / activity generation logic
     - itinerary assembly (day theming/rotation)
     - API layer and frontend static assets
   - Document any deterministic seeding algorithm.

8. CI/CD
   - Provide a CI pipeline (e.g., GitHub Actions) that:
     - Runs linters (e.g., flake8 or pylint) and unit tests (pytest).
     - Builds the Docker image and ensures it runs basic health check.
     - Optionally runs simple frontend checks (presence of IDs/functions).
   - CI must fail if tests or linting fail.

9. Docker deployment
   - Provide a Dockerfile to build and run the Flask app (including static frontend).
   - Container must:
     - Expose the app on port 5000 (configurable via env var).
     - Support a health check endpoint (/health) for container orchestration.
   - Provide a simple docker-compose (optional) or run instructions.
   - The Docker image must be deterministic with no variable build-time secrets.

10. AI image generation integration (scoped)
    - The core coursework must NOT implement actual image generation or show image previews in the frontend.
    - The API must optionally include image prompt strings (not base64 image data) to allow a later image agent to generate visuals. Example optional per-activity field:
      - image_prompt (string) — a concise prompt describing the activity/location suitable for later AI image generation.
    - The frontend must NOT display any images by default nor implement a preview area. It may include empty, well-documented data-attributes or element placeholders where a separate image agent may later attach images.
    - Any image generation responsibilities (callouts to an AI service) must be implemented in a separate component or later phase — not in the core Flask API/website for this coursework.

---

## Acceptance Criteria (tests / examples)
- API endpoints:
  - GET /health returns 200 and JSON { "status": "ok" }.
  - POST /api/itinerary with valid payload returns 200 and JSON containing the required top-level keys.
  - For input with days = N, itinerary array length == N.
  - Each itinerary day object includes day, morning, afternoon, evening, budget_note.
  - All activity estimated_cost fields are numeric (float/int) if present.
  - No activity titles/descriptions or rendered frontend text equals "[object Object]".
  - Repeated interests (e.g., ["food", "food"]) are expanded into multiple concrete activities so the day-to-day plan is varied.
  - Invalid or missing keys produce HTTP 400 with the prescribed error object.

- Frontend contract:
  - Generated HTML includes plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage element IDs.
  - The frontend code base exposes the functions: collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
  - The frontend does not render an image preview area.

- CI and Docker:
  - Provided GitHub Actions workflow runs tests and builds Docker image successfully.
  - Docker image starts and /health returns 200.

---

## Implementation notes and constraints (for students)
- Seed deterministically: derive a numeric seed by hashing a normalized JSON string of the request (sort keys, trim interest strings), and use that seed for any pseudo-random ordering or selection to ensure repeatability.
- Interest expansion: maintain a small predefined mapping from common interest keywords to a list of concrete activities (food, outdoor, history, shopping, nightlife, culture, family, relaxation). Expand unknown interests by programmatic templates (e.g., "<interest> experience - local spot", "<interest> workshop", "<interest> walking route") so activities remain varied.
- Costs: define base numeric cost tiers for budget levels and multiply item base_cost by a budget factor (e.g., low=0.7, medium=1.0, high=1.4). Round to 2 decimals.
- Rotation: assign activity candidates into morning/afternoon/evening by cycling or by deterministic shuffle per day.
- Frontend rendering: when renderActivity receives an activity object, use title + " — " + description + (cost if present). Ensure all values are coerced to strings and escaped.

---

If you want, I can also produce:
- A concise example request and response JSON that conform to the schema.
- A minimal pytest testfile that asserts the main acceptance criteria.
- A sample mapping of interest expansions (food/outdoor/history -> concrete activities).