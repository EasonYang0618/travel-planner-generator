# Requirements

This document defines functional and non-functional requirements for a coursework-scale Flask API + website that generates personalised city travel itineraries. Scope is limited to a single Flask application that exposes a stable API and serves a small frontend. The specification follows the provided quality contract and keeps the project suitable for coursework, automated tests and Docker deployment.

---

## Functional requirements

1. API surface
   - Expose GET /health that returns 200 and a small JSON body indicating service status.
   - Expose POST /api/itinerary that accepts a JSON body and returns a JSON itinerary.

2. POST /api/itinerary — request schema
   - Accept a JSON object with the following fields:
     - destination: string (required)
     - days: integer > 0 (required)
     - budget: integer or float (numeric budget-level that influences estimated costs) (required)
     - interests: array of strings (may be empty) (required)
     - travel_style: string (e.g., "relaxed", "active", "family") (required)
   - Example request body:
     ```
     {
       "destination": "Lisbon",
       "days": 3,
       "budget": 75,
       "interests": ["food", "outdoor"],
       "travel_style": "relaxed"
     }
     ```

3. POST /api/itinerary — successful response schema (stable contract)
   - Return HTTP 200 and a JSON object with top-level fields exactly:
     - destination: string
     - days: integer
     - budget: numeric
     - interests: array of strings
     - travel_style: string
     - overview: string (short human-readable summary)
     - itinerary: array of day objects (length must equal days)
     - tips: array of human-readable strings
   - Each day object must contain:
     - day: integer (1-based)
     - morning: activity (see activity type below)
     - afternoon: activity
     - evening: activity
     - budget_note: string (human-readable explanation of how costs relate to budget)
   - Activity value:
     - May be either a string or a dictionary/object, but any dictionaries must contain explicit readable fields (e.g., title, description, estimated_cost, image_prompt).
     - Required activity fields if object:
       - title: string
       - description: string
       - estimated_cost: numeric (adjusted by budget)
       - image_prompt: string (optional — see AI image generation)
     - Example itinerary day:
       ```
       {
         "day": 1,
         "morning": {
           "title": "Breakfast at Street-Food Lane",
           "description": "Sample local pastries and coffee at the market stalls.",
           "estimated_cost": 8.5,
           "image_prompt": "A busy Mediterranean street market breakfast scene in Lisbon"
         },
         "afternoon": "Lakefront walk at Jardim do Parque",
         "evening": {
           "title": "Signature Restaurant Meal",
           "description": "Tasting menu at a well-known local restaurant.",
           "estimated_cost": 45,
           "image_prompt": "Fine dining plate with local cuisine and wine"
         },
         "budget_note": "Day 1 mixes low-cost street food and one mid-range restaurant; total estimated: ~62."
       }
       ```

4. Input validation & errors
   - Invalid inputs must return HTTP 400 and a JSON error object with:
     - error: string (brief error message)
     - details: optional object/array with specific field errors
   - Example error:
     ```
     {
       "error": "Validation failed",
       "details": {"days": "must be an integer > 0"}
     }
     ```

5. Itinerary generation rules (quality contract)
   - The itinerary array length must equal the requested days.
   - No generic fallback activity should repeat each day. Instead rotate morning/afternoon/evening items using:
     - destination
     - day number
     - time slot (morning/afternoon/evening)
     - user interests
   - Expand each interest into several concrete activities before building the itinerary (e.g., "food" -> ["breakfast street-food lane", "local market tasting", "signature restaurant meal", "dessert and tea stop", "evening snack street"]). Use these expanded activity buckets to avoid visible repetition across days.
   - Each day should, where possible, have a different theme or planning focus (culture day, food day, outdoors day, slow day, neighbourhood exploration, etc.).
   - Activity titles and descriptions must be human-readable strings (never raw dictionaries printed in the frontend or a value of "[object Object]").

6. Costing
   - estimated_cost fields must be numeric values (float or int), calculated/adjusted according to the numeric budget input.
   - budget_note must be a human-readable string per day explaining estimated costs relative to the provided budget numeric.

7. AI image generation integration (minimal coursework scope)
   - The API may optionally include an image_prompt (string) for activities or days that can be used by a separate image-generation agent later.
   - The application must not call an external image generation service during itinerary generation (to keep deterministic outputs). Only supply image prompt strings; do not return binary images or external image URLs.
   - The frontend must not create its own image preview area; image preview and rendering are handled later by a separate integration agent.

8. Frontend — DOM & functions (stable contract)
   - The generated frontend must include specific stable element IDs:
     - plannerForm, destination, days, budget, interests, travel_style, resultsContainer, daysContainer, formMessage, errorMessage
   - The frontend must implement the following stable functions (exact names required):
     - collectFormData(): collect and return data matching the POST schema.
     - validateFormData(data): validate form data and return {valid: boolean, errors: {...}}.
     - setLoading(isLoading): toggle UI loading state.
     - showError(message): show error message in errorMessage element.
     - renderItinerary(itinerary): render the full itinerary into resultsContainer/daysContainer.
     - renderDay(dayObject): render a single day object into DOM.
     - renderActivity(activityObjectOrString): render activity fields as readable text (must never display "[object Object]").
     - formatActivityText(activityObjectOrString): return a single human-readable string for display.
   - The frontend must not create or assume an image preview area — it should ignore any image_prompt fields or store them but not attempt to display images.
   - All rendered activity titles/descriptions must be human-readable strings. If an activity is an object, render its title and description fields explicitly rather than object stringification.

