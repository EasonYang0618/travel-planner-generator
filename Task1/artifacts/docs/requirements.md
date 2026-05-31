# Requirements

This document defines functional and non-functional requirements for a coursework-scale Flask API + website that generates personalised city travel itineraries for a small travel agency. It is scoped for a student project and includes explicit stability/quality constraints required by the coursework quality contract.

---

## 1. Functional requirements

1.1 API: endpoints
- GET /health
  - Returns HTTP 200 and a simple JSON status object when the service is healthy.
- POST /api/itinerary
  - Accepts a JSON request body (see 1.2).
  - Returns HTTP 200 with a JSON itinerary response on success (see 1.3).
  - Returns HTTP 400 with a JSON error object on invalid input.

1.2 API: request schema (POST /api/itinerary)
- Request body must be JSON with these fields:
  - destination: string (e.g., "Lisbon")
  - days: integer (>=1)
  - budget: integer (e.g., numeric scale 1..5 or absolute daily budget; project may pick a scale but must be numeric)
  - interests: array of strings (e.g., ["food", "outdoor", "history"])
  - travel_style: string (e.g., "relaxed", "active")
- The API must validate required fields and types. Missing/invalid fields must produce HTTP 400 with a JSON error object.

1.3 API: success response schema (stable)
- Top-level JSON object MUST contain these keys:
  - destination: string
  - days: integer
  - budget: numeric
  - interests: array of strings
  - travel_style: string
  - overview: string (human-readable trip summary)
  - itinerary: array of day objects (length MUST equal days)
  - tips: array of strings (human-readable tips)
- Each day object MUST contain:
  - day: integer (1-based)
  - morning: activity object or human-readable string (see 1.4)
  - afternoon: activity object or human-readable string
  - evening: activity object or human-readable string
  - budget_note: numeric or string explaining day cost (budget numeric adjustments must be present)
- Activity object (if used) MUST have at least:
  - title: string (human-readable)
  - description: string (human-readable)
  - estimated_cost: numeric (adjusted by budget)
  - image_prompt: string (optional): a text prompt for later AI image generation (note: API must not return image binary data)
- Notes:
  - Activity titles/descriptions must always be strings. The frontend must never receive raw JS objects in place of strings (no [object Object] display).
  - estimated_cost must be numeric (not "low/medium/high" strings). If a per-activity breakdown is not provided, budget_note must include a numeric value for that day.
  - The itinerary array length MUST equal the `days` value supplied.

1.4 Activity generation constraints (content generation contract)
- For each interest, the backend must expand it into several concrete activities before assembling the daily itinerary so the trip does not repeat the same three generic activities across multiple days.
  - Example mappings (for guidance): 
    - "food" -> ["breakfast street-food lane", "local market tasting", "signature restaurant meal", "dessert and tea stop", "evening snack street"]
    - "outdoor" -> ["lakefront walk", "city park reset", "scenic viewpoint", "garden or nature trail"]
- Each day should, where possible, have a different theme or planning focus (e.g., "historic neighborhoods", "culinary day", "riverfront & parks").
- When assigning activities to slots (morning/afternoon/evening):
  - Rotate items so the same generic fallback does not appear each day in the same slot.
  - Use destination, day number, time slot, and user interests to vary titles/descriptions.
- Activity text must be human-readable phrases (not raw objects). The backend may include structured activity objects, but all displayed text must derive from string fields.

1.5 Error handling
- Invalid input must return HTTP 400 and JSON:
  - error: string short message
  - details: optional object or string with validation details
- The API must never return HTML error pages for API requests.

1.6 Frontend (website) requirements
- Single-page or multi-page Flask-served site that:
  - Presents a form allowing the user to enter destination, days, budget, interests, travel_style.
  - Submits the form to POST /api/itinerary and renders results returned by the API.
- Stable HTML element IDs (these identifiers MUST exist in the generated frontend):
  - plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage
- Stable frontend JavaScript function names (these functions MUST be present and used where appropriate):
  - collectFormData
  - validateFormData
  - setLoading
  - showError
  - renderItinerary
  - renderDay
  - renderActivity
  - formatActivityText
- Frontend rendering rules:
  - The frontend must render human-readable text for activities; if activity objects are provided, use title/description/estimated_cost fields to build strings via formatActivityText.
  - The frontend must never display "[object Object]" or raw object dumps. renderActivity must format fields into readable DOM text/nodes.
  - No image preview area or client-side image generation/preview should be created by the frontend at this stage. Image integration will be handled separately by a dedicated image agent later.
  - The frontend must surface error messages in the errorMessage element and general messages in formMessage.

1.7 AI image generation (integration-friendly)
- The API may include an image_prompt string per activity to allow later image generation by a separate service/agent.
- The API and frontend must NOT return or display image binaries/preview areas at this stage.
- The backend must not depend on any image-generation service for the core itinerary functionality; image prompts are optional metadata only.

---

## 2. Non-functional requirements

2.1 Determinism and testability
- Generation logic must be deterministic enough for automated tests:
  - Either use a fixed random seed for content generation in test runs, or allow seeding via configuration/ENV variable (e.g., ITINERARY_SEED).
  - Determinism ensures pytest-based automated checks can assert exact or stable properties.
