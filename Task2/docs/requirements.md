# Requirements Specification

Project: City Travel Itinerary Generator — Flask API + Website  
Scope: Coursework-level web application (Flask backend + simple frontend) that accepts destination, trip length, budget level, and interests and returns a clear day-by-day itinerary. External-service usage is optional and limited (e.g., static bundled datasets or optional API keys). Focus is on a working prototype rather than production-grade travel recommendation complexity.

---

## Functional requirements

Each requirement has: ID, brief description, priority (Must / Should / Could), and acceptance criteria.

### F1 — User input form (website)
- Description: Provide a web UI form where users enter:
  - destination (city name)
  - trip length (integer days)
  - budget level (e.g., low / medium / high)
  - interests (one or more from a predefined list, e.g., culture, food, outdoors, museums, nightlife)
  - optional: start date (optional)
- Priority: Must
- Acceptance criteria:
  - Form validates required fields client- and server-side.
  - Trip length restricted to a sensible range (1–30).
  - Interests selected from predefined options.
  - On submit, form posts to backend and triggers itinerary generation.

### F2 — Flask API endpoint (JSON)
- Description: Provide an API endpoint (e.g., POST /api/itineraries) that accepts the same inputs as the web form and returns a generated itinerary in JSON.
- Priority: Must
- Acceptance criteria:
  - Endpoint accepts JSON request body with specified fields.
  - Returns HTTP 200 with JSON payload on success, or appropriate 4xx/5xx with error message.
  - Response schema documented (see acceptance example).

### F3 — Day-by-day itinerary generation
- Description: Generate a day-by-day itinerary for the requested number of days based on destination, budget, and interests.
- Priority: Must
- Acceptance criteria:
  - Output contains an entry for each day (1..N) with 3–6 activities or items per day (depending on trip length and "pace").
  - Each activity includes a title, short description, estimated duration (e.g., 1.5h), and suggested time of day (morning/afternoon/evening).
  - If travel time between activities is relevant, include approximate transit suggestions or links (e.g., walking 15m, metro line).

### F4 — Budget-aware recommendations
- Description: Tailor activity and venue suggestions to the selected budget level (low/medium/high).
- Priority: Must
- Acceptance criteria:
  - Generated activities include budget-appropriate types (e.g., free/low-cost sights for low budget; paid experiences for higher budgets).
  - Each activity includes an approximate cost category (Free / $ / $$ / $$$).

### F5 — Interest-matching logic
- Description: Prioritise activities that match selected interests.
- Priority: Must
- Acceptance criteria:
  - At least 60% of activities align with one or more user-selected interests.
  - Activities unrelated to chosen interests are marked as "optional" or less prominent.

### F6 — Simple data source layer
- Description: Use a compact, local dataset (CSV/JSON/SQLite) of activities/POIs for a set of example cities bundled with the app. Provide clear integration points for optional external APIs.
- Priority: Must
- Acceptance criteria:
  - App runs without external API keys using bundled dataset.
  - Code includes an adapter layer to plug in external data sources (e.g., third-party place APIs) later.

### F7 — Web presentation of itinerary
- Description: Display generated itinerary on the website in a clear, readable day-by-day format with headings, activity details, and simple visual cues (duration, cost).
- Priority: Must
- Acceptance criteria:
  - Web page shows days as separate sections.
  - Each activity shows title, description, duration, cost category, and optional map link.
  - Page is usable on desktop and mobile (responsive layout).

### F8 — Download / export (JSON)
- Description: Allow users to download the generated itinerary as a JSON file.
- Priority: Should
- Acceptance criteria:
  - A download button provides the JSON representation of the current itinerary.
  - JSON matches the API response schema.

### F9 — Error handling and user feedback
- Description: Provide clear error messages for invalid inputs and generation failures (e.g., unknown destination, internal error).
- Priority: Must
- Acceptance criteria:
  - Validation errors return informative messages on both web and API.
  - Unknown or unsupported destinations return a friendly error and, if possible, a short list of supported nearby cities.

### F10 — Save itinerary to a simple persistent store (optional user session)
- Description: Allow users to save or revisit itineraries stored in a lightweight DB (e.g., SQLite) tied to an anonymous session or a short identifier.
- Priority: Should
- Acceptance criteria:
  - User can save an itinerary and receive a unique URL or identifier to reload it.
  - Saved items persist across server restarts (using SQLite or file-based storage).

### F11 — Regenerate & tweak
- Description: Provide controls to regenerate the itinerary (same inputs) and optionally tweak parameters (e.g., change pace or remove/add activities) and re-generate.
- Priority: Should
- Acceptance criteria:
  - "Regenerate" button produces a different valid itinerary.
  - Users can remove an activity client-side and request a rebalanced itinerary.

