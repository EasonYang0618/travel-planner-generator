# Requirements for Travel Itinerary Web Application

Scope note: these requirements are sized for a coursework project implemented with Flask, a small relational database (SQLite), and a simple front-end (HTML/CSS/JavaScript). The system generates personalised city travel itineraries from a curated POI dataset. The following does not require payment/booking integration or advanced AI services.

---

## Actors
- Tourist (end user): submits trip parameters and views/exports itineraries.
- Registered user: tourist who can save and retrieve itineraries across sessions.
- Admin (agency staff): manages attractions/POI data used by the generator.
- System (API + website): provides itinerary generation, persistence and presentation.

---

## Assumptions and Constraints
- The application runs as a Flask app with a relational DB (SQLite for coursework).
- POIs are stored in an internal database maintained by admins; no mandatory external API integrations.
- Trip length is limited to a reasonable maximum (e.g., 1–14 days).
- Budget level is modelled as a small set of categories (e.g., low / mid / high).
- Interests are selected from a predefined list (e.g., culture, food, outdoors, shopping).
- No real-money transactions, no third-party booking.

---

## OUT OF SCOPE (for coursework)
- Real-time booking, payments, or third‑party booking APIs.
- Complex route optimization (e.g., TSP over a city map).
- Full production-grade scalability (beyond local or small cloud deployment).
- Advanced recommendation engines or ML models (optional extra-credit).

---

## Functional Requirements

Each requirement has: brief description, priority (Must / Should / Could), and acceptance criteria.

FR-1: Itinerary generation (web form)
- Description: The website provides a form where a user enters: destination city, trip start date (or start day), trip length (days), budget level, and one or more interests; upon submission the system generates a day-by-day itinerary.
- Priority: Must
- Acceptance criteria:
  - Submitting valid form data returns a clear itinerary covering each day.
  - Each day contains a sequence of activities (POI visits, meal suggestions, free time blocks) with approximate times and short descriptions.
  - The output is displayed on the website within acceptable response time (see NFRs).

FR-2: Itinerary generation (API)
- Description: The system exposes a REST API endpoint to request itinerary generation using JSON input and returning JSON output.
- Priority: Must
- Acceptance criteria:
  - POST /api/itineraries (or equivalent) accepts JSON with fields: destination, start_date (or start_day), length_days, budget, interests[].
  - Response JSON includes: itinerary_id (if persisted), day-wise list of activities, total estimated daily cost range, and metadata (generation_time, algorithm_version).
  - API returns appropriate HTTP status codes (200 for success, 4xx for client errors).

FR-3: Input validation and friendly error messages
- Description: All user inputs (form and API) are validated and invalid input returns clear, actionable errors.
- Priority: Must
- Acceptance criteria:
  - Empty/invalid required fields result in client-visible errors (web) and structured error responses (JSON - field and message).
  - Trip length outside allowed range returns a validation error.

FR-4: Interests and destination selection
- Description: The UI and API accept interests from a predefined set and a supported list of destinations (or free-text destination with fallback).
- Priority: Must
- Acceptance criteria:
  - Web form shows selectable interests (checkboxes/tags).
  - API validates interest values; unknown interests cause a 400 error with message.
  - The system supports at least 3–5 sample destinations pre-populated for testing.

FR-5: Persist generated itineraries (session and optional account)
- Description: Generated itineraries can be persisted for the user: store per session (short-term) and for registered users long-term.
- Priority: Should
- Acceptance criteria:
  - Anonymous users: recent generated itinerary is saved in session and accessible in the same browser session.
  - Registered users: can save and later retrieve a list of their itineraries.
  - The API supports GET /api/itineraries/{id} for retrieving a stored itinerary (with access control).

FR-6: User registration and authentication (basic)
- Description: Provide a simple register/login/logout flow (email/username + password) so users can save itineraries across sessions.
- Priority: Could (should if persistent storage is required)
- Acceptance criteria:
  - Users can create an account and log in; passwords are stored hashed.
  - Authenticated endpoints require a session cookie or token (for coursework, Flask sessions are acceptable).
  - Attempts to access another user's saved itinerary return 403 Forbidden.

FR-7: Admin POI management
- Description: An admin interface (web pages restricted to admin accounts) to create, edit, delete POIs and tag them by interest, cost level, opening hours.
- Priority: Should
- Acceptance criteria:
  - Admin can add or update POI name, description, category/interest tags, estimated visit duration, approximate cost tier, and location (address or coordinates).
  - Changes are used by the generator within a reasonable time (immediate for the scope).

FR-8: Attraction details and simple search
- Description: Users can view details for POIs included in an itinerary and perform a simple search/filter of POIs by interest, cost, name.
- Priority: Should
- Acceptance criteria:
  - Clicking a POI in the itinerary opens a detail view (modal or page) with description, suggested visit duration, address, opening hours (if present).
  - A search box filters POIs by name/interest on a listing page.

