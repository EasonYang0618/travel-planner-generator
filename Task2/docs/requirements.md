# Requirements

Below are concise functional and non-functional requirements scoped for a coursework Flask API + website that generates personalised city travel itineraries.

---

## Functional requirements

Each requirement includes an ID, short description, acceptance criteria and brief implementation notes.

- F1 — Input form / API request
  - Description: Accept destination, trip length (days), budget level (low/medium/high), 1+ interests (e.g., museums, food, parks), optional start date, optional number of items per day.
  - Acceptance: Web form and API endpoint accept these fields; required fields validated; clear error returned for missing/invalid values.
  - Notes: API uses JSON body; web form posts to backend; client-side and server-side validation.

- F2 — Input validation
  - Description: Validate destination exists in the system (or fallback to “unknown”), enforce trip length between 1 and 30, budget within allowed values, interests from supported list.
  - Acceptance: Invalid inputs produce 4xx responses (API) and user-visible form errors (site); server never crashes on malformed input.
  - Notes: Supported destinations and interests stored in DB or config.

- F3 — POI dataset and metadata
  - Description: Maintain a dataset of points of interest (POIs) per destination with: id, name, category/tags, coordinates (lat/lon), estimated visit duration, cost level, opening hours (optional), short description.
  - Acceptance: System can retrieve POIs for a destination and filter by interest and budget.
  - Notes: Use SQLite or JSON data file for coursework; admin script to seed dataset.

- F4 — Itinerary generation
  - Description: Generate a day-by-day itinerary matching user inputs: allocate POIs per day, respect daily time budget (e.g., 8–10 hours), group nearby POIs to minimise travel, include suggested meal times and free time.
  - Acceptance: Generated itinerary has entries for each day, includes POI name, scheduled time window (approx.), estimated duration, and brief description. Trip length matches request.
  - Notes: Implement a simple heuristic (filter → sort by match → cluster by proximity → allocate to days). No need for heavy optimization or external routing API for coursework.

- F5 — API: generate and retrieve itineraries
  - Description: Provide RESTful endpoints:
    - POST /api/itineraries — generate (returns itinerary id + data)
    - GET /api/itineraries/{id} — retrieve a saved itinerary
    - GET /api/destinations — list supported destinations
    - GET /api/interests — list supported interests
    - GET /api/health — basic health check
  - Acceptance: Endpoints return JSON with appropriate status codes and error messages; POST returns generated itinerary and persistent id.
  - Notes: Use Flask-RESTful or Flask routes.

- F6 — Persistence
  - Description: Save generated itineraries (inputs + itinerary + timestamp) to a simple persistent store (SQLite).
  - Acceptance: After generation, GET by id returns the same itinerary; entries persist across server restarts.
  - Notes: No user accounts required; itinerary id is a UUID or similar.

- F7 — Website UI: create & view itineraries
  - Description: Provide a web UI that:
    - Presents the input form
    - Displays the generated itinerary in a clear day-by-day layout
    - Offers link to share/revisit a saved itinerary via its id/URL
  - Acceptance: Users can generate and view itineraries via browser; layout readable on desktop and mobile.
  - Notes: Use Jinja templates and minimal CSS (Bootstrap optional).

- F8 — Error handling & user messages
  - Description: Return meaningful error messages in API responses and friendly messages on the website for common error conditions (invalid input, no POIs found, internal error).
  - Acceptance: Errors are handled without exposing stack traces; HTTP status codes used appropriately.

- F9 — Logging and basic monitoring
  - Description: Log requests, responses (summary), and errors to server logs with timestamps; include API usage logs.
  - Acceptance: Logs capture sufficient information to debug itinerary generation failures; logging can be toggled between debug and production modes.
  - Notes: Use Python logging.

- F10 — Admin data management (minimal)
  - Description: Provide a simple CLI/script or minimal admin route to seed or update the POI dataset for coursework (not a full admin UI).
  - Acceptance: Developer can seed dataset into DB from CSV/JSON.

- F11 — Optional: Export / print
  - Description: Allow exporting an itinerary to PDF or printer-friendly HTML.
  - Acceptance: User can produce a printable view; PDF is optional but encouraged.
  - Notes: Use wkhtmltopdf or browser print CSS; mark optional.

---

## Non-functional requirements

- N1 — Simplicity and scope
  - Requirement: Design must be implementable within a coursework timeframe: single Flask app, SQLite or JSON-backed data, no large external dependencies.
  - Acceptance: Project can be set up and run locally with provided instructions and requirements file.

- N2 — Performance
  - Requirement: Typical itinerary generation request should complete within 5 seconds on a typical laptop; API responses for retrieval should be under 1 second.
  - Acceptance: Measured generation time for representative inputs less than 5s.

- N3 — Reliability
  - Requirement: Saved itineraries must be durable across server restarts; API should respond with appropriate errors rather than crash.
  - Acceptance: Persisted entries load after restart; no unhandled exceptions propagate to clients.

- N4 — Usability
  - Requirement: Website must be clear and easy to use: labeled fields, concise instructions, readable itinerary layout, mobile-friendly.
  - Acceptance: Basic usability checks pass (form labels, error feedback, responsive layout).

- N5 — Security (basic)
  - Requirement: Validate and sanitize all inputs, avoid SQL injection, prevent XSS in templates, protect any form submissions from CSRF.
  - Acceptance: Use parameterised queries or ORM; Jinja autoescaping enabled; CSRF token used for site forms.

- N6 — Privacy
  - Requirement: Do not collect PII unless explicitly required; if any PII is stored it must be optional and documented.
  - Acceptance: Default dataset and storage contain no personal data; documentation explains data handling.

- N7 — Maintainability & code quality
  - Requirement: Code should be modular, documented, and include docstrings and README. Use a requirements.txt and (optional) Dockerfile.
  - Acceptance: Project includes README with setup/run instructions and inline documentation for core modules.

- N8 — Testability
  - Requirement: Include automated tests covering core itinerary generation logic and API endpoints (unit tests + a few integration tests).
  - Acceptance: Test suite runs locally (pytest) and covers key edge cases (no POIs, invalid inputs, typical generation).

- N9 — Portability / Deployability
  - Requirement: App should run locally and be easily deployable to a typical PaaS (Heroku, Render) or Docker container.
  - Acceptance: Provide simple deployment notes and a Dockerfile or Procfile if applicable.

- N10 — Extensibility
  - Requirement: Design should allow later integration of external services (maps, routing, third-party POI APIs) without major rewrites.
  - Acceptance: POI access behind a data access layer; itinerary generation logic isolated.

- N11 — Accessibility (basic)
  - Requirement: Follow basic accessibility practices: semantic HTML, alt text for images, color contrast, keyboard navigability.
  - Acceptance: No critical accessibility barriers; basic manual checks pass.

- N12 — Logging & observability
  - Requirement: Provide logs for debugging and basic metrics (request counts, errors); sensitive info must not be logged.
  - Acceptance: Logs include timestamps, endpoints, status codes; debug mode more verbose.

- N13 — Error tolerance / graceful degradation
  - Requirement: If external resources (e.g., optional map embed) fail, the core itinerary generation and viewing must still work.
  - Acceptance: Optional features fail gracefully with user-facing message; core flow unaffected.

---

If useful, these requirements can be converted into user stories, acceptance-test checklists, or an initial backlog for coursework planning.