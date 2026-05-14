# Requirements for Travel Itinerary Web App (Flask API + Website)

Brief: A small travel agency needs a web application that helps tourists generate personalised city travel itineraries. Users provide destination, trip length, budget level, and interests; the system returns a clear day-by-day itinerary. The app will expose a Flask JSON API and a simple responsive website that consumes the API.

---

## Functional requirements

Each functional requirement includes a short description, priority (Must / Should / Could), and one or more acceptance criteria that are concrete and testable.

FR1 — User input form / API endpoint to request an itinerary  
- Priority: Must  
- Description: The system must accept the following input: destination (city name), trip length (integer days, 1–14), budget level (e.g., low / medium / high), and a list of interests (e.g., museums, food, parks, nightlife).  
- Acceptance criteria:
  - Website: a form exists where a user can enter the fields above and submit. All fields validated client-side.
  - API: POST /api/itineraries accepts JSON with keys: destination, days, budget, interests. Returns 400 on invalid input.

FR2 — Generate a day-by-day itinerary  
- Priority: Must  
- Description: Produce a structured itinerary covering each day of the trip. Each day should contain 1–5 scheduled items (e.g., attractions, meals, transit notes) with approximate times or time-of-day tags (morning/afternoon/evening). Items are chosen to match interests and budget.  
- Acceptance criteria:
  - API response body includes an "itinerary" array with `days` equal to requested trip length.
  - Each day object contains at least one item with fields: title, category, estimated_duration (minutes), time_of_day, short_description.
  - Items filtered by the interests requested: at least 60% of items match the user's interests (or a meaningful fallback if few POIs available).

FR3 — Budget-aware recommendations  
- Priority: Must  
- Description: The itinerary should consider the selected budget level when choosing POIs/activities (e.g., more free/low-cost items for "low" budget).  
- Acceptance criteria:
  - Generated items include a `cost_level` tag (free / low / medium / high).
  - For "low" budget requests, at least 70% of items are free/low cost.

FR4 — Basic routing / daily travel awareness (approx.)  
- Priority: Should  
- Description: The system should avoid scheduling widely-dispersed activities back-to-back on the same day where possible (use simple clustering by neighbourhood or POI type). Exact routing/navigation not required.  
- Acceptance criteria:
  - If two items are from different neighbourhoods, the generator prefers inserting a different item in-between or scheduling them on different days when possible.
  - Unit tests demonstrating the clustering heuristic applied to a sample dataset.

FR5 — Persist and retrieve itineraries  
- Priority: Should  
- Description: Allow generated itineraries to be saved and retrieved by ID (persistent storage using SQLite or similar).  
- Acceptance criteria:
  - POST /api/itineraries returns an itinerary id when the "save" option is selected or by default.
  - GET /api/itineraries/{id} returns the saved itinerary (404 if not found).
  - Data persists across server restarts in a coursework environment.

FR6 — Website result view and printable view  
- Priority: Must  
- Description: The website must display the generated itinerary day-by-day and provide a printer-friendly version.  
- Acceptance criteria:
  - Result page lists days and items with times/descriptions.
  - A "Print / Save as PDF" button presents a condensed, printable layout.

FR7 — API documentation and sample requests  
- Priority: Should  
- Description: Provide basic API documentation (README or /api/docs) with example requests and responses.  
- Acceptance criteria:
  - README or an HTML page lists endpoints, required request fields, and example JSON responses.

FR8 — Input validation and error handling  
- Priority: Must  
- Description: Validate inputs server-side and return meaningful error messages. Handle common errors and third-party failures gracefully.  
- Acceptance criteria:
  - API returns 400 with JSON error details for missing/invalid fields.
  - If an external POI service fails, API returns 503 with a helpful message and the website shows a friendly error page.

FR9 — Optional: User feedback for itinerary adjustments  
- Priority: Could  
- Description: Allow users to mark items as "remove" or "replace" and regenerate the day's plan.  
- Acceptance criteria:
  - Website provides buttons to remove/replace an item; invoking them calls an API that returns an updated itinerary fragment.

FR10 — Admin / data seeding interface (development feature)  
- Priority: Could  
- Description: Allow the developer to seed local POI/sample data or switch between a local sample dataset and a third-party API for POIs.  
- Acceptance criteria:
  - A config or simple admin route allows toggling data source for local testing.

