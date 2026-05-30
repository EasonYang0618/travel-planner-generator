import requests
import re
import base64
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, datetime, hashlib

app = Flask(__name__)
CORS(app)

INTEREST_MAP = {
    'nature': 'outdoor', 'outdoors': 'outdoor',
    'museum': 'museums', 'museums': 'museums',
    'history': 'culture', 'culture': 'culture',
    'dining': 'food', 'food': 'food',
    'nightlife': 'nightlife','shopping':'shopping'
}
DEFAULT_INTERESTS = ['culture', 'food', 'outdoor']

ACTIVITY_TEMPLATES = {
    'culture': [
        ("City Museum visit", "Explore a local museum or cultural center."),
        ("Historical walking tour", "Guided or self-guided walk through historic district.")
    ],
    'museums': [
        ("Art & History Museum", "See curated exhibits highlighting local heritage."),
        ("Special exhibition", "Temporary exhibits featuring regional artists.")
    ],
    'food': [
        ("Local market tasting", "Sample street food and local specialties."),
        ("Recommended restaurant", "Sit-down meal at a popular local spot.")
    ],
    'outdoor': [
        ("Scenic park visit", "Relax or walk in a well-known park or nature spot."),
        ("Coastal promenade", "Walk along waterfront or viewpoints.")
    ],
    'nightlife': [
        ("Live music venue", "Enjoy local bands or performances."),
        ("Bar hop", "Visit a selection of popular local bars.")
    ],
    'shopping': [
        ("Local artisan market", "Browse crafts and souvenirs."),
        ("Shopping street", "Explore boutiques and local designers.")
    ]
}

BUDGET_SCALE = {'low': 0.5, 'medium': 1.0, 'high': 2.0}

def normalize_interests(raw):
    if not raw:
        return DEFAULT_INTERESTS
    if isinstance(raw, str):
        items = [s.strip() for s in raw.split(',')]
    elif isinstance(raw, list):
        items = raw
    else:
        return DEFAULT_INTERESTS
    mapped = []
    for it in items:
        if not it: continue
        key = it.lower()
        mapped.append(INTEREST_MAP.get(key, key))
    mapped = [m for m in mapped if m]
    # keep only known or defaults
    valid = [m for m in mapped if m in ACTIVITY_TEMPLATES]
    return valid if valid else DEFAULT_INTERESTS

def seed_from_inputs(destination, days, budget, interests, travel_style):
    s = f"{destination}|{days}|{budget}|{','.join(interests)}|{travel_style}"
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

def pick_activity(interest, index):
    options = ACTIVITY_TEMPLATES.get(interest, ACTIVITY_TEMPLATES['culture'])
    return options[index % len(options)]

def cost_for_activity(budget_level):
    base = 20
    scale = BUDGET_SCALE.get(budget_level, 1.0)
    return int(base * scale)


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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route('/api/itinerary', methods=['POST'])
def create_itinerary():
    data = request.get_json(silent=True) or {}
    destination = (data.get('destination') or "").strip()
    try:
        days = int(data.get('days'))
    except Exception:
        days = None
    budget = (data.get('budget') or "medium").lower()
    interests = normalize_interests(data.get('interests'))
    travel_style = (data.get('travel_style') or "moderate")
    if not destination:
        return jsonify({"error": "destination is required"}), 400
    if days is None or not (1 <= days <= 14):
        return jsonify({"error": "days must be an integer between 1 and 14"}), 400

    seed = seed_from_inputs(destination, days, budget, interests, travel_style)
    itinerary = []
    total_estimated = 0
    for d in range(1, days + 1):
        # Deterministic selection based on seed and day
        idx = (seed + d) % 997
        morning, afternoon, evening = [], [], []
        chosen_interest = interests[(seed + d) % len(interests)]
        # pick activities rotating through interests
        mi_name, mi_desc = pick_activity(chosen_interest, d)
        cost = cost_for_activity(budget) + ((d * 3) % 20)
        morning = [{"name": mi_name, "description": mi_desc,
                    "est_duration_minutes": 120, "est_cost": cost}]
        total = cost
        # Afternoon: alternate interest or add local food
        ai_interest = interests[(seed + d + 1) % len(interests)]
        ai_name, ai_desc = pick_activity(ai_interest, d+1)
        cost2 = int(cost * (0.8 if budget=='low' else 1.0))
        afternoon = [{"name": ai_name, "description": ai_desc,
                      "est_duration_minutes": 150, "est_cost": cost2}]
        total += cost2
        # Evening optional: add if travel_style or nightlife interest
        if travel_style.lower() in ('relaxed','social') or 'nightlife' in interests or (d % 2 == 0):
            ei_name, ei_desc = pick_activity('food', d+2)
            cost3 = int(cost * (0.6 if budget=='low' else 1.2))
            evening = [{"name": "Evening: " + ei_name, "description": "Dinner and evening activity. " + ei_desc,
                        "est_duration_minutes": 120, "est_cost": cost3}]
            total += cost3
        # Ensure at least one activity
        if not (morning or afternoon or evening):
            morning = [{"name":"Leisure time","description":"Free time to explore.","est_duration_minutes":180,"est_cost":0}]
        budget_note = f"Estimated daily spend: ${total}"
        total_estimated += total
        itinerary.append({
            "day": d,
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "budget_note": budget_note
        })

    overview = f"{days}-day trip to {destination} focused on {', '.join(interests)} with a {budget} budget."
    tips = [
        "Book major attractions in advance when possible.",
        "Use public transport to save money and time.",
        "Allow flexibility in your schedule for unexpected finds."
    ]
    result = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "interests": interests,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": itinerary,
        "tips": tips,
        "estimated_total": f"${total_estimated}",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    return jsonify(result), 201


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

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    app.run(host='0.0.0.0', port=port)