Overview
- Build a lightweight web application for a small travel agency that generates personalised, day-by-day city itineraries.
- Users provide destination, trip length, budget level, and interests. The system returns a clear itinerary via:
  - A RESTful Flask API (machine-consumable JSON).
  - A responsive website (human-friendly display, printable/exportable).
- Focus: useful, actionable plans (places to visit, rough times, estimated costs, travel times) — not booking or ticketing.

Goals
- Provide fast, relevant, and personalised itineraries that reduce manual planning time for tourists.
- Expose a simple API so agency systems or partners can fetch itineraries programmatically.
- Offer an intuitive web UI for direct consumer use and agency demos.
- Maintain privacy-minimised user interactions (no mandatory accounts; optional sign-in for saving itineraries).

Scope
Included
- User inputs: destination (city), trip length (days), budget level (low/medium/high), interests (e.g., museums, food, outdoors, shopping, nightlife), optional start date and mobility constraints (e.g., slow/average/fast pace).
- Output: day-by-day itinerary in human-readable format and structured JSON:
  - Morning/afternoon/evening activities, estimated visit durations, approximate transit times between items, cost band estimates, brief descriptions and addresses, suggested time windows.
  - Optional map links and printable PDF/export.
- System components:
  - Flask-based REST API with endpoints for itinerary generation and basic health/status.
  - Frontend website with input form, results page, and share/print functionality.
  - Data integration layer using POI and transit data (third-party APIs or curated datasets).
- Basic error handling and input validation, logging, and simple analytics (number of itineraries generated).
- Localisation: English only (initial release).

Excluded (out of scope)
- Direct booking, ticket purchasing, payments, or complex travel routing (no airline/hotel booking).
- Full multi-city or complex multi-modal itinerary optimization beyond a single city visit plan.
- Advanced personalization via long-term user profiles (beyond saving a single itinerary).

Constraints
- Technical
  - Must use Flask for the API; frontend may use a lightweight JS framework or server-rendered templates.
  - Typical response time target of <3s for common requests; support up to N concurrent users depending on hosting (start target: 50 concurrent).
  - Limited integration budget: rely on free/low-cost POI sources (OpenStreetMap, public datasets) or paid APIs with quota limits.
- Data & Legal
  - Third-party data licensing and API quotas may limit completeness and freshness.
  - Privacy regulations: minimise collection of personal data; provide opt-out for analytics; comply with GDPR for users in scope.
- Team & Timeline
  - Small team (1–3 devs); MVP delivery in 8–12 weeks.
- Operational
  - Hosting on low-cost cloud (e.g., single-region VPS or managed platform) with basic backups and monitoring.

Success Criteria
Functional / Quality
- API correctness: POST /itinerary returns a complete JSON itinerary for 95% of valid requests for supported cities.
- UI delivery: Website displays the generated itinerary clearly and allows printing/export; end-to-end flow validated by manual QA.
- Performance: Median API response time < 2s; 95th percentile < 5s under expected load.
- Reliability: System uptime >= 99% in production over the first 3 months.

User / Business
- User satisfaction: average SUS-like or simplified satisfaction score >= 4/5 in initial user testing (20 users).
- Usage: >= 250 itineraries generated within the first month of launch (or an agreed baseline).
- Conversion for agency leads: simple metric (e.g., contact requests or downloads) — target > 5% of users request follow-up or save itinerary.

Operational / Security
- No incidents of data breach; logging and access controls in place for stored data.
- Minimal required test coverage for core modules (unit tests for itinerary logic; integration tests for API).

Acceptance Tests (examples)
- Given valid input for a supported city, the API returns an itinerary JSON with entries for each day equal to trip length and each day containing at least 2 activities.
- Frontend form accepts inputs, calls API, and renders a readable day-by-day plan with map links and print button.
- Invalid inputs (unknown city, zero days) produce clear error messages and HTTP 4xx responses.

Deliverables
- Flask API code, docs (endpoint spec, example requests/responses).
- Web frontend with input page and itinerary view.
- Deployment scripts and a short operations runbook (start/stop, monitoring links, API keys).