Overview
A small travel-agency web application that generates personalised city travel itineraries. Users provide destination, trip length (days), budget level, interests, and travel style. The system exposes a Flask JSON API and a browser frontend that submits the form to the API and renders a clear day-by-day itinerary. The app must be deterministic and testable for coursework automated checks and deployable via Docker.

Goals
- Provide reliable, human-readable, day-by-day itineraries that match user inputs.
- Maintain a stable, well-documented API contract for automated verification.
- Ensure frontend readability and deterministic rendering (no raw objects shown).
- Prepare integration points (placeholders/hooks) for later AI-generated images without rendering them.
- Ship with automated tests (pytest) that validate API and generation rules.
- Support containerised deployment with a reproducible Docker image.

Scope
In scope
- Flask backend exposing GET /health and POST /api/itinerary.
- POST /api/itinerary accepts: destination, days, budget, interests, travel_style.
- Deterministic itinerary generation logic that:
  - Expands each interest into multiple concrete activities before assembling the itinerary.
  - Produces an itinerary list with length equal to days.
  - Rotates morning/afternoon/evening items using destination, day number, time slot and interests so daily activities do not repeat the same fallback.
  - Assigns a day theme/focus where possible.
  - Produces human-readable activity titles/descriptions and numeric estimated costs adjusted by budget.
  - Each itinerary day includes: day, morning, afternoon, evening, budget_note.
- Frontend (single-page) that posts to the API and renders results using stable IDs and functions.
- pytest suite covering API endpoints, response schema, generation rules and determinism.
- Dockerfile(s) and simple docker-compose for running app and tests.

Out of scope
- Generating or displaying AI images inside the frontend (image rendering is handled later by a separate image contract agent).
- Third-party booking integrations, payment processing, or user accounts.

Constraints
- API stability: endpoints and request/response schema must be exact and stable for automated checks.
- Determinism: generation must be deterministic (no unseeded randomness); if randomness is needed it must be seedable and the seed must be controllable during tests.
- Frontend readability: UI must never display raw dictionaries or "[object Object]"; activity titles and descriptions must be plain strings.
- Input validation: invalid or missing required fields must return HTTP 400 with a JSON error object and appropriate message.
- No frontend image preview area or autonomous image requests; provide named placeholders/hooks for later image integration.
- Performance: generate typical itinerary responses within reasonable time (e.g., < 1s median in test environment).
- Deployment: must run inside Docker with clear environment configuration and health check endpoint.

Success Criteria
API stability
- Expose GET /health returning 200 OK and a simple JSON status.
- Expose POST /api/itinerary accepting JSON body with keys: destination, days, budget, interests, travel_style.
- POST /api/itinerary on success returns JSON containing top-level keys: destination, days, budget, interests, travel_style, overview, itinerary, tips.
- Invalid input returns HTTP 400 and a JSON error object describing the problem.
- The itinerary array length equals the requested days.

Frontend readability and stability
- Frontend uses stable DOM IDs: plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage.
- Frontend defines and uses stable functions: collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
- Frontend renders human-readable strings for activity titles/descriptions and numeric estimated costs; never displays raw objects or “[object Object]”.
- The frontend must not create its own image preview area; instead it exposes a named placeholder hook or metadata attributes for later image injection by the image contract agent.

AI image integration
- Provide a clear, documented hook in API responses and/or frontend DOM for later AI image integration (e.g., image_tags or activity.image_hint strings, and well-known DOM attributes on activity elements) without embedding or previewing images now.
- The application itself must not fetch or render images; it must be ready to accept image URLs or image metadata later.

Itinerary generation quality
- Interests are expanded into multiple concrete activities before itinerary construction (for example: food => breakfast street-food lane, local market tasting, signature restaurant meal, dessert and tea stop, evening snack street).
- Activities rotate by time slot and day so the same fallback is not used each day; morning/afternoon/evening slots should vary using destination + day number + time slot + interest.
- Each day should, where possible, have a different theme or planning focus.
- Activity titles/descriptions are human-readable strings; any activity data objects rendered by frontend are formatted into readable text by formatActivityText.
- Estimated costs are numeric and adjusted by budget parameter; budget_note explains cost scaling numerically.

Automated tests
- Provide pytest tests that verify:
  - /health and /api/itinerary endpoints respond correctly and deterministically.
  - POST /api/itinerary validates inputs and returns HTTP 400 on invalid requests.
  - Response schema contains required top-level keys.
  - itinerary length == days.
  - No repeated generic fallback across days; rotation rules apply.
  - Activity titles/descriptions are strings; estimated_costs are numeric.
  - Each itinerary day includes day, morning, afternoon, evening, budget_note.
  - Frontend renders readable strings (unit tests or headless DOM tests can assert the absence of “[object Object]” and presence of stable IDs/functions).
- Tests must be deterministic and runnable in CI; randomness, if present, must be seed-controlled in tests.

Docker deployment
- Provide Dockerfile(s) that build the Flask app and serve static frontend (single container acceptable).
- Provide docker-compose.yml for local development/test orchestration and for running pytest inside the container environment.
- Health endpoint must be usable by container orchestration to determine readiness.
- Build artifacts and runtime must be deterministic and runnable by automated graders.

Acceptance checklist (short)
- GET /health exists and returns 200 JSON.
- POST /api/itinerary accepts required fields and returns required top-level keys.
- itinerary length equals days and each day contains required slots and budget_note.
- Interests expanded into multiple activities; rotation of slots prevents repeating same fallback.
- Activity titles/descriptions are strings; estimated costs numeric and budget-adjusted.
- Frontend uses stable IDs and functions; never renders raw objects; provides hooks for image integration but no preview area.
- pytest suite covers contract and deterministic behavior.
- Dockerfile/docker-compose provided and app runs in container with /health reachable.

This PRD defines the minimal, verifiable contract required for coursework grading while leaving image rendering to a later agent integration step.