FR-9: Export and print
- Description: Users can export an itinerary as JSON and as a printable HTML page.
- Priority: Should
- Acceptance criteria:
  - On the web UI there is a "Download JSON" button yielding the itinerary JSON.
  - There is a "Print" / "Printable view" option that renders a print-friendly HTML page.

FR-10: Present itinerary with maps/links
- Description: Each POI in the itinerary includes a link to a map (e.g., Google Maps URL) and clear address or location text.
- Priority: Should
- Acceptance criteria:
  - POI entries include a clickable external map link or an embedded small map (optional).
  - Map links open in a new tab/window.

FR-11: API documentation and examples
- Description: Provide concise API documentation (Swagger/OpenAPI or README examples) for the itinerary endpoint and retrieval endpoints.
- Priority: Must
- Acceptance criteria:
  - README or /api/docs endpoint describes request/response JSON schemas and example requests.

FR-12: Logging, errors, and monitoring hooks
- Description: The application logs key events (generations, errors, auth events) and surfaces user-friendly error pages.
- Priority: Must
- Acceptance criteria:
  - Server logs record generation requests with timestamp, destination, and outcome.
  - Web UI shows a friendly error page on unhandled exceptions and returns 500 status.

FR-13: Automated tests for core functionality
- Description: Include unit/integration tests for itinerary generation logic, API endpoints and at least one end-to-end flow.
- Priority: Must
- Acceptance criteria:
  - Tests cover generation for at least 3 example inputs and assert the existence of day entries and POIs.
  - Tests can be run with a single command (e.g., pytest).

---

## Non-Functional Requirements

Performance
- NFR-1 Response time: The system must generate and return an itinerary for typical requests within 5 seconds on a local dev machine or modest cloud instance.
- NFR-2 Concurrency: The app should handle basic concurrent use (at least several simultaneous users; target: 10 concurrent generation requests without failure).

Reliability & Availability
- NFR-3 Error tolerance: The generator should fail gracefully with meaningful error messages; no crash on malformed input.
- NFR-4 Persistence durability: Saved itineraries must survive server restarts (use DB).

Security
- NFR-5 Transport security: The application must be deployable behind HTTPS; for development HTTP is acceptable.
- NFR-6 Authentication and credentials: Passwords must be securely hashed (e.g., bcrypt). No plaintext password storage.
- NFR-7 Input sanitization: All user inputs must be sanitized/escaped to prevent injection and XSS in the UI.
- NFR-8 Access control: Only admins can access POI management. Users can only access their saved itineraries.

Privacy & Data protection
- NFR-9 Minimal data: Store only necessary PII (email/username); provide a way to delete a user and their saved itineraries (for coursework, an admin script or UI).
- NFR-10 Compliance: Document how personal data is stored and offer deletion (simple GDPR-aware behavior).

Usability & Accessibility
- NFR-11 Usability: Common tasks (generate itinerary, view results) should be achievable in ≤ 3 clicks.
- NFR-12 Accessibility: Follow basic accessibility guidelines (semantic HTML, alt text for images, keyboard navigable forms). Aim for WCAG AA where practicable.

Maintainability & Code quality
- NFR-13 Modularity: Code should be organized (Flask blueprints or similar) with clear separation of concerns: API, UI, data layer, generation logic.
- NFR-14 Tests: Maintain automated tests for core business logic with a target coverage for core modules (e.g., 60–80% for generation logic).
- NFR-15 Documentation: Provide README with setup, run, test instructions and API documentation.

Compatibility & Portability
- NFR-16 Browser support: Works on the latest versions of Chrome, Firefox and a modern mobile browser.
- NFR-17 Deployment: Deployable to common PaaS for coursework (Heroku, Railway, or a simple VPS). Database should be SQLite in dev; design should allow swapping to Postgres for deployment.

Scalability (low priority)
- NFR-18 Scalable design: No requirement for immediate horizontal scale, but architecture should not tightly couple generation logic to a single monolithic component; modular design preferred.

Logging & Monitoring
- NFR-19 Logs: Application logs must include timestamped events for errors and itinerary generation requests.
- NFR-20 Metrics (optional): Provide basic metrics/endpoints (count of generation requests, avg response time) if feasible.

Internationalization
- NFR-21 Language: UI texts in English. Design should allow adding other languages later (separation of strings).

Data quality and content
- NFR-22 POI dataset: POIs should have sufficient metadata (category, cost tier, duration, address) so generated itineraries can be meaningful.
- NFR-23 Content freshness: Admins must be able to update POI details; updates are reflected in new itineraries immediately.

---

## Acceptance / Success Criteria (project-level)
- A user (anonymous or registered) can generate a 3–5 day itinerary for at least three sample destinations via the website and via the API.
- The generated itinerary is coherent: day-by-day, includes POIs matching selected interests, includes times/durations and map links.
- The application includes basic admin POI management, validation, error handling, API docs, and tests that pass.
- The project is runnable locally via documented steps and can be deployed to a simple PaaS.

---

If you want, I can convert these into user stories, produce a minimal API contract (example request/response JSON schemas), or produce a prioritized development plan with sprint tasks suitable for coursework. Which would you prefer next?