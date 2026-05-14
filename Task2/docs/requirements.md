# Requirements

This document lists the functional and non-functional requirements for a coursework-scale Flask web application and API that generates personalised city travel itineraries. Requirements are prioritised and include acceptance criteria where useful. The scope is suitable for a student project: a Flask backend, a simple frontend (Jinja2 + HTML/CSS/JS or Bootstrap), and a small local dataset (or mocked external API).

---

## Functional requirements

Each requirement has an ID, a short description, rationale, and acceptance criteria.

FR-1: Landing page and instructions
- Description: Provide a landing/home page that explains the service and shows an input form or a prominent link to the itinerary generator.
- Rationale: Help users understand and access the tool quickly.
- Acceptance criteria: Visiting `/` displays brief instructions and a link/button to the generator.

FR-2: Trip input form (website)
- Description: A web form where users enter:
  - Destination city (text)
  - Trip length (number of days, integer >=1 and <=14)
  - Budget level (e.g., low / medium / high)
  - Interests (multi-select: e.g., culture, food, outdoor, shopping, nightlife, museums)
  - Optional: start date (date)
- Rationale: Collect parameters needed to create an itinerary.
- Acceptance criteria: Form validates required fields client- and server-side and posts to the backend.

FR-3: RESTful API endpoint for itinerary generation
- Description: POST /api/itinerary accepts JSON payload with the same fields as the web form and returns a generated itinerary in JSON.
- Rationale: Separate API layer for programmatic access and to enable the website to consume the service.
- Acceptance criteria: Valid request returns HTTP 200 JSON with clear day-by-day structure; invalid request returns 4xx with error message.

FR-4: Itinerary generation engine (core)
- Description: Generate a day-by-day itinerary based on inputs:
  - Distribute points-of-interest (POIs) across days according to trip length.
  - Match POIs to selected interests and budget level.
  - Suggest timings (morning/afternoon/evening) and approximate durations for each activity.
- Rationale: Provide meaningful, personalised itineraries.
- Acceptance criteria: Generated itinerary contains an entry for each day from 1..n, each day lists 2–6 activities, and activities correspond to selected interests.

FR-5: POI data source
- Description: Use a local dataset (JSON/SQLite) of sample POIs for several cities. Each POI includes name, category/tags, estimated cost level, opening hours (optional), brief description, and coordinates (optional).
- Rationale: Keep external dependencies minimal for coursework.
- Acceptance criteria: Engine uses the dataset to select POIs; dataset is packaged with the project or seeded on setup.

FR-6: Budget-aware suggestions
- Description: Map the budget level to appropriate POIs (e.g., low -> more free/cheap activities; high -> include paid experiences).
- Rationale: Keep recommendations realistic and aligned with user constraints.
- Acceptance criteria: ≥80% of suggested POIs match the budget tier mapping rules.

FR-7: Interest matching and prioritisation
- Description: If user selects multiple interests, ensure suggestions reflect a balanced mix or allow a primary interest to receive priority.
- Rationale: Personalisation.
- Acceptance criteria: For single-interest requests, ≥70% of activities match that interest; for multi-interest, activities cover at least two selected interests.

FR-8: Output formats (website + API)
- Description: Display the itinerary on the website as a readable day-by-day plan with clear headings, times, brief descriptions, and an estimated daily cost summary. The API returns a structured JSON representation of the same content. Optionally support JSON export and a simple PDF or printable view.
- Rationale: Usable UI and machine-readable output.
- Acceptance criteria: Website view shows day headers, activities, times, and costs; API returns JSON keys: days[], activities[], times, cost_estimate.

FR-9: Download or export itinerary
- Description (optional / nice-to-have): Allow users to download itinerary as JSON (required) and optionally as a printable HTML/PDF.
- Rationale: Users often want to save or print itineraries.
- Acceptance criteria: Button downloads JSON; printable view is accessible via “Print” or “Save as PDF”.

FR-10: Error handling and user feedback
- Description: Provide clear error messages for invalid inputs, missing data for a destination, or server errors.
- Rationale: Improve usability and debugging.
- Acceptance criteria: Invalid form shows inline errors; API returns JSON error with message and HTTP status code.

FR-11: Simple persistence of saved itineraries (optional)
- Description: Allow users to save generated itineraries to a local database (SQLite) under a generated identifier (no full user account required). Provide a page to list saved itineraries and view them.
- Rationale: Useful feature without heavy auth complexity.
- Acceptance criteria: Saved itinerary is retrievable by ID and listed on a "Saved itineraries" page.

FR-12: Basic admin/maintenance for dataset (optional)
- Description: Provide a simple script or protected route to import/refresh the local POI dataset from a JSON file.
- Rationale: Make it easy to update sample data for coursework demonstration.
- Acceptance criteria: Dataset can be reseeded via a script or admin-only endpoint.

FR-13: Frontend usability
- Description: Use responsive layout (desktop + mobile), clear typography, and simple navigation. Use client-side form validation and helpful placeholders.
- Rationale: Acceptable UX for coursework.
- Acceptance criteria: Pages are viewable on narrow screens; required fields flagged before submit.

