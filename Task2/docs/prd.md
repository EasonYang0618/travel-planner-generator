Overview
A lightweight web application that enables tourists to generate personalised, day-by-day city itineraries. Users submit destination, trip length, budget level, and interests; the system returns a clear, actionable itinerary via a Flask API and a simple website. The product is geared toward a small travel agency that wants to offer fast, custom itineraries to customers without heavy operational overhead.

Goals
- Core: Produce relevant, realistic day-by-day itineraries tailored to destination, length, budget, and interests.
- Delivery: Expose itinerary generation via a documented Flask REST API and a responsive website UI.
- Usability: Present itineraries that are easy to read, include times/locations and estimated costs, and can be edited or saved by users.
- Business: Increase customer engagement and lead generation for the travel agency (e.g., contact/booking inquiries from itinerary pages).
- Maintainability: Be deployable and maintainable by a small team with modest infrastructure costs.

Scope
In-scope
- Inputs: destination (city), trip length (number of days), budget level (e.g., low/medium/high), interests (multi-select: culture, food, outdoors, nightlife, family, shopping, museums, etc.).
- Outputs: day-by-day itinerary with ordered activities per day, estimated times/durations, travel time approximations, estimated per-activity and total costs, short descriptions, and location links.
- Delivery channels:
  - Flask REST API: endpoint(s) to generate itineraries and fetch/save user itineraries.
  - Website: single-page or multi-page responsive interface to input parameters, display results, and allow saving/contacting the agency.
- Basic user flows:
  - Anonymous generation of itineraries.
  - Save or email itinerary (optional lightweight storage).
  - Admin/agency view to see saved itineraries/contacts.
- Business logic:
  - Budget mapping to activity types/cost ranges.
  - Simple routing constraints: reasonable daily schedules, opening-hours awareness where available, travel time heuristics.
- Minimal persistence: store saved itineraries and user-submitted contact requests.
- Basic logging and usage metrics for analytics.

Out of scope (initial release)
- Full booking engine or payment processing.
- Deep personalization (user history, AI-chat planning).
- Complex route optimization with real-time traffic.
- Large-scale multi-city itineraries or multi-stop routing.
- Enterprise-grade localization or multi-language support beyond basic translations.

Constraints
Technical
- Small team and limited hosting budget: target low-cost VPS/cloud tier; use Flask, simple relational DB (SQLite/Postgres), and lightweight front-end (HTML/CSS/JS).
- Limited third-party API budget: prefer open data (OpenStreetMap, public POI datasets) or optionally paid Places APIs behind feature flags.
- Response-time goal: generation should be fast for typical requests; complex lookups must not block the UI. Use caching for popular destinations.

Data & Legal
- POI and map data licensing must be respected (OSM license, or paid API terms).
- No stored personal data beyond contact info; comply with basic privacy practices (data minimization).

Operational
- Target small scale: initial concurrency and throughput modest (hundreds of users/day).
- Offline availability and high availability beyond 99% SLA are not required for launch.

Security & Privacy
- Input validation and basic protections against injection.
- Secure storage of contact info; no sensitive financial data stored.
- Rate limiting to protect API.

Success Criteria
Functional acceptance
- Correctness: For 95% of test cases (representative cities + interest combinations), the API returns a complete itinerary that:
  - Covers the requested number of days.
  - Reflects the chosen interests (>=70% of activities match selected interests).
  - Keeps estimated daily cost within the selected budget range (within ±20%).
  - Respects simple scheduling constraints (no overlapping activities; includes travel time gaps).
- API stability: /generate endpoint returns a successful itinerary response in <=5 seconds for uncached requests and <=2 seconds for cached/popular requests, 95th percentile.
- UI usability: A usability test with 20 users yields a median satisfaction score >=4/5 for clarity and usefulness of the itinerary.

Operational & business metrics
- Adoption: At least 200 unique itinerary generations in the first month after launch (adjustable target).
- Lead generation: At least 5% of users who view an itinerary submit a contact or save request in first 3 months.
- Availability: System uptime >=99% monthly.
- Data quality: Random QA of 100 generated itineraries shows >=90% of POI links are valid (resolving to expected location pages).

Deliverables / Acceptance tests
- Flask REST API with documented endpoints:
  - POST /generate_itinerary {destination, days, budget, interests} → itinerary JSON
  - GET /itinerary/{id} → saved itinerary
  - POST /save_itinerary {itinerary, contact_info?}
  - GET /health
- Website with:
  - Input form page (destination, length, budget, interests)
  - Results page: day-by-day display, map links, cost summary, save/contact button
  - Admin/agency list view of saved itineraries (basic)
- Test cases to pass:
  - Input: “Paris”, 3 days, medium budget, interests {museums, food} → returns 3 days with museum/food items predominating, total cost in medium range.
  - Input: “A small city with few POIs” → fallback to curated suggestions and phrasing “light itinerary” (no failure).
  - Input validation: missing/invalid fields return appropriate 4xx errors.

Monitoring & Analytics
- Basic logging of API calls, response times, and errors.
- Track generated itineraries, saves, and contact submissions for business insight.

This document is intended to define the minimum viable product for a small travel agency to offer personalised city itineraries. Further capabilities (booking integration, multi-language, advanced personalization) can be scoped for later releases after validating demand.