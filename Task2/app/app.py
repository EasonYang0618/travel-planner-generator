import requests
import re
import base64
import time
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging, os, uuid, datetime, random

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# In-memory storage
itineraries = {}

# Normalization map
NORMALIZE = {
    "nature": "outdoor", "outdoors": "outdoor", "outdoor": "outdoor",
    "museum": "museums", "museums": "museums",
    "history": "culture", "culture": "culture",
    "dining": "food", "food": "food",
    "nightlife": "nightlife", "shopping": "shopping", "family": "family"
}
DEFAULT_INTERESTS = ["culture", "food", "outdoor"]

def normalize_interests(raw):
    if raw is None:
        return DEFAULT_INTERESTS
    if isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    elif isinstance(raw, list):
        parts = [str(p).strip().lower() for p in raw if p]
    else:
        parts = []
    mapped = []
    for p in parts:
        if p in NORMALIZE:
            mapped.append(NORMALIZE[p])
        elif p in NORMALIZE.values():
            mapped.append(p)
    return mapped or DEFAULT_INTERESTS

def activity_templates(destination):
    return {
        "culture": [
            ("Historic District Walk", f"Guided or self-led walk through {destination}'s historic quarter."),
            ("Local Art Gallery", f"Explore contemporary and traditional artworks in {destination}."),
            ("Cultural Show", f"Attend a performance showcasing local music or dance.")
        ],
        "food": [
            ("Food Market Tour", f"Sample street food and local specialties at the market."),
            ("Classic Restaurant", f"Dine at a recommended spot serving regional cuisine."),
            ("Cooking Class", f"Learn to cook a local dish with a short hands-on class.")
        ],
        "outdoor": [
            ("City Park Hike", f"Relax or hike in a popular park with scenic views."),
            ("Coastal Walk", f"Enjoy a walk along the waterfront and viewpoints."),
            ("Boat or Nature Trip", f"Short boat ride or nature excursion near {destination}.")
        ],
        "museums": [
            ("Main Museum", f"Visit the city's prominent museum with curated exhibits."),
            ("Specialty Museum", f"Explore niche collections about local history or science.")
        ],
        "nightlife": [
            ("Live Music Venue", "Catch live music at a local venue."),
            ("Rooftop Bar", "Enjoy skyline views with drinks at a rooftop spot.")
        ],
        "shopping": [
            ("Local Market", "Browse artisan stalls and local crafts."),
            ("Boutique Street", "Window-shop and find unique local designers.")
        ],
        "family": [
            ("Interactive Museum", "Kid-friendly exhibits and hands-on activities."),
            ("Zoo or Aquarium", "Visit family attractions suitable for children.")
        ]
    }

def choose_activity(pool, used):
    choices = [a for a in pool if a[0] not in used]
    if not choices:
        choices = pool
    act = random.choice(choices)
    used.add(act[0])
    return {"title": act[0], "description": act[1],
            "estimated_duration": f"{random.choice([45,60,90,120])} mins",
            "time_of_day": None, "cost_tier": random.choice(["low","medium","high"])}

def plan_itinerary(destination, days, budget, interests, travel_style):
    pools = activity_templates(destination)
    used = set()
    day_list = []
    for d in range(1, days+1):
        slots = {"morning": None, "afternoon": None, "evening": None}
        # Decide number of activities 1-3
        num = random.choice([1,2,2,3])
        chosen_slots = random.sample(list(slots.keys()), num)
        for slot in chosen_slots:
            interest = random.choice(interests)
            pool = pools.get(interest, pools["culture"])
            act = choose_activity(pool, used)
            act["time_of_day"] = slot
            # adjust cost by budget preference
            if budget == "low" and act["cost_tier"] == "high":
                act["cost_tier"] = "medium"
            if budget == "high" and act["cost_tier"] == "low":
                act["cost_tier"] = random.choice(["medium","high"])
            slots[slot] = act
        # budget note
        bn = {"low":"Focus on free or low-cost options.",
              "medium":"Mix of paid attractions and free activities.",
              "high":"Includes higher-end experiences and dining."}.get(budget, "")
        day_list.append({"day": d, **slots, "budget_note": bn})
    overview = f"{days}-day {travel_style or 'mixed-style'} trip to {destination} focused on {', '.join(interests)}."
    tips = [
        "Book popular attractions in advance when possible.",
        "Check opening hours and local holidays.",
        "Allow extra time for transit between activities."
    ]
    estimated_cost = sum(10 if a and a["cost_tier"]=="low" else 30 if a and a["cost_tier"]=="medium" else 80
                         for day in day_list for a in [day.get("morning"), day.get("afternoon"), day.get("evening")] if a)
    return {"destination": destination, "days": days, "budget": budget,
            "interests": interests, "travel_style": travel_style,
            "overview": overview, "itinerary": day_list, "tips": tips,
            "estimated_total_cost": estimated_cost, "generated_at": datetime.datetime.utcnow().isoformat()+"Z"}


