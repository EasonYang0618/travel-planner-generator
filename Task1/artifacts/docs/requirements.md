# Requirements

This document lists the functional and non-functional requirements for the coursework web application (Flask API + frontend) that generates personalised city travel itineraries. It is scoped for a coursework project and includes the stable "quality contract" requirements so automated tests and Docker deployment succeed.

---

## Functional requirements

### 1. API surface (required)
- Expose GET /health
  - Returns 200 OK and a small JSON object indicating service health (e.g., { "status": "ok" }).
- Expose POST /api/itinerary
  - Accepts a JSON body with these fields (all names exact and required unless specified):
    - destination (string)
    - days (integer, >= 1)
    - budget (string or enumerated value accepted by the API such as "low", "medium", "high")
    - interests (array of strings)
    - travel_style (string; e.g., "relaxed", "active", "family")
  - On success returns 200 OK with a JSON object (stable schema) — see Response schema below.
  - On invalid input returns HTTP 400 with a JSON error object:
    - { "error": "<human-readable message>", "details": { ... } } (details optional)

### 2. Stable response schema (contract)
- Top-level fields (all required on success):
  - destination (string)
  - days (integer)
  - budget (string as accepted input)
  - interests (array of strings)
  - travel_style (string)
  - overview (string): a short human-readable overview of the trip
  - itinerary (array): length must equal `days`; each item is a day object (see Day schema)
  - tips (array of strings): general travel tips for the destination and selected travel_style
- Day schema (each day object must contain):
  - day (integer, 1-based)
  - morning (activity object or string) — see Activity rules below
  - afternoon (activity object or string)
  - evening (activity object or string)
  - budget_note (string) — numeric insight derived from estimated costs and budget level
- Activity object rules:
  - Titles and descriptions must be human-readable strings; never return raw dictionaries displayed as UI objects or "[object Object]".
  - Estimated costs must be numeric values (float or integer) adjusted according to `budget` (not strings such as "low/medium/high").
  - Activity objects may contain fields such as:
    - title (string)
    - description (string)
    - estimated_cost (number)
    - duration_minutes (integer, optional)
    - location_hint (string, optional)
    - image_prompt (string, optional): a short prompt for an external image-generator to create an image (the backend does NOT produce images).
  - The frontend must be able to render activity objects into readable text using the stable rendering functions (see Frontend requirements).

### 3. Itinerary generation rules / content contract
- The itinerary array length must equal the provided `days`.
- Activities must not repeat the same generic fallback each day. The generator must rotate morning/afternoon/evening activity choices using the combination of:
  - destination, day number, time slot, and user interests
- For each interest, the system must expand that interest into a list of several concrete activities before building the itinerary so multi-day trips do not visibly repeat the same few activities. Example expansions (must be followed where applicable):
  - interest "food" -> e.g. breakfast street-food lane, local market tasting, signature restaurant meal, dessert & tea stop, evening snack street
  - interest "outdoor" -> e.g. lakefront walk, city park reset, scenic viewpoint, garden or nature trail
- Each day should have a different theme or planning focus where possible (e.g., "historical day", "food day", "relaxation day").
- Activity titles/descriptions must be human-readable strings (no raw dicts).
- The generator must try to diversify activities across days and time slots.
- Provide numeric estimated_costs adjusted up/down by budget level (e.g., low -> lower numeric costs; high -> higher numeric costs).

### 4. Determinism and testability
- The itinerary generation must be deterministic given the same input and a fixed seed.
  - The service should allow (for tests) seeding the generator via an environment variable or header (e.g., X-GENERATOR-SEED) or use a stable internal seed for coursework automation.
- Any randomness must be controlled so pytest-based checks and automated grading can repeat runs and compare results reliably.
- The service should avoid making live network calls in the generation path during automated tests (external services must be mocked).

### 5. Frontend requirements (website)
- The frontend must provide a form and results area to call the API and render itineraries.
- Required stable DOM element IDs:
  - plannerForm
  - destination
  - days
  - budget
  - interests
  - travel_style
  - resultsContainer
  - daysContainer
  - formMessage
  - errorMessage
- Required stable frontend functions (names and responsibilities):
  - collectFormData(): gather and return a JS object of the form input values matching the API fields
  - validateFormData(data): validate client-side and return { valid: boolean, errors: [...] } (client-side validation only; backend still authoritatively validates)
  - setLoading(isLoading): toggle loading UI state
  - showError(message): display errors inside errorMessage
  - renderItinerary(itineraryResponse): render the returned itinerary into resultsContainer
  - renderDay(dayObject): render a single day into daysContainer with morning/afternoon/evening/budget_note
  - renderActivity(activity): render a single activity as readable text (title, description, numeric cost, duration)
  - formatActivityText(activity): helper to format activity data into safe, human-readable text
- Rendering rules:
  - The frontend must never display raw object serialization (no "[object Object]").
  - Activities may be objects, but renderActivity must extract and display human-readable fields (title, description, estimated_cost). Null/undefined fields should be handled gracefully.
  - The frontend must NOT create its own image preview area. Image integration/preview will be handled by a separate frontend image contract agent later. The frontend should, however, display non-modal placeholders or explicit "Image available" indicators only if image_prompt (or image metadata) is present; it must not attempt to fetch or render images itself in this coursework scope.
