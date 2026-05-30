# Requirements

Project: City Travel Itinerary Generator — Flask API + Website  
Scope: Coursework-level web application (Flask backend, lightweight front-end) that generates simple, personalised day-by-day city itineraries from user inputs.

---

## Functional requirements

Each requirement is numbered FR-#. Priority: (High / Medium / Low)

FR-1 — User input form (High)  
- The website must provide a web form that accepts:
  - Destination (city name) — text
  - Trip length (number of days) — integer (1–30)
  - Budget level — enum {low, medium, high}
  - Interests — multiple-select list (e.g., culture, food, museums, outdoors, nightlife, shopping)
  - Optional: desired daily start/end times, mobility constraints (walking vs public transport)
- Acceptance: form validates required fields and shows inline errors.

FR-2 — API endpoint to generate itinerary (High)  
- Expose a Flask JSON API endpoint to request generation:
  - POST /api/itineraries
  - Request body: destination, days, budget, interests, optional parameters
  - Response: 201 Created with a JSON itinerary object (see FR-4) or error (400/422)
- Acceptance: valid POST returns a well-formed itinerary JSON within response time limit (see NFR).

FR-3 — Web UI result display (High)  
- The site must display a clear, day-by-day itinerary based on the user inputs:
  - Day headers (Day 1, Day 2, …)
  - For each day: list of activities with title, type, estimated duration, approximate cost, start time (if scheduled)
  - A summary of daily total estimated cost and travel time
- Acceptance: user sees a readable itinerary page after submitting the form.

FR-4 — Itinerary JSON schema (High)  
- Itinerary responses (API and website data layer) must follow a consistent JSON structure:
  - itinerary_id (string)
  - destination (string)
  - days (integer)
  - budget_level (string)
  - interests (array[string])
  - created_at (ISO timestamp)
  - day_plan: array of objects { day_number (int), activities: array of { id, name, type, description, est_duration_minutes, est_cost, start_time_optional, location { lat, lon, address_optional } } }
- Acceptance: API response validates against this schema.

FR-5 — Basic itinerary generation logic (High)  
- Implement a deterministic rule-based generator appropriate for coursework:
  - Distribute activities by interest and day
  - Respect trip length and budget level when selecting and ordering activities
  - Create reasonable time estimates and a simple daily schedule (morning/afternoon/evening)
- Acceptance: given identical inputs, service returns consistent itineraries; activities respect user interests and budget.

FR-6 — Optional enrichment via external POI API (Medium, optional)  
- Support optional integration with a public Points-of-Interest API (configurable) to fetch POI names and locations.
- The system must fall back to a local dataset or templates if external API is unavailable.
- Acceptance: when configured, enrichment populates location/address fields; when not configured, generator still works.

FR-7 — Persist generated itineraries (Medium)  
- Store generated itineraries in a lightweight local database (e.g., SQLite) with itinerary_id, inputs, result, timestamp.
- Provide API endpoints:
  - GET /api/itineraries/{id} — retrieve one
  - GET /api/itineraries — list recent (paginated)
  - DELETE /api/itineraries/{id} — delete (optional)
- Acceptance: saved itineraries can be retrieved by id.

FR-8 — Session / client-side persistence (Medium)  
- On the website, allow users to view a list of their recent generated itineraries stored in the server-side DB and/or browser local storage.
- No user account system required; use session cookie or local storage to associate recent items.
- Acceptance: recent items visible for the session.

FR-9 — Input validation & error handling (High)  
- Validate inputs on client and server:
  - Destination non-empty
  - Days within allowed range
  - Budget and interests valid values
- Return meaningful error messages and appropriate HTTP status codes.
- Acceptance: invalid inputs return clear, actionable errors.

FR-10 — Clear README and API documentation (High)  
- Provide a README that explains how to run the Flask app, run tests, configure optional API keys, and lists API endpoints with sample requests/responses.
- Acceptance: another student can run the project locally following instructions.

FR-11 — Basic UI navigation (High)  
- Website pages:
  - Home / input form
  - Itinerary result page
  - Recent itineraries page
  - About / help page
- Acceptance: user can navigate between these pages.

FR-12 — Export and share (Low)  
- Allow export of an itinerary as JSON and as simple printable HTML (or PDF via browser print).
- Acceptance: export buttons produce downloadable JSON and a print-friendly page.

FR-13 — Rate limiting & abuse protection (Low for coursework)  
- Implement a simple per-IP request throttle on the generation endpoint to avoid accidental heavy usage (e.g., 10 requests/min).
- Acceptance: endpoint rejects excessive requests with 429.

---

## Non-functional requirements

NFR-1 — Performance (High)  
- API should generate and return an itinerary within 3 seconds for normal inputs on a development machine.
- UI pages should render initial response within 1.5 seconds after server response.

NFR-2 — Availability and reliability (Medium)  
- The app should gracefully handle failures of optional external services (fallback to local data).
- Unhandled exceptions should be logged and return friendly error pages/messages to the user.

NFR-3 — Security (High)  
- Do not allow arbitrary file writes or command execution via inputs.
- Validate and sanitize all inputs to prevent injection attacks (SQL injection, XSS).
- Serve the front-end with CSRF protection for any state-changing endpoints (if forms post to the server).
- Securely store any external API keys outside source control (e.g., environment variables).

NFR-4 — Data privacy (High)  
- Do not collect personally identifiable information (PII). If any session identifiers are used, keep them minimal and expire sessions reasonably (e.g., session cookies expire after browser close or a short timeout).
- Log only necessary metadata; no detailed user tracking.

NFR-5 — Usability and accessibility (Medium)  
- UI must be usable on desktop and mobile (responsive layout).
- Follow basic accessibility practices: semantic HTML, proper labels for inputs, keyboard navigable, and color contrast sufficient for readability.

NFR-6 — Maintainability and code quality (High)  
- Codebase should be modular with clear separation: Flask app, business logic (itinerary generator), data layer, templates/static files, and tests.
- Include docstrings and inline comments for non-trivial functions.
- Use a requirements.txt or pyproject.toml to list dependencies.

NFR-7 — Testability (High)  
- Provide automated tests:
  - Unit tests for itinerary generation logic and input validation
  - Integration tests for API endpoints (e.g., using Flask test client)
- Aim for basic coverage (e.g., tests covering major paths and error handling).

NFR-8 — Portability and deployment (Medium)  
- The app must run on a typical development environment (Python 3.8+).  
- Provide simple deployment instructions for a local environment and optionally for a basic PaaS (e.g., Gunicorn + Heroku/Render) or Dockerfile.

NFR-9 — Scalability (Low)  
- Design the app so that the business logic is stateless where possible to allow straightforward horizontal scaling in the future (e.g., storing state in DB rather than server memory).
- No requirement to handle heavy production traffic.

NFR-10 — Observability and logging (Medium)  
- Log key operations with enough context to debug (request inputs, errors, external API failures) without leaking sensitive data.
- Provide a simple log file or console logging configuration for development.

NFR-11 — Extensibility (Medium)  
- The design should allow future extensions: additional activity types, multi-day constraints, user accounts, richer transport/time scheduling, or switching to a different POI source.

NFR-12 — Documentation and deliverables (High)  
- Include: README, API docs (endpoints + example JSON), design notes describing the generation algorithm, and instructions to run tests.

---

Notes and constraints for coursework scope
- The itinerary generator should be rule-based or template-driven; use of heavy external AI or paid APIs is optional and must be clearly documented.  
- Keep external dependencies minimal. Prefer SQLite and small JS/CSS libraries (optional).  
- Authentication and user accounts are out-of-scope unless you choose to implement a simple optional variant for demonstration.