FR11 — Health-check endpoint  
- Priority: Should  
- Description: Expose a simple GET /api/health that returns status 200 and basic service info.  
- Acceptance criteria: Endpoint returns 200 and JSON {status: "ok", version: "x.y"}.

Data model notes (for implementation):
- Itinerary: id, destination, start_date (optional), days: [Day].
- Day: day_number, date (optional), items: [Item].
- Item: id, title, category, cost_level, estimated_duration, time_of_day, description, source (local/third-party), location/neighbourhood (optional).

---

## Non-functional requirements

NFR1 — Performance (interactive generation)  
- Requirement: Generating an itinerary for a standard request (1–7 days) should complete within 5 seconds on a typical student VM or cloud free tier.  
- Measurement: 95th percentile response time <= 5s under low load (single-user tests).

NFR2 — Availability for coursework deployment  
- Requirement: The application must be runnable locally and deployable to a simple platform (e.g., Heroku/Render) with documented steps.  
- Measurement: README includes start and deployment instructions; app starts without extra proprietary services.

NFR3 — Security basics  
- Requirement: Use HTTPS in production deployment, validate and sanitize inputs, protect against basic web vulnerabilities (XSS, CSRF, SQL injection). Secrets (API keys) must not be committed.  
- Measurement: No plaintext secrets in repo; forms protected against CSRF; prepared statements/ORM for DB access.

NFR4 — Privacy / data minimisation  
- Requirement: Do not collect or store more personal data than necessary. If user accounts are omitted, do not store identifiable personal info. Provide a short privacy note in README.  
- Measurement: Database schema and sample data do not include unnecessary personal fields.

NFR5 — Usability & accessibility  
- Requirement: Website should be responsive (works on mobile and desktop) and meet basic accessibility practices (semantic HTML, alt text, keyboard navigation).  
- Measurement: Manual checklist confirming responsive layout and ability to navigate and submit forms via keyboard; contrast > 4.5:1 for primary text.

NFR6 — Maintainability and code quality  
- Requirement: Use modular Flask app structure, separate concerns (routes, services, data access, templates), and include inline documentation. Keep complexity suitable for coursework.  
- Measurement: Code has a README, docstrings for main modules, and modules not exceeding reasonable size.

NFR7 — Testability  
- Requirement: Provide unit tests for core itinerary generation logic and API endpoint integration tests.  
- Measurement: At least a small test suite (e.g., pytest) exercising generation for different interests and invalid inputs.

NFR8 — Error logging and observability  
- Requirement: Log server errors and key events (itinerary creation, save operations) to console/file with timestamps. Include enough context to reproduce issues.  
- Measurement: Logs include error stack traces in development and structured messages for key actions.

NFR9 — Extensibility  
- Requirement: Design the POI/data access layer so it can be swapped between a local sample dataset and external APIs with minimal changes.  
- Measurement: Data access behind an interface/class with two implementations (sample vs. external).

NFR10 — Resource constraints / dependency management  
- Requirement: Keep third-party dependencies minimal and pinned (requirements.txt). The app should run within modest resource limits typical for coursework (~512MB RAM).  
- Measurement: requirements.txt provided; memory usage reasonable in simple tests.

NFR11 — Internationalisation / localisation (basic)  
- Requirement: Support at least English content. Clear separation of display strings so adding translations later is straightforward.  
- Measurement: Strings are not hard-coded into templates or logic; a single file or approach for messages.

NFR12 — License and third-party data compliance  
- Requirement: If using external POI datasets or APIs, follow their terms of use and note sources in README. If including sample data, ensure licensing permits use in coursework.  
- Measurement: README lists any external data sources and their license or API terms.

---

## Constraints and assumptions (coursework scope)

- The itinerary generator may use a simple rule-based or heuristic algorithm and a small local POI dataset for offline use. Integrating a commercial routing or optimisation engine is not required.  
- User authentication and payment processing are out of scope, unless implemented as an optional stretch goal.  
- The app must be implemented in Python using Flask for the API and server-side rendering or a small client-side script for the website.  
- Persistent storage may be SQLite to keep deployment simple.

---

If you want, I can convert these into a user-stories backlog, or produce concise acceptance-test cases for each requirement suitable for coursework marking.