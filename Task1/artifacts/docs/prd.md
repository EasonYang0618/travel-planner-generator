Overview
- Build a small web application for a travel agency that generates personalised city travel itineraries. 
- Provide both a Flask API and a single-page website UI. Users supply destination, trip length (days), budget level, interests, and travel_style; system returns a clear day-by-day itinerary plus tips.

Goals
- Deliver a stable, well-documented Flask API that can be automatically exercised by tests.
- Deliver a readable, deterministic frontend that renders itineraries for humans and passes automated checks.
- Ensure itinerary content is varied, concrete, human-readable, and budget-aware.
- Make the system Docker-deployable so it can run reproducibly in CI and in class demos.
- Provide an integration path for later AI image support (handled by a separate image-agent contract).

Scope
In scope
- Flask API with health check and itinerary endpoint.
- Single-page frontend (HTML/JS/CSS) that posts to the API, validates input, and renders results.
- Deterministic itinerary generation logic that expands interests into concrete activities and rotates activities across morning/afternoon/evening.
- Automated pytest suite verifying API contract, content rules, and frontend DOM stability where practical.
- Dockerfile(s) and basic docker-compose for single-container deployment.
- Documentation describing API input/output, stable IDs and functions, and how to run tests and Docker.

Out of scope
- AI image generation or image preview rendering in the frontend (the frontend must not create its own image preview area). Image generation/integration will be provided later by a dedicated frontend image contract agent.
- External booking/payment or live maps integration.

Constraints (technical and quality contract)
- API endpoints:
  - GET /health — returns 200 with simple health JSON.
  - POST /api/itinerary — accepts JSON with keys: destination, days, budget, interests, travel_style.
- Input validation:
  - Invalid or missing inputs must return HTTP 400 with a JSON error object {error: "..."}.
  - days must be an integer >= 1.
  - budget must be a recognized level (mapped internally to numeric adjustments).
  - interests must be a list/array.
- Response shape (successful response must include all top-level keys):
  - destination (string), days (int), budget (string or canonical key), interests (list), travel_style (string),
  - overview (string),
  - itinerary (list of day objects) length must equal days,
  - tips (list or string).
- Per-day structure: each day object must include keys: day (int), morning, afternoon, evening, budget_note.
- Activities:
  - Activity titles/descriptions must be human-readable strings (no raw objects, no "[object Object]").
  - Activity entries may be objects internally, but frontend must render readable text fields only.
  - Estimated costs must be numeric values adjusted by budget (not textual low/medium/high).
- Content variability rules:
  - Expand each interest into several concrete activities before building the itinerary (e.g., food -> several concrete items; outdoor -> multiple outdoor items).
  - Itinerary activities must not repeat the same generic fallback each day.
  - Rotate morning/afternoon/evening items using destination, day number, time slot, and user interests to avoid visible repetition.
  - Where feasible, assign a different theme/focus to each day.
- Frontend stability:
  - Stable element IDs (must exist): plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage.
  - Stable JS functions (must exist): collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
  - The frontend must not create its own image preview area; any image placeholders or insertion points are handled later by the image agent.
- Determinism:
  - Generated code and itinerary generation should be deterministic (seedable random or algorithmic) so automated pytest checks can reliably reproduce outputs.
- Deployment:
  - Application must be Docker-ready with a Dockerfile and instructions for running tests in the container.

Success Criteria (must be met for acceptance)
- API stability and contract:
  - GET /health returns HTTP 200 and JSON health status.
  - POST /api/itinerary accepts destination, days, budget, interests, travel_style and validates input.
  - Invalid input returns HTTP 400 with JSON error object.
  - Successful responses include top-level destination, days, budget, interests, travel_style, overview, itinerary, tips.
  - The itinerary list length equals days.
  - Each itinerary day contains day, morning, afternoon, evening, budget_note.
  - Estimated cost fields are numeric and adjusted according to budget level.
  - Activities are human-readable strings when rendered; the frontend never displays raw objects or “[object Object]”.
- Frontend readability and stability:
  - Frontend uses the specified stable IDs and implements the specified stable functions.
  - Frontend renders results into resultsContainer and daysContainer and uses formatActivityText to produce readable text.
  - Frontend shows errors in errorMessage and form messages in formMessage.
  - Frontend does not create an image preview area (satisfies separation of concerns for later image integration).
- AI image integration readiness:
  - The frontend and API expose clear insertion points (no image UI elements created) so a later image agent can add images without changing the core app.
  - Metadata required for images (e.g., activity title, location, time) is present in API responses so an image agent can generate appropriate prompts.
- Content quality and non-repetition:
  - Each interest is expanded into multiple concrete activities before scheduling.
  - The generator rotates and varies morning/afternoon/evening activities across days (no same fallback repeated).
  - Each day attempts a different theme or focus where possible.
- Automated tests:
  - Pytest suite exists and validates: endpoints, input validation, response shape, itinerary length, per-day fields, numeric cost adjustments, non-repetition rules, stable frontend IDs and function names (where testable).
  - Tests are deterministic (use seeded randomness or algorithmic determinism) and runnable inside CI or locally.
- Docker deployment:
  - A Dockerfile (and optional docker-compose) builds and runs the app and tests.
  - The app can be launched in Docker and responds correctly to /health and /api/itinerary.
- Deterministic generation for coursework checks:
  - Itinerary generation is deterministic for a given seed/input so automated coursework graders can compare expected outputs.

Notes / Acceptance checklist (short)
- [ ] /health implemented and passes.
- [ ] /api/itinerary implemented, validates input, returns exact response keys.
- [ ] Itinerary length equals days; per-day fields present.
- [ ] Interests expanded into multiple concrete activities.
- [ ] Morning/afternoon/evening rotation and day themes implemented.
- [ ] Costs numeric and budget-adjusted.
- [ ] Frontend uses stable IDs and functions; renders readable strings only.
- [ ] Frontend does not create image preview; image metadata included in API response.
- [ ] Pytest suite passes deterministically.
- [ ] Dockerfile and run instructions included.

This PRD is intentionally concise and focused on requirements and acceptance criteria that a coursework implementation and automated tests can verify.