- The frontend must call POST /api/itinerary and handle success and 400 error responses with proper UI messages.

### 6. AI image generation integration (limited coursework scope)
- The backend may produce structured image metadata per activity but must NOT produce images.
  - Provide an optional activity.image_prompt (string) that gives a concise prompt for an external image-generation agent to use later.
- The API must not return binary image data.
- The frontend must not generate or preview images; integration is deferred to the image contract agent.
- If image_prompt is present, it should be a short, clear English sentence suitable for automated image agents.

### 7. Error handling
- Invalid request payloads result in HTTP 400 and a JSON error object:
  - { "error": "Invalid input", "details": { "field": "message" } }
- Unexpected server errors return HTTP 500 with a generic JSON error message but must not leak internal stack traces in production mode.
- GET /health must always return 200 if service is reachable.

### 8. Test hooks and observability for coursework grading
- Provide an environment-variable-controlled deterministic mode or seed (for automated tests) as described above.
- Include a test endpoint or header-based toggle only used in test/development (if added, document it).
- Log sufficient information for debugging (request ID, sanitized input values, errors) but avoid logging sensitive PII.

---

## Non-functional requirements

### 1. Determinism and reproducibility
- Given the same input and seed, outputs must be stable across runs.
- Production and CI runs should behave deterministically for automated checks; randomness must be seedable and documented.

### 2. Performance
- Typical itinerary generation for up to 14 days should respond within 2 seconds on coursework infrastructure (single-container Docker on a laptop); timeouts and graceful degradation if heavy processing is used.
- The API must gracefully handle concurrent requests expected for coursework load (tens of requests/minute).

### 3. Reliability and correctness
- API must return correct HTTP status codes and JSON content types.
- The itinerary array length must strictly match the `days` integer in the request.
- Activity costs must be numeric and consistent with the budget parameter.

### 4. Security
- Validate and sanitize inputs server-side.
- Disable any unsafe template rendering of user input.
- Do not include secrets (API keys, credentials) in the repo; use environment variables for configuration.
- Implement basic rate-limiting or document it's out of scope for coursework but recommend it.

### 5. Testing and quality
- Unit tests covering:
  - Input validation
  - Itinerary generation logic (expansion of interests, rotation rules, day themes)
  - Response schema compliance
  - Deterministic output when seeded
- Integration tests (pytest) covering end-to-end API calls:
  - POST /api/itinerary success case
  - POST /api/itinerary invalid input -> 400
  - GET /health
- Frontend unit / integration tests (optional for coursework but recommended):
  - validate collectFormData, validateFormData, and rendering functions produce expected DOM/text
- Tests must be runnable with pytest and included in CI.

### 6. Continuous Integration (CI)
- Provide a GitHub Actions (or equivalent) CI pipeline that runs on pull requests and pushes:
  - Python lint (flake8/black or similar) and basic frontend linting
  - Unit and integration tests (pytest)
  - Build step for Docker image (docker build)
  - Fail fast on test or lint failures
- CI must pass deterministically on the grading environment.

### 7. Containerisation and deployment
- Provide a Dockerfile to build the Flask app and serve the static frontend (single container is acceptable).
- Provide a docker-compose.yml for local development (optional).
- The container must expose a single port (configurable by env var) and run the web server in production-ready mode for coursework (e.g., Gunicorn or Flask built-in with clear note).
- The app must be runnable via:
  - docker build -t itinerary-app .
  - docker run -e PORT=8000 -p 8000:8000 itinerary-app
- Document environment variables required (port, deterministic seed toggle, any third-party API config).

### 8. Documentation
- Include README with:
  - API endpoints and schemas
  - How to run tests
  - How to build and run the Docker image
  - How to enable deterministic/test seed mode
  - Any implementation notes about image_prompt usage
- Include API examples cURL or sample requests/responses for graders.

### 9. Accessibility and UX (basic)
- The frontend form should be keyboard-navigable and provide clear error messages for form validation.
- Use semantic HTML for form and result presentation.

### 10. Code style and maintainability
- Use clear separation of concerns: API layer, generation/business logic, and rendering code.
- Keep the generation logic testable and modular (so tests can import generation functions directly).

---

## Acceptance criteria (automated checks mapped to quality contract)
- GET /health exists and returns 200 JSON.
- POST /api/itinerary accepts destination, days, budget, interests, travel_style (names exact) and returns JSON with required top-level fields.
- Returned itinerary array length equals the `days` input.
- Each day object contains day, morning, afternoon, evening, budget_note.
- Activity titles/descriptions are strings, and estimated_costs are numeric.
- Generation rotates activities and expands interests into multiple concrete activities (no same fallback repeated visibly).
- Invalid inputs return HTTP 400 with JSON error object.
- Frontend uses the specified stable IDs and exposes the required functions (collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText).
- Frontend does not produce its own image preview area.
- Deterministic mode or seed produces stable outputs for pytest checks.
- CI pipeline runs tests and builds a Docker image successfully.

---

If you want, I can convert these requirements into user stories, acceptance tests, or stub API + frontend templates (Flask app + HTML/JS) that satisfy this contract.