9. Determinism
   - Itinerary generation must be deterministic for identical inputs to permit automated pytest checks. If any pseudo-random selection is used, it must be seeded deterministically using a seed derived from the input (for example a stable hash of destination+days+budget+interests+travel_style).

10. Accessibility & UX (basic coursework requirements)
    - Forms must provide labels for inputs and basic client-side validation feedback.
    - The results must be readable on common desktop widths and mobile; semantic HTML where feasible.

11. Testing APIs and frontend behavior
    - Provide automated tests (see Non-functional) that assert the API response schema and frontend function presence/behavior.

---

## Non-functional requirements

1. Testability & automated checks
   - Provide a test suite runnable with pytest that includes:
     - Tests for GET /health returning 200 and expected JSON.
     - Tests for POST /api/itinerary with valid input returning 200 and a response matching the stable schema.
     - Tests for POST /api/itinerary invalid inputs returning 400 with an error object.
     - Tests that itinerary length equals days and that each day has morning/afternoon/evening/budget_note.
     - Tests that estimated_cost fields are numeric and adjusted by budget.
     - Determinism test: repeated calls with identical input produce identical responses.
   - Provide basic frontend unit tests (recommended small test using a JS test runner or simple DOM tests using jsdom or Playwright) that assert:
     - Required element IDs exist.
     - Required functions (collectFormData, validateFormData, setLoading, showError, renderItinerary, renderDay, renderActivity, formatActivityText) are defined and reachable.
     - renderActivity renders readable text (not "[object Object]") for both string activities and object activities.

2. Continuous Integration (CI)
   - Provide a CI configuration (e.g., GitHub Actions) that:
     - Installs dependencies.
     - Runs unit tests (backend pytest and frontend tests).
     - Lints Python (e.g., flake8 or pylint) and JavaScript (e.g., ESLint) code.
     - Builds a Docker image for the application (see Docker requirements).
     - Fails the pipeline if tests or linters fail.

3. Docker deployment
   - Provide a Dockerfile that produces a container capable of running the Flask app and serving static frontend files.
   - The container MUST expose a configurable port (default 5000) via environment variable PORT.
   - Include a HEALTHCHECK in Dockerfile that queries GET /health and considers non-200 a failure.
   - Optionally provide a docker-compose.yml for local development (api service, environment variables).
   - The Docker image must be buildable in CI and runnable locally for evaluation.

4. Deterministic builds & reproducibility
   - Avoid nondeterministic runtime behavior: any random choices used for variety must be seeded deterministically from the request parameters.
   - Use locked dependency files (requirements.txt or Pipfile.lock / poetry.lock) to allow reproducible CI builds.

5. Performance
   - Response latency should be reasonable for coursework: typical requests complete under 1–2 seconds with no external network calls (image generation excluded).
   - The API must refuse overly large requests (e.g., days > 30) with a 400 error and descriptive message.

6. Security & hardening (basic)
   - Validate and sanitize all inputs server-side.
   - Do not execute arbitrary code or shell commands based on user input.
   - Do not embed secrets in client-side code or in the repository; use environment variables for sensitive configuration.
   - CORS: enable only what is necessary for the frontend served by the same app (or configure safe CORS policy for the coursework environment).

7. Logging & error handling
   - Log API requests and errors to console in a structured, readable format suitable for local debugging.
   - Return helpful error messages for client failures (400) and a generic 500 message for unexpected server errors.

8. Maintainability & code quality
   - Keep code modular: separate route handlers, itinerary generation logic, and frontend static assets.
   - Provide clear README with build/test/run instructions including how to run Docker container and run tests locally.

9. Accessibility & Internationalisation (coursework scope)
   - Provide UTF-8 safe outputs that work with non-ASCII destination names.
   - Keep UX readable but full i18n is out of scope.

10. AI image generation (non-functional)
    - Since image generation is handled later, the app must:
      - Provide stable image_prompt strings where applicable.
      - Not depend on or call remote AI image generation services during normal itinerary generation (no network calls for images).
      - Ensure the image_prompt text is deterministic and derived from activity fields (so an image-generation agent can reproduce previews from the same input).

---

## Acceptance criteria (automated checks / instructor checklist)

- GET /health returns 200 with JSON status.
- POST /api/itinerary accepts the specified request fields and returns a JSON response with the exact top-level fields: destination, days, budget, interests, travel_style, overview, itinerary, tips.
- The itinerary array length equals the input days.
- Each day object includes day, morning, afternoon, evening, budget_note.
- Activity titles/descriptions are human-readable strings; no "[object Object]" in outputs.
- estimated_cost fields are numeric and reflect budget adjustments.
- Invalid requests return HTTP 400 and a JSON error object.
- Frontend includes the stable element IDs and functions (names match exactly).
- Frontend does not render an image preview area.
- Deterministic behavior: same input -> same output.
- CI runs tests/lint and builds Docker image; Docker image includes healthcheck.

---

If you want, I can next generate:
- A concise example OpenAPI-like schema for the POST /api/itinerary endpoint, or
- A checklist of pytest tests (skeletons), or
- A minimal Dockerfile and CI workflow example for this coursework project.