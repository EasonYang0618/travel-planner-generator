from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, logging, random, datetime, time, base64, re
import requests

app = Flask(__name__)
CORS(app)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Simple local POI dataset (generic templates; destination inserted at runtime)
POI_POOL = {
    "culture": [
        {"name": "Historic Center Walk", "desc": "Explore heritage streets and landmarks.", "cost": "low"},
        {"name": "Local Cultural Center", "desc": "Exhibits on local traditions and history.", "cost": "low"},
        {"name": "Architectural Highlights Tour", "desc": "Guided look at notable buildings.", "cost": "medium"},
        {"name": "Cultural Performance", "desc": "Evening show of music/dance.", "cost": "medium"},
    ],
    "food": [
        {"name": "Street Food Stroll", "desc": "Taste local specialties at market stalls.", "cost": "low"},
        {"name": "Popular Bistro", "desc": "Casual meal showcasing regional dishes.", "cost": "medium"},
        {"name": "Chef's Tasting Menu", "desc": "Multi-course dining experience.", "cost": "high"},
        {"name": "Food Market Visit", "desc": "Shop fresh ingredients and snacks.", "cost": "low"},
    ],
    "outdoor": [
        {"name": "Scenic Park Hike", "desc": "Walk or light hike through green spaces.", "cost": "low"},
        {"name": "Waterfront Promenade", "desc": "Relax by the water and enjoy views.", "cost": "low"},
        {"name": "Guided Nature Tour", "desc": "Learn about local flora/fauna.", "cost": "medium"},
        {"name": "Adventure Activity", "desc": "High-energy outdoor experience.", "cost": "high"},
    ],
    "shopping": [
        {"name": "Local Artisan Market", "desc": "Buy handcrafted souvenirs.", "cost": "low"},
        {"name": "Boutique Shopping Street", "desc": "Independent designers and shops.", "cost": "medium"},
        {"name": "Shopping Mall", "desc": "Modern retail with varied options.", "cost": "medium"},
    ],
    "nightlife": [
        {"name": "Rooftop Bar", "desc": "Drinks with a city view.", "cost": "high"},
        {"name": "Live Music Venue", "desc": "Local bands and performances.", "cost": "medium"},
        {"name": "Casual Pub Crawl", "desc": "Visit a few popular local pubs.", "cost": "low"},
    ],
    "museums": [
        {"name": "Main City Museum", "desc": "Core artworks and exhibits.", "cost": "medium"},
        {"name": "Specialty Museum", "desc": "Focused collection (science, maritime, etc.).", "cost": "medium"},
        {"name": "Small Gallery", "desc": "Emerging artists and rotating shows.", "cost": "low"},
    ],
}

COST_RANK = {"low": 1, "medium": 2, "high": 3}
COST_ESTIMATE = {"low": 10, "medium": 40, "high": 120}

def pick_poi_for_interest(destination, interest, budget_level):
    candidates = POI_POOL.get(interest, [])
    # prefer items with cost <= budget_level, else allow medium/high if necessary
    preferred = [p for p in candidates if COST_RANK[p["cost"]] <= budget_level]
    pool = preferred or candidates
    if not pool:
        return None
    p = random.choice(pool).copy()
    p["name"] = f"{destination} - {p['name']}"
    return p

