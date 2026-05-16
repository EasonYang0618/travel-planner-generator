# Requirements for City Itinerary Generator (Flask API + Website)

Scope: a coursework-level web application (Flask backend + simple frontend) that accepts user inputs (destination, trip length, budget level, interests), generates a clear day-by-day itinerary, and exposes the functionality via a REST API and a website UI. The scope assumes a small curated dataset or lightweight external place-data calls (optional) and does not require enterprise-grade features.

---

## Functional Requirements

Each requirement includes a short rationale and an acceptance criterion. Priority key: MUST (core), SHOULD (important), MAY (optional/extension).

FR1 — Input Form (Website)
- Requirement: Provide a web form where users can enter:
  - Destination (city name)
  - Trip length (number of days, integer >=1)
  - Budget level (e.g., low / medium / high)
  - Interests (one or more from a list: culture, food, outdoors, museums, nightlife, shopping, family, etc.)
- Rationale: Core user input for itinerary generation.
- Acceptance: Submitting valid inputs triggers itinerary generation and shows results; invalid inputs show inline validation messages.
- Priority: MUST

FR2 — REST API Endpoint: Create Itinerary
- Requirement: Expose a POST /api/itineraries endpoint that accepts JSON with the same fields as the web form and returns a generated itinerary in JSON.
- Rationale: Programmatic access and separation of concerns for frontend.
- Acceptance: Valid request returns HTTP 201 (or 200) and JSON with a day-by-day itinerary; invalid request returns 400 with error details.
- Priority: MUST

FR3 — REST API Endpoint: Retrieve Itinerary
- Requirement: Provide GET /api/itineraries/{id} to fetch a previously generated itinerary (if persistence implemented) or returned result for session-bound itineraries.
- Rationale: Allow users or frontend to reload or share generated itineraries.
- Acceptance: Known id returns 200 and itinerary JSON; unknown id returns 404.
- Priority: SHOULD

FR4 — Itinerary Generation Logic
- Requirement: Generate a day-by-day plan that assigns 1–6 activities per day (configurable) aligned with interests, budget, and realistic travel times between attractions; include suggested time windows and short descriptions for each activity.
- Rationale: Provide useful, realistic plans rather than unordered lists.
- Acceptance: Returned itinerary contains days numbered 1..N, each with a list of activities having: title, short description, estimated duration, recommended time-of-day, and approximate cost tier.
- Priority: MUST

FR5 — Data Source for Places/Activities
- Requirement: Use a curated local dataset (JSON/SQLite) of attractions per city for coursework; optional integration with a public places API (e.g., OpenStreetMap or a mock external API) may be provided as an extension.
- Rationale: Keep dependencies simple for coursework; allow later extension.
- Acceptance: For covered cities, activities are drawn from dataset; external API calls are configurable and documented.
- Priority: MUST

FR6 — Result Presentation (Website)
- Requirement: Present the generated itinerary in a clear, readable day-by-day format on the website, with options to view details for each activity and to download or copy the itinerary (e.g., printable view or JSON export).
- Rationale: Usable UI for tourists.
- Acceptance: Web page shows itinerary with day headings and activity cards; a “Print/Export” control is present.
- Priority: MUST

FR7 — Input Validation and Error Handling
- Requirement: Validate inputs both client-side (basic) and server-side; handle server errors gracefully and show user-friendly messages on the website and structured error responses from the API.
- Rationale: Robustness and good UX.
- Acceptance: Invalid requests return structured errors; website displays readable messages and does not crash.
- Priority: MUST

FR8 — Session or Persistence (Lightweight)
- Requirement: Store generated itineraries temporarily (in-memory or simple database) for retrieval during the session and optionally allow unique URLs for sharing (if persistence implemented).
- Rationale: Improve usability for viewing/sharing results.
- Acceptance: After generation, user can refresh page and still see itinerary (session or DB-backed); GET endpoint can return stored itinerary by id.
- Priority: SHOULD

FR9 — Filtering & Customization (Basic)
- Requirement: Allow users to re-run generation with modified constraints (e.g., change interests, adjust budget, or prefer walking vs public transport) and update itinerary accordingly.
- Rationale: Iterative user refinement.
- Acceptance: Changing parameters and re-submitting yields adjusted itineraries.
- Priority: SHOULD

FR10 — Minimal Admin/Developer Controls
- Requirement: Provide simple CLI or admin endpoint to load/update the local dataset (e.g., import JSON), and configuration for toggling external API usage.
- Rationale: Maintainability for coursework demonstration.
- Acceptance: Developer can load dataset via documented command or endpoint.
- Priority: MAY

