# Requirements for Travel-Itinerary Web App (Flask API + Website)

Scope: a coursework-sized Flask-based web application and accompanying REST API that lets tourists generate personalised city travel itineraries from simple inputs (destination, trip length, budget level, interests). Core deliverables are a working Flask API, a responsive website front-end, basic persistence for saved itineraries, and documentation/tests.

Below the requirements are grouped and prioritized using MUST / SHOULD / COULD to keep scope realistic for coursework.

---

## Functional Requirements

### Core itinerary generation (MUST)
1. Users can submit inputs to generate an itinerary:
   - Inputs: destination (city name), trip length (days, integer ≥1), budget level (low / medium / high), interests (one or more from a predefined list such as museums, food, outdoor, nightlife, family, history, shopping).
   - Validation: destination and trip length are required; trip length is between 1 and 30; interests limited (e.g., max 5).
2. The system returns a clear day-by-day itinerary:
   - Each day contains a sequence of items (activity name, short description, suggested time or part-of-day, estimated duration).
   - Total number of days equals trip length.
   - Activities reflect selected interests and are labelled with an estimated cost category (free / cheap / moderate / expensive).
   - The itinerary includes at least one recommendation for morning/afternoon/evening per day when appropriate.
3. The generated itinerary is reproducible for the same inputs (deterministic or seed-controlled) unless “randomise” is explicitly requested.

Acceptance criteria: Valid input produces a JSON itinerary and a human-readable page showing one entry per day with activities and basic cost/duration info.

### REST API (MUST)
4. Provide an HTTP JSON API endpoint to generate itineraries:
   - POST /api/itineraries
     - Request body: { destination, days, budget, interests, (optional) language, (optional) randomize }
     - Response: 201 Created with itinerary JSON (or 200 OK) or detailed 4xx on invalid input.
5. Provide endpoint to retrieve a generated or saved itinerary:
   - GET /api/itineraries/{id}
     - Returns itinerary JSON or 404 if not found.
6. Basic API health/status endpoint:
   - GET /api/health — returns OK and basic service metadata.

### Website / UI (MUST)
7. Home / input form page:
   - A web form matching the API inputs (destination, days, budget, interests, submit).
   - Client-side validation with meaningful error messages.
8. Results page:
   - Presents the generated itinerary in a readable day-by-day format.
   - Allows navigation between days and shows activity details.
9. Persist and list saved itineraries (SHOULD):
   - Allow users to save generated itineraries to a simple datastore.
   - Provide a page to list saved itineraries and view details.
   - Persistence can be anonymous (no user accounts); items identified by generated ID/link.
10. Export (SHOULD/COULD):
    - Allow export of an itinerary as JSON and as a printable HTML page (PDF via browser print).
    - Optionally allow export as simple downloadable text or CSV.

### Input validation & error handling (MUST)
11. Validate inputs server-side and return informative error messages (JSON for API / inline messages for website).
12. Graceful handling of external failures or missing data: return user-friendly fallback messages and log errors.

### Data model & storage (SHOULD)
13. Use a lightweight datastore suitable for coursework (e.g., SQLite) to store saved itineraries and minimal metadata (id, destination, creation time, input params, itinerary JSON).
14. The app can function without persistence (i.e., one-off generation) — saving is optional but preferred.

### Logging, monitoring & audit (COULD)
15. Basic request logging for debugging and grading (timestamp, endpoint, status code).
16. Simple error logging (stack traces in development only).

### Testing & documentation (MUST)
17. Provide:
    - README with setup/run instructions.
    - API documentation (endpoints, request & response examples).
    - A small suite of automated tests (unit tests for core functions and at least one integration test calling the API).
18. Provide sample requests (curl or Postman collection) demonstrating typical usage.

---

## Non-functional Requirements

### Performance (MUST)
1. Typical API response time for itinerary generation should be reasonable for coursework: average under 3 seconds on a developer machine for basic inputs.
2. Page load for the main pages (home, results) should render within 2–4 seconds on a standard student laptop / browser.

### Reliability & Availability (SHOULD)
3. The app runs reliably for the expected minimal usage (tens of concurrent users are not required). Target basic uptime in a single-process deployment; graceful failure on errors.

### Security (MUST)
4. Input sanitisation to prevent injection (SQL injection, XSS). Use parameterized queries and escape output in templates.
5. Protect POST forms with CSRF tokens (Flask-WTF or similar) for the website.
6. Do not require production-level auth for coursework; if credentials or secrets are used, they must be configurable via environment variables and not hard-coded.
7. If deployed publicly, run over HTTPS (documented requirement).

### Privacy & Data protection (MUST/SHOULD)
8. If storing saved itineraries, treat them as non-sensitive; do not collect personal data unless implementing optional user accounts. If user accounts are implemented, store passwords hashed (bcrypt/argon2).
9. Provide a simple privacy note in the README explaining what is stored.

### Usability & Accessibility (SHOULD)
10. The website must be responsive (usable on desktop and mobile) and follow basic accessibility practices (semantic HTML, labels for form controls, keyboard navigation). Aim for WCAG AA where feasible.
11. Provide clear inline help text for inputs (e.g., examples for destination format).

### Maintainability (MUST)
12. Code should be modular and documented enough for graders:
    - Separate API logic from presentation.
    - Use a simple, well-known project structure for Flask apps.
13. Include comments and a short design doc or architecture explanation (one page).

### Portability & Compatibility (MUST)
14. The app must run with Python 3.8+ and use Flask; dependencies listed in requirements.txt or pyproject.toml.
15. Use only freely available third-party libraries suitable for coursework (no proprietary services).

### Scalability (COULD)
16. Not required to support high scale. Design should not prevent future scaling (e.g., avoid tight coupling between storage layer and app logic).

### Testing & Quality (MUST)
17. Include automated tests (unit tests for itinerary generation logic and at least one API endpoint test). Aim for a small but meaningful coverage (e.g., key edge cases).
18. Provide instructions on how to run tests.

### Documentation (MUST)
19. README must include:
    - Setup and run steps.
    - How to call the API (examples).
    - Any configuration (database, ports, env vars).
    - Limitations and known issues.

---

## Constraints & Assumptions
- Technology: Flask for backend + Jinja templates (or minimal frontend JS) for the website. SQLite is acceptable for persistence.
- External data: Itinerary content can be generated from a local dataset or simple heuristics; linking to external APIs (maps, POI) is optional and should be documented if used.
- Authentication: Not required for core functionality. If implemented, keep it optional and minimal.
- Time/budget: Designed to be achievable within a typical coursework timeframe.

---

If you want, I can convert these into a prioritized backlog (user stories) or produce example API request/response schemas to include in the project documentation.