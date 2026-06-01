Overview
- Build a small, deterministic web application for a travel agency that generates clear, human-readable, day-by-day city itineraries from user inputs (destination, days, budget, interests, travel_style).  
- Deliverables: a Flask JSON API and a browser frontend that consumes it, suitable for automated tests and Docker deployment.

Goals
- Produce readable, predictable itineraries that are useful to tourists and easy to verify by automated tests.
- Ensure a stable API contract so coursework grading and integration tools can rely on endpoints, payloads and response shapes.
- Maintain frontend readability, accessibility and deterministic rendering (no raw JS objects shown).
- Provide a codebase that can be validated by pytest and deployed in a single Docker container image.
- Support future AI image integration without the frontend creating its own image preview area; allow later augmentation by a separate image contract agent.

Scope
Included
- Flask API with:
  - GET /health — simple health check (200 OK + JSON).
  - POST /api/itinerary — accepts request JSON and returns a validated itinerary JSON.
- Frontend web app (static HTML + JS) that:
  - Presents a small form, collects input, validates, calls POST /api/itinerary, and renders results.
  - Uses the required stable element IDs and function names so automated checks can locate and exercise UI behavior.
  - Renders readable fields for all activity data (never display [object Object]).
  - Does not produce its own image preview area; reserves image handling to a later agent.
- Itinerary generation logic that:
  - Expands each interest into several concrete activity ideas before assignment.
  - Rotates morning/afternoon/evening activities using destination, day number, time slot and user interests.
  - Assigns a theme or planning focus per day when possible.
  - Produces numeric estimated costs adjusted by budget level.
  - Produces one itinerary day object per requested day.
- Automated tests (pytest) that assert API and frontend contract stability.
- Docker deployment configuration for API + static frontend.

Excluded
- In-app image generation or preview UI (handled later by image contract agent).
- External booking/payment integrations.
- Complex personalization beyond supplied inputs.

Constraints
- Deterministic behavior: given the same input, the system must produce the same itinerary (no random seeds or non-deterministic ordering) to allow automated checks.
- Response and UI must be human-readable: activity titles/descriptions are strings (no raw dicts displayed).
- Estimated costs are numeric values (integers or floats), computed from a base and adjusted by budget (e.g., budget factor).
- API input validation: invalid or missing required fields return HTTP 400 with a JSON error object containing at least an "error" string.
- The frontend must not render any image preview area or manage images; any image fields must be ignored or hidden until the image contract agent augments them.
- Stable names: frontend must use these element IDs: plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage.
- Stable functions required in frontend: collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
- The Flask API must deterministically expose GET /health and POST /api/itinerary.
- Each itinerary day must include fields: day, morning, afternoon, evening, budget_note.
- No activity may be the same generic fallback repeated each day; activities must be varied by expansion and rotation.
- Code quality: maintainable, readable, and amenable to static analysis and pytest checks.
- Packaging: application runnable in Docker with a single container (or documented multi-container if split) for coursework submission.

Success Criteria (measurable acceptance conditions)
- API stability
  - GET /health returns 200 with a JSON payload indicating status.
  - POST /api/itinerary accepts JSON with keys: destination, days, budget, interests, travel_style; missing/invalid -> HTTP 400 + JSON error.
  - Successful POST returns JSON containing top-level keys: destination, days, budget, interests, travel_style, overview, itinerary, tips.
  - The itinerary array length equals days.
  - Each itinerary day object contains exactly: day (int), morning, afternoon, evening (each human-readable strings or structured objects that the frontend renders), and budget_note (string or numeric note).
  - Estimated costs in activity objects are numeric values and reflect budget adjustments.
- Frontend readability and stability
  - The frontend uses and exposes the stable element IDs and function names listed in Constraints.
  - The frontend never displays JS objects as raw “[object Object]”; renderActivity/formatActivityText produce human-readable strings for titles and descriptions.
  - The frontend does not create any image preview area (space reserved for later augmentation only).
  - The frontend provides clear error messaging (via errorMessage) and loading states (via setLoading).
- AI image integration readiness
  - The application design and API do not hard-code or render images; they allow a later agent to add image URLs or overlays without UI refactor.
  - The frontend ignores or hides image fields until an image contract agent updates rendering logic.
- Activity generation quality
  - Interests are expanded into multiple concrete activities before assignment (e.g., food -> several distinct food activities; outdoor -> multiple outdoor activities).
  - Activity selection rotates by day/time slot and includes destination and day number in activity variations so no daily repeat of a generic fallback.
  - Each day attempts a distinct theme or focus where possible.
- Automated tests
  - A suite of deterministic pytest tests covers:
    - API contract tests (health, 400 handling, response shape, itinerary length equals days, day fields exist).
    - Content rules (no repeated fallback items, numeric estimated costs, human readable strings).
    - Frontend DOM contract tests (stable IDs present, named JS functions exist, no image preview element present).
  - Tests must pass reliably on CI and locally.
- Docker deployment
  - A Dockerfile (and optional docker-compose) builds a container that runs the Flask API and serves the frontend static files; container can be started with a documented command.
  - The container exposes the API and serves the frontend at documented ports; deployment steps are deterministic and work in an automated CI environment.

Acceptance checks (examples)
- POST /api/itinerary with valid input returns JSON with required top-level keys; len(response["itinerary"]) == days.
- For each day i in itinerary:
  - response["itinerary"][i]["day"] == i+1
  - morning/afternoon/evening are non-empty human-readable strings; budget_note is present.
- A pytest test verifies no activity title equals a single generic fallback repeated across days.
- Frontend DOM inspection shows elements with IDs plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage and that functions collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText are defined.
- Docker build and run produce a healthy service that passes the API tests.

Notes
- Keep generation logic and rendering simple and deterministic for coursework grading; prioritize clear, verifiable outputs over heavy personalization.
- Design the API and frontend so a future image contract agent can attach image URLs to activities or days without changing the required frontend IDs/functions or breaking tests.