- Avoid external non-deterministic dependencies in core generation (or make them mockable).

2.2 Performance
- The API must respond to typical requests (single itinerary generation) within a reasonable time for coursework (target < 3s on modest hardware). If heavy processing is needed, include clear timeouts and progress indicators.

2.3 Reliability and stability
- /health endpoint must reflect service availability.
- Validate and sanitize all user input server-side to avoid crashes.

2.4 Security
- Validate input types and sizes.
- Escape content when rendering in HTML to prevent XSS.
- Do not embed or return executable code in user-visible fields.

2.5 Maintainability and code quality
- Clear separation between API layer, generation logic, and rendering templates/static assets.
- Provide inline documentation/comments for stable functions and IDs required by the coursework tests.

2.6 Accessibility & UX (minimal)
- Form fields must be labelled and reachable via keyboard.
- Error and status messages must be visible and readable.

2.7 Logging and observability
- Log API requests and validation failures at an appropriate level for debugging (do not log sensitive info).
- Health endpoint and minimal metrics accessible to CI test scripts.

---

## 3. Testing and acceptance criteria

3.1 Automated tests (pytest)
- Unit tests for generation logic:
  - Ensure interests are expanded into multiple concrete activities.
  - Ensure activities rotate across days and time slots.
  - Ensure itinerary array length equals `days`.
  - Ensure activity titles and descriptions are strings and estimated_cost numeric.
  - Ensure each day object contains day, morning, afternoon, evening, budget_note.
- API integration tests:
  - POST /api/itinerary returns HTTP 200 and response conforms to schema for valid requests.
  - Invalid payloads return HTTP 400 with JSON error object.
  - GET /health returns HTTP 200 with expected status.
- Frontend tests (lightweight DOM checks):
  - The served HTML contains stable IDs listed in 1.6.
  - The served JS contains stable function names (basic presence checks).
  - renderItinerary/renderDay/renderActivity produce readable text (can be tested with the Flask test client + BeautifulSoup to assert rendered strings for a known response).
- Deterministic tests:
  - Use seeding or deterministic mode in tests so expected values are reproducible.

3.2 CI pipeline
- CI runs:
  - Code style checks (e.g., flake8, black optional).
  - pytest suite (unit + integration + frontend DOM checks).
  - Build step: docker build to verify Dockerfile correctness.
  - Optional: run the container and perform a smoke test against /health and /api/itinerary.
- CI must fail builds if tests fail.

3.3 Acceptance criteria (end-to-end)
- All tests must pass.
- The frontend renders an itinerary for a sample request and meets the stable-ID/function contract.
- The API strictly follows the request/response schemas and error rules.

---

## 4. Docker deployment

4.1 Dockerfile
- Provide a Dockerfile that builds a container with:
  - Flask app and static frontend assets.
  - All required Python dependencies installed.
  - A single command to run the app (e.g., gunicorn or flask run for coursework).
- The container must expose the configured port via environment variable (e.g., PORT) and default to 5000.

4.2 docker-compose (optional but recommended)
- Provide docker-compose.yml for local development/test:
  - Service for the Flask app.
  - Optional service for running tests (invoked by CI).

4.3 Configuration via environment variables
- Use environment variables for configuration (e.g., PORT, ITINERARY_SEED, FLASK_ENV) and avoid hard-coded secrets.

4.4 Container acceptance checks
- CI should build the Docker image and run it, then execute basic smoke tests:
  - GET /health returns 200.
  - POST /api/itinerary returns 200 and schema-valid response for a valid sample payload.

---

## 5. Constraints & clarifications (quality contract highlights)

- Required endpoints: GET /health and POST /api/itinerary must exist.
- POST /api/itinerary must accept destination, days, budget, interests, travel_style.
- Success response MUST include: destination, days, budget, interests, travel_style, overview, itinerary, tips.
- itinerary array length must equal days.
- Activities must rotate morning/afternoon/evening using destination, day number, time slot, and interests; avoid repeating the same generic fallback every day/slot.
- Interests must be expanded into multiple concrete activities before building the multi-day itinerary (so the user sees varied activities across days).
- Activity titles/descriptions must be human-readable strings (never show [object Object]).
- estimated_cost values must be numeric and adjusted by budget.
- Each itinerary day must include day, morning, afternoon, evening, and budget_note.
- Frontend must render readable fields and never display raw object serialisation; activity data may be structured objects but must be formatted for display.
- Invalid input must return HTTP 400 with a JSON error object.
- The generated frontend must not create its own image preview area — image integration is handled later by a separate image contract agent.
- The generated frontend must include stable IDs: plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage.
- The generated frontend must include stable functions: collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText.
- The code should be deterministic enough for pytest checks and Docker deployment (support seeding or deterministic behaviour).

---

If you want, I can also produce:
- A JSON Schema example for request/response,
- A small checklist for CI steps and pytest commands,
- A minimal Flask app skeleton and frontend template that implements the above stable IDs and functions to be used as starter code.