def generate_itinerary(data):
    destination = data["destination"]
    days = data["days"]
    budget = data.get("budget", "medium").lower()
    interests = data.get("interests") or []
    if not isinstance(interests, list):
        interests = [interests]
    travel_style = data.get("travel_style", "balanced")
    budget_level = COST_RANK.get(budget, 2)

    all_interests = interests if interests else list(POI_POOL.keys())
    # Build a pool of POIs per interest
    day_plans = []
    used = []
    for d in range(1, days + 1):
        slots = {"morning": None, "afternoon": None, "evening": None}
        # Rotate interests to balance
        random.shuffle(all_interests)
        for idx, slot in enumerate(slots.keys()):
            interest = all_interests[idx % len(all_interests)]
            poi = pick_poi_for_interest(destination, interest, budget_level)
            if poi:
                # avoid immediate duplicates if possible
                tries = 0
                while poi["name"] in used and tries < 6:
                    poi = pick_poi_for_interest(destination, interest, budget_level)
                    tries += 1
                used.append(poi["name"])
                slots[slot] = {
                    "activity": poi["name"],
                    "description": poi["desc"],
                    "category": interest,
                    "estimated_cost": COST_ESTIMATE.get(poi["cost"], 20)
                }
        # Optionally remove evening for relaxed travel style
        if travel_style == "relaxed" and random.random() < 0.3:
            slots["evening"] = {"activity": "Leisure evening", "description": "Relax and enjoy local ambiance.", "category": "relax", "estimated_cost": 10}
        # Compute budget note
        est_cost = sum(v["estimated_cost"] for v in slots.values() if v)
        if budget_level == 1:
            note = f"Approx {est_cost}$ - budget-conscious choices with free/cheap options."
        elif budget_level == 2:
            note = f"Approx {est_cost}$ - mix of paid attractions and local eats."
        else:
            note = f"Approx {est_cost}$ - includes premium experiences."
        day_plans.append({
            "day": d,
            "morning": slots["morning"],
            "afternoon": slots["afternoon"],
            "evening": slots["evening"],
            "budget_note": note
        })

    overview = f"{days}-day {budget} budget trip to {destination} focused on {', '.join(all_interests)}."
    tips = [
        "Book popular attractions in advance when possible.",
        "Carry a reusable water bottle and comfortable shoes.",
        f"Adjust pace to your travel style: {travel_style}.",
        "Check local opening hours and transit options."
    ]
    return {
        "destination": destination,
        "days": days,
        "budget": budget,
        "interests": all_interests,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": day_plans,
        "tips": tips,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_destination.png", methods=["GET"])
def generated_destination_image():
    return send_from_directory(".", "generated_destination.png")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    logger.info("Received /api/itinerary request")
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Bad request: no JSON")
        return jsonify({"error": "Invalid JSON payload"}), 400
    destination = data.get("destination", "")
    days = data.get("days")
    if not destination or not isinstance(destination, str) or not destination.strip():
        return jsonify({"error": "destination is required"}), 400
    try:
        days = int(days)
    except Exception:
        return jsonify({"error": "days must be an integer"}), 400
    if days < 1 or days > 14:
        return jsonify({"error": "days must be between 1 and 14"}), 400
    try:
        itinerary = generate_itinerary({
            "destination": destination.strip(),
            "days": days,
            "budget": data.get("budget", "medium"),
            "interests": data.get("interests", []),
            "travel_style": data.get("travel_style", "balanced")
        })
        logger.info("Itinerary generated successfully")
        return jsonify(itinerary)
    except Exception as e:
        logger.exception("Error generating itinerary")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "destination"

def build_destination_image_prompt(destination, interests, travel_style):
    interest_text = ", ".join(interests[:4]) if interests else "local culture, food, and scenic places"
    return (
        f"Realistic editorial travel photography for a polished travel planner website: {destination}. "
        f"Show the feeling of {interest_text} with a {travel_style or 'balanced'} travel style. "
        "Bright natural light, professional composition, inviting destination atmosphere, no text, no logos, no watermark."
    )

def submit_apifree_destination_image(prompt, output_path):
    api_key = os.getenv("APIFREE_API_KEY")
    if not api_key:
        raise RuntimeError("APIFREE_API_KEY is not configured")
    base_url = os.getenv("APIFREE_BASE_URL", "https://api.apifree.ai/v1").rstrip("/")
    image_model = os.getenv("APIFREE_IMAGE_MODEL", "google/nano-banana-2")
    submit_response = requests.post(
        f"{base_url}/image/submit",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": image_model,
            "prompt": prompt,
            "negative_prompt": "blurry, distorted text, watermark, low quality, deformed objects",
            "width": 768,
            "height": 512,
            "num_images": 1,
        },
        timeout=120,
    )
    submit_response.raise_for_status()
    submit_data = submit_response.json()
    if "error" in submit_data:
        raise RuntimeError(submit_data["error"].get("message", submit_data["error"]))
    request_id = submit_data.get("request_id") or submit_data.get("resp_data", {}).get("request_id")
    if not request_id:
        raise RuntimeError(f"Image submission did not return request_id: {submit_data}")
    result_url = f"{base_url}/image/{request_id}/result"
    result_data = {}
    for _ in range(24):
        result_response = requests.get(result_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=120)
        result_response.raise_for_status()
        result_data = result_response.json()
        payload = result_data.get("resp_data", result_data)
        status = payload.get("status")
        if status in {"success", "completed"}:
            image_urls = payload.get("image_list") or []
            images = payload.get("images") or []
            if image_urls:
                image_response = requests.get(image_urls[0], timeout=120)
                image_response.raise_for_status()
                with open(output_path, "wb") as image_file:
                    image_file.write(image_response.content)
                return request_id
            if images and images[0].get("b64_json"):
                with open(output_path, "wb") as image_file:
                    image_file.write(base64.b64decode(images[0]["b64_json"]))
                return request_id
            if images and images[0].get("url"):
                image_response = requests.get(images[0]["url"], timeout=120)
                image_response.raise_for_status()
                with open(output_path, "wb") as image_file:
                    image_file.write(image_response.content)
                return request_id
            raise RuntimeError(f"Completed image result did not include image data: {result_data}")
        if status in {"failed", "error"}:
            raise RuntimeError(f"Image generation failed: {result_data}")
        time.sleep(5)
    raise TimeoutError(f"Image generation did not complete: {result_data}")

@app.route("/api/destination-image", methods=["POST"])
def api_destination_image():
    data = request.get_json(silent=True) or {}
    destination = (data.get("destination") or "").strip()
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    interests = data.get("interests") or []
    if isinstance(interests, str):
        interests = [i.strip() for i in interests.split(",") if i.strip()]
    travel_style = data.get("travel_style") or "balanced"
    prompt = build_destination_image_prompt(destination, interests, travel_style)
    image_dir = os.path.join(app.root_path, "generated_images")
    os.makedirs(image_dir, exist_ok=True)
    filename = f"{slugify(destination)}.png"
    output_path = os.path.join(image_dir, filename)
    try:
        request_id = submit_apifree_destination_image(prompt, output_path)
        return jsonify({
            "destination": destination,
            "image_url": f"/generated_images/{filename}",
            "prompt": prompt,
            "request_id": request_id,
        })
    except Exception as e:
        logger.exception("Error generating destination image")
        return jsonify({"error": "Image generation failed", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
