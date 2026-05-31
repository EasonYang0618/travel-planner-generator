Overview:
A lightweight web application for a small travel agency that generates clear, personalised day-by-day city itineraries. Users submit destination, days, budget level, interests, and travel_style via a Flask API and a web UI. The system returns a deterministic, human-readable itinerary and exposes a stable API and frontend contract so automated tests and deployment are reliable.

Goals:
- Provide accurate, readable, and non-repetitive multi-day itineraries tailored to destination, days, budget, interests, and travel_style.
- Expose a stable Flask API for integration and automated testing.
- Provide a simple, accessible frontend that renders the itinerary with clear text (no raw objects shown).
- Support later addition of AI-generated images via a clear integration point (the frontend must not create its own image preview area).
- Be fully testable and deployable via Docker.

Scope:
In scope
- Flask API with GET /health and POST /api/itinerary.
- Frontend web page that submits the form and renders results.
- Itinerary generation logic that:
  - Expands each interest into many concrete activities before assembling the itinerary.
  - Produces day-by-day entries with morning/afternoon/evening slots, a day theme where possible, and a budget_note.
  - Estimates numeric costs adjusted by budget level.
  - Avoids repeating the same fallback activity each day; rotates slot content using destination, day number, time slot and interests.
- Automated pytest-based checks that validate the API, response schema, deterministic outputs, and rotation/expansion rules.
- Dockerfile(s) and docker-compose for local deployment.
Out of scope
- Built-in AI image generation or image preview UI (images integrated later by a separate image contract agent).
- Large-scale production concerns (multi-tenant auth, payment, analytics) unless required later.

Constraints:
- API contract (must be implemented exactly):
  - Endpoints: GET /health (simple 200 OK JSON) and POST /api/itinerary.
  - POST body must accept: destination, days, budget, interests, travel_style.
  - Successful itinerary response must contain top-level fields: destination, days, budget, interests, travel_style, overview, itinerary, tips.
  - itinerary must be a list with length == days; each day entry must include: day, morning, afternoon, evening, budget_note.
  - Estimated costs must be numeric values (ints/floats) adjusted by budget (not strings like "low/medium/high").
  - Activities may be represented as dictionaries internally, but any fields rendered by the frontend must be human-readable strings (no raw "[object Object]").
  - Invalid input must return HTTP 400 with a JSON error object.
- Frontend stability:
  - Stable element IDs required: plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage.
  - Stable client functions required: collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
  - Frontend must not create its own image preview area; provide integration hooks/metadata for future AI images.
- Itinerary generation rules:
  - Expand each declared interest into multiple concrete activities (e.g., "food" -> breakfast street-food lane, local market tasting, signature restaurant meal, dessert & tea stop, evening snack lane).
  - Rotate or vary morning/afternoon/evening items across days so the user does not see the same generic fallback each day.
  - Where possible give each day a different theme or planning focus.
  - Activity titles and descriptions must be human-readable strings.
- Determinism & testing:
  - Generation must be deterministic for the same inputs (use a seeded RNG tied to inputs) so pytest checks are stable.
  - Code must be structured so automated tests can assert response schema, item counts, rotation rules, numeric cost scaling, and frontend element/function presence.
- Deployment:
  - Support containerized deployment (Dockerfile for the Flask app and static frontend, optional docker-compose), with health check route used by orchestration.

Success Criteria:
The project will be considered successful when the following are met:

API stability
- GET /health returns 200 and JSON status.
- POST /api/itinerary accepts the required fields and returns the specified top-level JSON fields.
- Invalid requests return HTTP 400 with a JSON error object.
- Outputs are deterministic for identical inputs (seeded generation).

Frontend readability
- Frontend uses the required stable element IDs and functions.
- All rendered activity titles/descriptions and budget notes are human-readable strings (no raw objects).
- Frontend rendering functions (renderItinerary, renderDay, renderActivity, formatActivityText) produce clear, accessible text and never display [object Object].
- Frontend shows a clear results container (resultsContainer, daysContainer) and uses formMessage / errorMessage for feedback.

AI image integration
- Frontend provides integration hooks/metadata (e.g., image_key or image_prompt fields per activity) but does not create an image preview area or attempt to fetch/generate images itself.
- API/Frontend include consistent metadata fields (if any) for future image-agent consumption without embedding images now.

Automated tests
- Pytest suite verifies:
  - API endpoints, response schema, and 400 behavior.
  - itinerary list length equals days.
  - Each day includes day, morning, afternoon, evening, budget_note.
  - Activities are expanded per interest into many concrete activities and rotation prevents repeating the same fallback each day.
  - Estimated costs are numeric and scaled by budget.
  - Deterministic outputs for same input.
  - Frontend static checks (presence of required IDs and functions).
- Tests must be runnable in CI and pass deterministically.

Docker deployment
- Dockerfile(s) build the app and serve the frontend and API.
- docker-compose (recommended) runs services and exposes the API and frontend.
- Health check route used to validate container readiness.
- Containers run deterministically; tests can be executed inside a container or via CI pipeline.

Acceptance
- All automated tests pass.
- Manual verification: submitting a sample request returns a day-by-day itinerary with numeric costs, varied activities across days (no repeated generic fallback), human-readable strings, and frontend renders readable fields with the required IDs and functions present.
- Application can be started via Docker and responds on /health and /api/itinerary.

Notes / Implementation guidance (short)
- Use seeded RNG based on a hash of input fields to ensure deterministic variation.
- Build an interest -> expanded activities map with 4–6 concrete activities per interest.
- Use numeric cost multipliers per budget level (e.g., budget: low=0.6, medium=1.0, high=1.6).
- Keep frontend lightweight (vanilla JS or minimal framework) to make required IDs/functions straightforward to test.
- Expose clear hooks/metadata for the later image-agent integration but defer image fetching/rendering.