FR-14: Basic logging
- Description: Log key events (requests to /api/itinerary, errors) to console or a file for debugging.
- Rationale: Aid development and assessment.
- Acceptance criteria: Server logs include timestamped entries for requests and exceptions.

FR-15: Automated tests for core logic
- Description: Provide unit tests for itinerary generation logic (e.g., distribution of POIs across days, interest matching).
- Rationale: Demonstrate correctness and support maintainability.
- Acceptance criteria: Test suite runs locally with tests for the main generation functions.

---

## Non-functional requirements

NFR-1: Technology stack and constraints
- Requirement: Use Flask (Python) for the backend; Jinja2 templates and minimal JS (or Bootstrap) for the frontend; local SQLite or JSON file for data.
- Rationale: Keep scope manageable for coursework.
- Success criteria: Project runs locally with instructions; no paid external services required.

NFR-2: Performance
- Requirement: Typical itinerary generation request should complete within 3 seconds on a modest development machine.
- Rationale: Acceptable responsiveness for interactive use.
- Measurement: Average response time under light load measured during demonstration.

NFR-3: Scalability (coursework-level)
- Requirement: Design code modularly to allow future replacement of local dataset with an external API or larger DB without major rewrites.
- Rationale: Good engineering practice.
- Success criteria: Data access isolated in a repository/service layer.

NFR-4: Reliability and availability
- Requirement: Application should start reliably and handle missing data gracefully (return informative errors rather than crashing).
- Rationale: Robust demo behavior.
- Success criteria: Known errors handled and logged; app does not crash on malformed requests.

NFR-5: Security (basic)
- Requirement: Prevent common web vulnerabilities relevant to coursework:
  - Validate and sanitize user inputs server-side.
  - Use Flask CSRF protection for forms.
  - Escape output in templates to avoid XSS.
  - Avoid storing secrets in source; use configuration/local env vars.
- Rationale: Minimal security hygiene.
- Success criteria: No obvious XSS/CSRF issues in demo; inputs validated.

NFR-6: Privacy and data handling
- Requirement: If saving itineraries, store only the itinerary data and minimal metadata (timestamp). Do not collect or store sensitive personal data.
- Rationale: Ethical handling of user data in coursework.
- Success criteria: Database schema contains no PII fields by default.

NFR-7: Maintainability and code quality
- Requirement: Code should be modular, documented, and follow PEP8 where reasonable. Provide a README with setup and run instructions.
- Rationale: Facilitate grading and future changes.
- Success criteria: README explains how to run the app and tests; code organized into routes, services, models, templates.

NFR-8: Testability
- Requirement: Provide automated tests (unit tests for generation logic, basic integration tests for API endpoints).
- Rationale: Demonstrate correctness and enable regression checking.
- Success criteria: Tests runnable with a single command (e.g., pytest) and pass.

NFR-9: Portability and deployment
- Requirement: The app must run on a local development machine and be easily containerisable (Dockerfile optional). Use only commonly available Python packages.
- Rationale: Simplifies demonstration and assessment.
- Success criteria: Setup via pip/venv or Docker documented in README.

NFR-10: Usability and accessibility
- Requirement: UI should be readable, keyboard-navigable, and conform to basic accessibility practices (semantic HTML, alt text for images if used).
- Rationale: Improve inclusivity and user experience.
- Success criteria: Pages usable without heavy scrolling; form fields labelled.

NFR-11: Documentation
- Requirement: Provide README describing system architecture, how the itinerary is generated (brief algorithm description), API specification for endpoints and sample requests/responses, and instructions to run tests.
- Rationale: Assist reviewers and instructors.
- Success criteria: README includes sample curl/postman request and example JSON output.

NFR-12: Logging and observability
- Requirement: Provide server-side logs for requests and errors; log level configurable via environment.
- Rationale: Easier debugging during coursework demonstration.
- Success criteria: Logs are produced on startup and on errors.

NFR-13: Acceptable accuracy for recommendations
- Requirement: The itinerary generator may be heuristic-based; results should be sensible (no gross mismatches like suggesting “ski resort” for a summer beach city unless explicitly tagged).
- Rationale: Practical realism for demo.
- Success criteria: Manual inspection of 5 sample itineraries shows recommendations are relevant.

---

## Prioritisation (suggested for coursework)

- Must-have (MVP): FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-8, FR-10, FR-13, NFR-1..NFR-4, NFR-5..NFR-8, NFR-11.
- Nice-to-have: FR-9, FR-11, FR-12, FR-14, NFR-9, NFR-10, NFR-12, NFR-13.

---

## Example minimal acceptance test cases

1. POST /api/itinerary with {destination: "Paris", days: 3, budget: "medium", interests: ["museums","food"]} returns HTTP 200 and JSON with 3 days, each with activities matching “museums” or “food”.
2. Submitting the web form for the same input shows a readable day-by-day itinerary page within 3 seconds.
3. Invalid input (days = 0) shows validation error (400 + message for API; inline UI error for web).

---

This set of requirements aims to keep the project achievable within a coursework timeline while demonstrating full-stack design, a REST API, data-driven recommendation logic, and attention to quality attributes.