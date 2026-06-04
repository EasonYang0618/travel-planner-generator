Overview
A lightweight web application for a small travel agency to generate personalised city travel itineraries. Users submit destination, trip length, budget level, interests, and travel_style via a website or Flask API. The system returns a clear, day-by-day itinerary and supporting tips. The deliverable is deterministic, testable, and deployable in Docker.

Goals
- Provide a stable, documented Flask API for itinerary generation.
- Provide a readable, accessible frontend that collects input and renders itineraries.
- Produce human-readable, non-repetitive, multi-day itineraries that expand each interest into many concrete activities.
- Ensure determinism and automated testability (pytest).
- Enable later AI-powered image integration via a clearly defined hook (no frontend image preview area).
- Deliver a Docker-deployable application with CI-friendly stability.

Scope
Included
- Flask API with required endpoints and request/response contract.
- Single-page frontend that posts form data and renders results using stable IDs and functions.
- Itinerary generation logic that:
  - expands each interest into multiple concrete activities,
  - rotates morning/afternoon/evening activities to avoid repeated generic fallbacks,
  - assigns numeric estimated costs adjusted by budget,
  - assigns a theme or planning focus per day where possible.
- Automated tests (pytest) covering API contract, data validation, itinerary rules, and deterministic outputs.
- Dockerfile (and optional docker-compose) for containerized deployment and health checks.
- Hooks for future AI image integration (metadata fields/IDs), but no image preview area in this deliverable.

Excluded
- On-the-fly AI image generation/display in the frontend (handled by a separate frontend image contract agent).
- Third-party booking or payment integrations.
- Real-time user accounts or persistent user storage beyond basic in-memory/session for demo purposes.

Constraints
- API must be implemented in Flask and be deterministic for automated tests (configurable seed or no randomness).
- Frontend must be simple, readable, and accessible; must not render raw object representations like “[object Object]”.
- Use only stable field names, element IDs, and function names per the quality contract so automated checks can validate behavior.
- Estimated costs must be numeric and derived from budget parameter.
- Must validate inputs and return HTTP 400 with a JSON error object on invalid requests.
- No built-in image preview area in frontend; provide metadata hooks for later image integration.
- Code must be containerized with a Dockerfile and start reliably for CI and manual testing.
- Keep dependencies minimal to simplify deterministic builds and tests.

Success Criteria
API stability
- Expose GET /health and POST /api/itinerary.
- POST /api/itinerary accepts JSON: destination, days, budget, interests, travel_style.
- Invalid input returns HTTP 400 with a JSON error object.
- Deterministic behaviour (seedable or no randomness) so pytest checks pass consistently.

Response contract and itinerary rules
- A successful response JSON MUST include top-level keys: destination, days, budget, interests, travel_style, overview, itinerary, tips.
- itinerary is a list whose length equals days.
- Each itinerary day object MUST include: day, morning, afternoon, evening, budget_note.
- Activity titles/descriptions must be human-readable strings (no raw dictionaries or “[object Object]”).
- Activities may be objects internally, but the frontend must render readable fields.
- Estimated costs are numeric and adjusted by budget level.
- Activities must not repeat a single generic fallback each day; rotate morning/afternoon/evening using destination, day number, time slot, and user interests.
- Expand each interest into multiple concrete activities before assembling the itinerary (examples in quality contract: food → multiple concrete items; outdoor → varied outdoor activities).
- Each day should have a distinct theme/planning focus where feasible.

Frontend readability and stability
- The frontend MUST NOT create its own image preview area; leave image integration for the image contract agent.
- Use stable element IDs: plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage.
- Provide and use stable functions: collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
- Render activity fields as readable strings; never display raw objects.
- Provide clear success and error feedback in the UI.

Automated tests
- Provide pytest test suite validating:
  - API endpoints and error handling (GET /health, POST /api/itinerary with valid/invalid inputs).
  - Response contract (keys present, itinerary length equals days, each day has required fields).
  - Non-repetition/rotation rules and interest-expansion behavior.
  - Numeric estimated costs adjusted by budget.
  - Frontend-generated HTML contains stable IDs and expected function hooks (unit or integration tests).
- Tests must be deterministic and runnable in CI.

Docker deployment
- Provide a Dockerfile that builds and runs the Flask app and static frontend.
- App must start reproducibly and expose health and API endpoints (document port).
- Container passes health check via GET /health.
- Include simple instructions for building and running the container.

Acceptance metrics (pass/fail)
- All automated pytest checks for the quality contract pass.
- Manual inspection: frontend renders readable itineraries without [object Object], uses required IDs and functions, and does not include an image preview area.
- Docker container starts and GET /health returns 200.

Notes / Implementation hints
- Implement itinerary generator to first map each user interest to a list of concrete activities, then schedule activities across days with rotation rules and daily themes.
- Make cost adjustments numeric (e.g., budget multiplier) and expose budget_note per day.
- Keep code deterministic: either avoid randomness or expose a seed parameter for tests.
- Document the API schema and any configuration flags required for deterministic runs.