### F12 — Usage / dev documentation and API spec
- Description: Provide a README with setup, run, and API usage instructions and an API schema example (request/response).
- Priority: Must
- Acceptance criteria:
  - README includes steps to run the Flask app locally, sample API request, and explanation of dataset/configuration.
  - API endpoint documented with an example JSON request and response.

---

## Non-functional requirements

These define system qualities, constraints, and acceptance metrics suitable for a coursework project.

### N1 — Performance (API response time)
- Requirement: The API should generate and return an itinerary for a typical request within 2 seconds on a modest developer machine (e.g., 2 CPU cores, 2GB RAM).
- Rationale: Good user experience for a small dataset and logic.

### N2 — Availability
- Requirement: The application should be runnable locally and capable of continuous operation on a single server with minimal downtime for the coursework demo.
- Rationale: Demonstration must be reliable.

### N3 — Scalability (design)
- Requirement: Design should separate data, generation logic, and presentation so future scaling (larger datasets or external services) is straightforward.
- Rationale: Keep code modular and maintainable.

### N4 — Security: transport and input validation
- Requirement: Serve the web UI over HTTPS in deployment scenarios that support it. Validate and sanitize all user inputs to prevent injection attacks.
- Acceptance criteria:
  - No raw SQL concatenation; use parameterized queries (if DB used).
  - Server-side validation mirrors client validation.

### N5 — Privacy & data minimisation
- Requirement: Do not collect or store personal information by default. If saving itineraries, store only the request parameters and generated itinerary, not identifiable personal data.
- Rationale: Minimize privacy risk for a small coursework app.

### N6 — Maintainability & code quality
- Requirement: Project should be organized with clear modules (routes, services/generation logic, data access, templates). Include inline comments and a short developer guide.
- Acceptance criteria:
  - Unit tests for core generation logic.
  - Code linting or adherence to PEP8 style where practical.

### N7 — Testability
- Requirement: Core itinerary generation logic must be unit-testable. Provide automated tests for at least the generation module and API endpoints.
- Acceptance criteria:
  - Automated tests covering key rules with target coverage of ~70% for core modules.

### N8 — Error logging and diagnostics
- Requirement: Log server-side errors and key events to a file or console with sufficient detail to reproduce issues.
- Acceptance criteria:
  - Unhandled exceptions are logged with stack traces.
  - Logs include request identifiers for correlation.

### N9 — Usability
- Requirement: The website should provide a clean, simple UX: single page for input and result, clear calls-to-action, and readable itinerary layout.
- Acceptance criteria:
  - New user can create and view an itinerary within three clicks/steps.

### N10 — Accessibility (basic)
- Requirement: Follow basic accessibility practices (semantic HTML, labels for form fields, sufficient color contrast).
- Acceptance criteria:
  - Form fields have labels; page is navigable by keyboard; alt text provided for non-critical images.

### N11 — Portability / deployment
- Requirement: The app should be runnable locally using a documented virtual environment (venv) and a single command (e.g., flask run or a provided script). Optionally deployable to a simple PaaS (Heroku-like) without heavy changes.
- Acceptance criteria:
  - README includes requirements.txt and instructions; app can be started on a fresh environment.

### N12 — Rate limiting & abuse protection (optional)
- Requirement: Implement simple rate limiting or throttling for the API to prevent accidental overload during demos (e.g., 60 requests per minute per IP).
- Priority: Could
- Acceptance criteria:
  - Basic in-app rate limiting (e.g., Flask extension or middleware) configurable for demo runs.

---

## Constraints and assumptions
- The app is intended as a coursework prototype, not a production travel platform.
- The initial dataset will include a limited number of sample cities sufficient for demo purposes. Integration with live third-party APIs is optional and should be configurable via API keys.
- No user authentication is required for the base scope; persistent saves are anonymous (session or identifier-based).
- Mapping or routing functionality will consist of simple external links (e.g., Google Maps URL) rather than embedded, interactive maps (optional enhancement).

---

## Example API request/response (informal)
Request:
{
  "destination": "Lisbon",
  "days": 3,
  "budget": "medium",
  "interests": ["food", "culture"],
  "start_date": "2026-07-10"  // optional
}

Response (high-level):
{
  "destination": "Lisbon",
  "days": 3,
  "itinerary": [
    {
      "day": 1,
      "date": "2026-07-10",
      "activities": [
        {"title": "Belém Tower", "description": "...", "duration_hours": 1.5, "time_of_day": "morning", "cost": "$", "map_link": "..."},
        ...
      ]
    },
    ...
  ],
  "generated_at": "...",
  "notes": "Estimated costs are indicative."
}

---

These requirements are scoped to enable a complete coursework implementation: a Flask backend exposing a JSON API plus a simple website front-end, with clear acceptance criteria and modest non-functional targets.