FR11 — Basic Logging for Requests and Errors
- Requirement: Log incoming API requests and critical errors (to console or file) for debugging.
- Rationale: Troubleshooting during development.
- Acceptance: Logs include timestamp, endpoint, input summary, and error stack for exceptions.
- Priority: MUST

---

## Non-Functional Requirements

NFRs include measurable targets where appropriate. Priority: MUST / SHOULD / MAY.

NFR1 — Technology Stack
- Requirement: Implement backend with Python Flask; frontend with server-rendered templates (Jinja2) or a lightweight single-page interface (plain JS). Use SQLite or JSON for the dataset.
- Rationale: Appropriate for coursework and easy deployment.
- Priority: MUST

NFR2 — Performance
- Requirement: API should respond to valid itinerary requests within 2 seconds for local dataset lookups (average case). For external API calls, document expected additional latency.
- Rationale: Good user experience.
- Acceptance: Measured local responses average <= 2s under light load.
- Priority: SHOULD

NFR3 — Availability & Reliability
- Requirement: App should handle typical coursework/demo usage (single-digit concurrent users) without crashes; include basic retry or fail-safe behavior for transient external API failures.
- Rationale: Stable demos during evaluation.
- Priority: MUST

NFR4 — Security (Basic)
- Requirement: Sanitize and validate all inputs to prevent injection; do not enable admin/developer endpoints in production without protection; store secrets (API keys) in environment variables, not source code.
- Rationale: Basic security hygiene.
- Acceptance: No plaintext secrets in repo; input validation on server.
- Priority: MUST

NFR5 — Privacy / Data Handling
- Requirement: Do not collect personal PII; if persistence stores itineraries, avoid associating them with real user identities unless explicitly required and documented.
- Rationale: Simplicity and privacy for coursework.
- Priority: MUST

NFR6 — Usability & Accessibility
- Requirement: Website should be usable on desktop and mobile viewports, with clear visual hierarchy and accessible form controls; follow basic WCAG principles (labels for inputs, sufficient color contrast).
- Rationale: Inclusive design and demo readiness.
- Acceptance: Form inputs have labels; pages usable on 320px–1200px widths.
- Priority: SHOULD

NFR7 — Maintainability & Code Quality
- Requirement: Codebase should be organized, modular, and include README with setup/run instructions; include unit tests for core itinerary generation logic and API endpoints.
- Rationale: Demonstrable engineering practices for coursework.
- Acceptance: README explains run steps; at least 5 unit tests covering generation and validation.
- Priority: MUST

NFR8 — Logging & Observability
- Requirement: Capture request-level logs and error logs; logs should be human-readable and suitable for debugging a demo.
- Rationale: Simplify grading/debugging.
- Priority: SHOULD

NFR9 — Scalability (Minimal)
- Requirement: Design components so data source can be swapped with minimal code changes (e.g., abstract data access layer) to enable future scaling to real APIs/datasets.
- Rationale: Clean architecture for extension.
- Priority: SHOULD

NFR10 — Deployability
- Requirement: App can be started locally with a single command (e.g., flask run or a provided script) and documented dependencies (requirements.txt). Optional Dockerfile for containerized demo is a plus.
- Rationale: Ease of evaluation.
- Acceptance: Project can be launched by following README instructions; Docker optional.
- Priority: MUST

NFR11 — Documentation
- Requirement: Provide API documentation (README or simple OpenAPI/Swagger if feasible) describing endpoints, request/response schemas, and example requests.
- Rationale: Clear interface for graders and integration.
- Priority: SHOULD

NFR12 — Testing & Quality Assurance
- Requirement: Include unit tests for itinerary generator logic and integration tests for critical API endpoints. Automated test command (e.g., pytest) documented.
- Rationale: Validate correctness and support grading.
- Acceptance: Tests run via documented command and exit non-zero on failure.
- Priority: MUST

---

## Constraints and Assumptions
- The project is a coursework deliverable: keep third-party dependencies minimal and document any external APIs used.
- Dataset of attractions will cover a small set of sample cities; undefined cities should return a friendly “city not supported” response.
- No full user authentication system is required unless explicitly added as an extension.
- Geocoding/transport time estimates may be simplified (static travel time heuristics) for coursework.

---

This set of requirements is intentionally scoped for a small Flask-based coursework project while leaving room for useful extensions (external API integration, persistence, sharing).