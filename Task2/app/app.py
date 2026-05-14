from flask import Flask, request, jsonify
from flask_cors import CORS
import os, logging, random, datetime

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SAMPLE_POIS = {
    "museums": [
        {"title":"City Museum", "category":"museum","cost_level":"low","duration":90,"neighbourhood":"Old Town"},
        {"title":"Contemporary Art Gallery", "category":"museum","cost_level":"medium","duration":120,"neighbourhood":"Riverside"},
    ],
    "food": [
        {"title":"Local Market Stalls","category":"food","cost_level":"low","duration":60,"neighbourhood":"Market District"},
        {"title":"Tasting Menu Restaurant","category":"food","cost_level":"high","duration":120,"neighbourhood":"Downtown"},
    ],
    "parks": [
        {"title":"Central Park Walk","category":"park","cost_level":"free","duration":90,"neighbourhood":"Greenbelt"},
        {"title":"Botanical Gardens","category":"park","cost_level":"low","duration":60,"neighbourhood":"Northside"},
    ],
    "nightlife": [
        {"title":"Rooftop Bar","category":"nightlife","cost_level":"medium","duration":120,"neighbourhood":"Downtown"},
        {"title":"Live Music Venue","category":"nightlife","cost_level":"low","duration":150,"neighbourhood":"Harbor"},
    ],
    "sightseeing": [
        {"title":"City Walking Tour","category":"sightseeing","cost_level":"low","duration":120,"neighbourhood":"Old Town"},
        {"title":"Scenic Overlook","category":"sightseeing","cost_level":"free","duration":45,"neighbourhood":"Hilltop"},
    ],
    "shopping": [
        {"title":"Crafts Market","category":"shopping","cost_level":"low","duration":90,"neighbourhood":"Market District"},
        {"title":"Boutique Street","category":"shopping","cost_level":"medium","duration":120,"neighbourhood":"Shopping Quarter"},
    ],
}

DEFAULT_INTERESTS = ["sightseeing","food","parks"]

def pick_activity(preferred, avoid_neigh=None, budget_pref="medium"):
    pool = []
    for interest in preferred:
        pool += SAMPLE_POIS.get(interest, [])
    if not pool:
        pool = sum(SAMPLE_POIS.values(), [])
    # Filter by budget preference: for low budget prefer free/low
    if budget_pref == "low":
        weighted = [p for p in pool if p["cost_level"] in ("free","low")]
        pool = weighted or pool
    # Avoid same neighbourhood if possible
    candidates = [p for p in pool if p.get("neighbourhood") != avoid_neigh] or pool
    return random.choice(candidates)

def generate_itinerary(destination, days, budget, interests, travel_style):
    interests = [i.lower() for i in interests] if interests else DEFAULT_INTERESTS
    today = datetime.date.today()
    itinerary = []
    total_items = 0
    low_cost_items = 0
    last_neighbour = None
    for d in range(1, days+1):
        day_date = (today + datetime.timedelta(days=d-1)).isoformat()
        morning = pick_activity(interests, avoid_neigh=last_neighbour, budget_pref=budget)
        last_neighbour = morning.get("neighbourhood")
        afternoon = pick_activity(interests, avoid_neigh=last_neighbour, budget_pref=budget)
        last_neighbour = afternoon.get("neighbourhood")
        evening = pick_activity(interests, avoid_neigh=last_neighbour, budget_pref=budget)
        for a in (morning,afternoon,evening):
            total_items += 1
            if a["cost_level"] in ("free","low"):
                low_cost_items += 1
        day_budget_note = f"Suggested budget level: {budget}. Mostly {'low-cost' if (low_cost_items/total_items)>0.7 else 'mixed'} activities."
        itinerary.append({
            "day": d,
            "date": day_date,
            "morning": {
                "title": morning["title"], "category": morning["category"],
                "cost_level": morning["cost_level"], "estimated_duration": morning["duration"],
                "time_of_day":"morning","short_description": f"Visit {morning['title']} in {morning.get('neighbourhood')}"
            },
            "afternoon": {
                "title": afternoon["title"], "category": afternoon["category"],
                "cost_level": afternoon["cost_level"], "estimated_duration": afternoon["duration"],
                "time_of_day":"afternoon","short_description": f"Enjoy {afternoon['title']} around {afternoon.get('neighbourhood')}"
            },
            "evening": {
                "title": evening["title"], "category": evening["category"],
                "cost_level": evening["cost_level"], "estimated_duration": evening["duration"],
                "time_of_day":"evening","short_description": f"Relax at {evening['title']} in the evening"
            },
            "budget_note": day_budget_note
        })
    overview = f"{days}-day trip to {destination} focused on {', '.join(interests[:3])} with a {budget} budget and {travel_style} travel style."
    tips = [
        "Book popular attractions in advance where possible.",
        "Carry a small daypack and water.",
        "Mix free activities with paid ones to manage budget."
    ]
    return {
        "destination": destination,
        "days": days,
        "budget": budget,
        "interests": interests,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": itinerary,
        "tips": tips
    }

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"}), 200

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service":"Travel Itinerary Planner",
        "routes":[
            {"POST":"/api/itinerary","body":"destination, days, budget, interests, travel_style"},
            {"GET":"/health"}
        ],
        "note":"Submit JSON to /api/itinerary to generate a trip plan."
    })

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    data = request.get_json(force=True, silent=True) or {}
    destination = data.get("destination") or data.get("city")
    days = data.get("days")
    budget = (data.get("budget") or "medium").lower()
    interests = data.get("interests") or data.get("tags") or []
    travel_style = data.get("travel_style") or "relaxed"
    # Normalize interests: accept comma string
    if isinstance(interests, str):
        interests = [i.strip() for i in interests.split(",") if i.strip()]
    # Validation
    errors = {}
    if not destination or not isinstance(destination, str) or not destination.strip():
        errors["destination"] = "destination is required"
    try:
        days = int(days)
        if not (1 <= days <= 14):
            errors["days"] = "days must be between 1 and 14"
    except Exception:
        errors["days"] = "days must be an integer between 1 and 14"
    if errors:
        logging.warning("Validation errors: %s", errors)
        return jsonify({"error":"invalid_input","details":errors}), 400
    logging.info("Generating itinerary for %s: %d days, budget=%s, interests=%s", destination, days, budget, interests)
    result = generate_itinerary(destination.strip(), days, budget, interests, travel_style)
    return jsonify(result), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)