def parse_interests(raw):
    if not raw:
        return DEFAULT_INTERESTS[:] if "DEFAULT_INTERESTS" in globals() else ["culture", "food", "outdoor"]
    if isinstance(raw, str):
        values = [item.strip().lower() for item in raw.replace(";", ",").split(",") if item.strip()]
    elif isinstance(raw, list):
        values = [str(item).strip().lower() for item in raw if str(item).strip()]
    else:
        values = []
    interest_map = globals().get("INTEREST_MAP", {"nature": "outdoor", "outdoors": "outdoor", "history": "culture", "dining": "food"})
    valid = set(globals().get("BASE_COSTS", {"culture": 1, "food": 1, "outdoor": 1, "museums": 1}).keys())
    normalized = []
    for value in values:
        mapped = interest_map.get(value, value)
        if mapped in valid and mapped not in normalized:
            normalized.append(mapped)
    return normalized or (DEFAULT_INTERESTS[:] if "DEFAULT_INTERESTS" in globals() else ["culture", "food", "outdoor"])

def make_activity(interest, time_window, *args):
    destination = None
    if len(args) == 1:
        budget = args[0]
    elif len(args) >= 2:
        destination = args[0]
        budget = args[1]
    else:
        budget = "medium"
    templates = {
        "culture": ("Cultural landmark visit", "Explore a notable cultural site and learn local context."),
        "food": ("Local food stop", "Try representative local dishes in a popular neighbourhood."),
        "outdoor": ("Scenic outdoor walk", "Spend time in a park, waterfront, garden, or viewpoint."),
        "museums": ("Museum visit", "Visit a museum or curated exhibition related to the city."),
        "nightlife": ("Evening entertainment", "Enjoy a relaxed local nightlife or performance option."),
        "shopping": ("Local shopping area", "Browse markets, boutiques, or craft shops.")
    }
    title, description = templates.get(interest, templates["culture"])
    base_costs = globals().get("BASE_COSTS", {})
    low, high = base_costs.get(interest, (10, 40))
    multiplier = globals().get("BUDGET_MULT", {}).get(budget, 1.0)
    location_prefix = f"{destination} " if destination else ""
    return {"title": title, "name": title, "description": description, "time_window": time_window, "duration_minutes": 90, "estimated_cost": int(((low + high) / 2) * multiplier), "location": f"{location_prefix}{interest.title()} area"}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"})

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route("/api/itinerary", methods=["POST"])
def create_itinerary():
    data = request.get_json() or {}
    logging.info("POST /api/itinerary %s", {k: v for k,v in data.items() if k!="auth"})
    destination = data.get("destination", "").strip()
    days = data.get("days")
    budget = (data.get("budget") or "medium").lower()
    interests = normalize_interests(data.get("interests"))
    travel_style = data.get("travel_style", "relaxed")
    # validation
    errors = {}
    if not destination:
        errors["destination"] = "Destination is required."
    try:
        days = int(days)
        if not (1 <= days <= 14):
            errors["days"] = "Days must be between 1 and 14."
    except Exception:
        errors["days"] = "Days must be an integer."
    if errors:
        logging.warning("Validation errors: %s", errors)
        return jsonify({"errors":errors}), 400
    itinerary = plan_itinerary(destination, days, budget, interests, travel_style)
    id_ = str(uuid.uuid4())
    itineraries[id_] = itinerary
    resp = {"id": id_, **itinerary}
    return jsonify(resp), 201

@app.route("/api/itinerary/<id>", methods=["GET"])
def get_itinerary(id):
    it = itineraries.get(id)
    if not it:
        return jsonify({"error":"Itinerary not found"}), 404
    return jsonify({"id": id, **it})


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
        json={"model": image_model, "prompt": prompt, "negative_prompt": "blurry, distorted text, watermark, low quality, deformed objects", "width": 768, "height": 512, "num_images": 1},
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
        return jsonify({"destination": destination, "image_url": f"/generated_images/{filename}", "prompt": prompt, "request_id": request_id})
    except Exception as e:
        logger.exception("Error generating destination image")
        return jsonify({"error": "Image generation failed", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)