import requests
import re
import base64
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, hashlib, random, datetime, logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

INTEREST_MAP = {
    "nature": "outdoor", "outdoors": "outdoor", "outdoor": "outdoor",
    "museum": "museums", "museums": "museums",
    "history": "culture", "culture": "culture",
    "dining": "food", "food": "food", "gastronomy": "food",
    "nightlife": "nightlife", "shopping": "shopping"
}
DEFAULT_INTERESTS = ["culture", "food", "outdoor"]

TEMPLATES = {
    "culture": [
        {"title":"City Museum","desc":"Explore a signature museum highlighting local history and art.","dur":2,"cost":"$"},
        {"title":"Historic District Walk","desc":"Guided or self-led stroll through the old town and landmarks.","dur":1.5,"cost":"Free"},
        {"title":"Local Gallery","desc":"Small contemporary gallery with rotating exhibits.","dur":1,"cost":"$"}
    ],
    "museums": [
        {"title":"Main Museum","desc":"Large museum with permanent collections and special exhibits.","dur":2.5,"cost":"$$"},
        {"title":"Science Center","desc":"Interactive exhibits suitable for all ages.","dur":2,"cost":"$"}
    ],
    "food": [
        {"title":"Food Market Visit","desc":"Try street food and local specialties at a bustling market.","dur":1.5,"cost":"$"},
        {"title":"Recommended Bistro","desc":"Sit-down lunch featuring local dishes.","dur":1.5,"cost":"$$"},
        {"title":"Coffee & Pastries","desc":"Relax at a local café sampling pastries.","dur":1,"cost":"$"}
    ],
    "outdoor": [
        {"title":"City Park Hike","desc":"Walk or light hike in a major park or waterfront.","dur":2,"cost":"Free"},
        {"title":"Scenic Overlook","desc":"Visit a viewpoint for photos and a short picnic.","dur":1,"cost":"Free"},
        {"title":"Botanical Garden","desc":"Stroll through themed gardens and conservatories.","dur":1.5,"cost":"$"}
    ],
    "nightlife": [
        {"title":"Live Music Venue","desc":"Evening with local bands or performances.","dur":3,"cost":"$$"},
        {"title":"Rooftop Bar","desc":"Cocktails with a view of the city skyline.","dur":2,"cost":"$$$"}
    ],
    "shopping": [
        {"title":"Local Crafts Market","desc":"Browse handmade goods and souvenirs.","dur":1.5,"cost":"$"},
        {"title":"Boutique Street","desc":"Window-shop independent boutiques and designers.","dur":2,"cost":"$$"}
    ]
}

def normalize_interests(raw):
    if not raw:
        return DEFAULT_INTERESTS
    if isinstance(raw, str):
        items = [i.strip().lower() for i in raw.split(",") if i.strip()]
    elif isinstance(raw, list):
        items = [str(i).strip().lower() for i in raw]
    else:
        items = []
    mapped = []
    for it in items:
        key = INTEREST_MAP.get(it, None)
        if key:
            if key not in mapped:
                mapped.append(key)
    return mapped if mapped else DEFAULT_INTERESTS

def seed_from_inputs(*parts):
    s = "|".join(str(p) for p in parts)
    h = hashlib.sha256(s.encode()).hexdigest()
    return int(h[:16],16)

def pick_activity(pool, rnd, destination, budget):
    template = rnd.choice(pool)
    activity = {
        "title": template["title"] + f" ({destination})",
        "description": template["desc"],
        "duration_hours": template["dur"],
        "time_of_day": None,
        "cost": template["cost"]
    }
    # adjust cost to budget
    if budget=="low" and activity["cost"] in ("$$","$$$"):
        activity["cost"] = "$"
    if budget=="high" and activity["cost"]=="$":
        activity["cost"] = "$$"
    return activity

def generate_itinerary(destination, days, budget, interests, travel_style):
    seed = seed_from_inputs(destination.lower(), days, ",".join(interests), budget, travel_style)
    rnd = random.Random(seed)
    overview = f"{days}-day {travel_style or 'balanced'} trip to {destination}. Focus: {', '.join(interests)}. Budget: {budget}."
    itinerary = []
    for d in range(1, days+1):
        day_block = {"day": d, "date": None, "morning": [], "afternoon": [], "evening": [], "budget_note": ""}
        # determine pace: relaxed -> fewer activities, active -> more
        if travel_style=="relaxed":
            slots = ["morning","afternoon"]
        elif travel_style=="active":
            slots = ["morning","afternoon","evening"]
        else:
            slots = ["morning","afternoon","evening"] if rnd.random()>0.3 else ["morning","afternoon"]
        # pick primary interest for the day with some weight to user interests
        primary = rnd.choice(interests)
        secondary = rnd.choice(interests + [i for i in DEFAULT_INTERESTS if i not in interests])
        for slot in slots:
            pool_choice = primary if rnd.random() > 0.4 else secondary
            pool = TEMPLATES.get(pool_choice, sum(TEMPLATES.values(), []))
            act = pick_activity(pool if isinstance(pool, list) else pool, rnd, destination, budget)
            act["time_of_day"] = slot
            # ensure short descriptions vary
            act["description"] += f" Suggested for the {slot}."
            # assign into slot as single activity or list
            day_block[slot].append(act)
        # ensure at least one activity
        if not any(day_block[s] for s in ("morning","afternoon","evening")):
            pool = TEMPLATES.get(primary, [])
            act = pick_activity(pool, rnd, destination, budget)
            act["time_of_day"] = "morning"
            day_block["morning"].append(act)
        # budget note
        if budget=="low":
            note = "Mostly free/low-cost activities recommended."
        elif budget=="high":
            note = "Includes higher-end dining and paid experiences."
        else:
            note = "Balanced selection of paid and free activities."
        day_block["budget_note"] = note
        itinerary.append(day_block)
    tips = [
        "Book popular museums in advance.",
        "Use local transit passes for savings.",
        "Start early for busy outdoor attractions."
    ]
    return {"destination": destination, "days": days, "budget": budget, "interests": interests,
            "travel_style": travel_style, "overview": overview, "itinerary": itinerary, "tips": tips,
            "generated_at": datetime.datetime.utcnow().isoformat()+"Z"}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"}), 200

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.exception("Invalid JSON")
        return jsonify({"error":"Invalid JSON body"}), 400
    destination = (data.get("destination") or "").strip()
    days = data.get("days")
    budget = (data.get("budget") or "medium").lower()
    interests_raw = data.get("interests")
    travel_style = (data.get("travel_style") or "balanced").lower()
    if not destination:
        return jsonify({"error":"destination is required"}), 400
    try:
        days = int(days)
    except Exception:
        return jsonify({"error":"days must be an integer"}), 400
    if not (1 <= days <= 14):
        return jsonify({"error":"days must be between 1 and 14"}), 400
    interests = normalize_interests(interests_raw)
    logging.info("Generate itinerary for %s %s days %s interests=%s style=%s", destination, days, budget, interests, travel_style)
    result = generate_itinerary(destination, days, budget, interests, travel_style)
    return jsonify(result), 200


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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)