import logging
import requests
import re
import base64
import time
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import random, os

app = Flask(__name__)
CORS(app)

INTEREST_MAP = {
    'nature': 'outdoor', 'outdoors': 'outdoor', 'outdoor': 'outdoor',
    'museum': 'museums', 'museums': 'museums',
    'history': 'culture', 'culture': 'culture',
    'dining': 'food', 'food': 'food'
}
DEFAULT_INTERESTS = ['culture', 'food', 'outdoor']

TEMPLATES = {
    'culture': {
        'morning': ["Visit the main historical museum in {dest}", "Guided walking tour of the old city in {dest}"],
        'afternoon': ["Explore local galleries and cultural centers in {dest}", "Visit an iconic monument in {dest}"],
        'evening': ["Attend a local cultural show in {dest}", "Enjoy a sunset stroll through the heritage district in {dest}"]
    },
    'museums': {
        'morning': ["Start at the famous museum of {dest}", "Special exhibition at the modern art museum in {dest}"],
        'afternoon': ["Science and history museum hop in {dest}", "Museum café and gift shop browse in {dest}"],
        'evening': ["Night-time museum event or rooftop museum cafe in {dest}", ""]
    },
    'food': {
        'morning': ["Breakfast at a popular local café in {dest}", "Visit a morning food market in {dest}"],
        'afternoon': ["Street food tour or cooking class in {dest}", "Lunch at a well-known bistro in {dest}"],
        'evening': ["Dine at a top local restaurant in {dest}", "Experience the nightlife and local food stalls in {dest}"]
    },
    'outdoor': {
        'morning': ["Hike a scenic trail near {dest}", "Morning visit to a popular city park in {dest}"],
        'afternoon': ["Boat tour or lakeside picnic in {dest}", "Bike around scenic neighborhoods in {dest}"],
        'evening': ["Sunset viewpoint visit in {dest}", "Evening riverside walk in {dest}"]
    }
}

def normalize_interests(raw):
    if not raw:
        return DEFAULT_INTERESTS
    if isinstance(raw, str):
        items = [i.strip().lower() for i in raw.split(',') if i.strip()]
    elif isinstance(raw, list):
        items = [str(i).strip().lower() for i in raw if str(i).strip()]
    else:
        return DEFAULT_INTERESTS
    mapped = []
    for it in items:
        if it in INTEREST_MAP:
            v = INTEREST_MAP[it]
            if v not in mapped:
                mapped.append(v)
    return mapped if mapped else DEFAULT_INTERESTS

def pick_activity(interest, part, dest, travel_style, budget):
    choices = TEMPLATES.get(interest, {}).get(part, ["Relax and explore {dest} at your pace"])
    text = random.choice(choices) if choices else ""
    return text.format(dest=dest)

def generate_itinerary(destination, days, budget, interests, travel_style):
    overview = f"{days}-day {travel_style} trip to {destination} focusing on {', '.join(interests)} with a {budget} budget."
    itinerary = []
    for d in range(1, days+1):
        # rotate interests to vary days
        morning = pick_activity(interests[(d-1) % len(interests)], 'morning', destination, travel_style, budget)
        afternoon = pick_activity(interests[(d) % len(interests)], 'afternoon', destination, travel_style, budget)
        evening = pick_activity(interests[(d+1) % len(interests)], 'evening', destination, travel_style, budget)
        # ensure at least one non-empty
        if not any([morning, afternoon, evening]):
            morning = f"Free morning to explore {destination}"
        budget_note = {"low":"Budget-friendly options; prioritize markets and parks",
                       "medium":"Mix of local favorites and a couple of paid attractions",
                       "high":"Include premium dining and guided experiences"}.get(budget, "Flexible budget options suggested")
        day_entry = {
            "day": d,
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "budget_note": budget_note
        }
        itinerary.append(day_entry)
    tips = [
        "Book popular sites in advance when possible.",
        "Carry a reusable water bottle and local map.",
        "Allow flexibility for weather and local events."
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
    return jsonify({"status":"ok"})

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route('/api/itinerary', methods=['POST'])
def api_itinerary():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error":"Invalid or missing JSON body"}), 400
    destination = data.get('destination') or data.get('city') or ""
    days = data.get('days')
    budget = (data.get('budget') or "medium").lower()
    interests_raw = data.get('interests', data.get('interest'))
    travel_style = data.get('travel_style', 'relaxed')
    if not isinstance(destination, str) or not destination.strip():
        return jsonify({"error":"destination is required"}), 400
    try:
        days = int(days)
    except Exception:
        return jsonify({"error":"days must be an integer between 1 and 14"}), 400
    if not (1 <= days <= 14):
        return jsonify({"error":"days must be between 1 and 14"}), 400
    interests = normalize_interests(interests_raw)
    result = generate_itinerary(destination.strip(), days, budget, interests, travel_style)
    return jsonify(result)


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
            image_urls = payload.get("image_list") or payload.get("urls") or []
            images = payload.get("images") or payload.get("data") or []
            if isinstance(image_urls, str):
                image_urls = [image_urls]
            if isinstance(images, dict):
                images = [images]
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
            if images and images[0].get("image_url"):
                image_response = requests.get(images[0]["image_url"], timeout=120)
                image_response.raise_for_status()
                with open(output_path, "wb") as image_file:
                    image_file.write(image_response.content)
                return request_id
            # Some providers mark the task successful before the CDN image URL is attached.
            # Keep polling instead of failing immediately.
            time.sleep(5)
            continue
        if status in {"failed", "error"}:
            raise RuntimeError(f"Image generation failed: {result_data}")
        time.sleep(5)
    raise TimeoutError(f"Image generation did not return image data before timeout: {result_data}")

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
        logging.exception("Error generating destination image")
        return jsonify({"error": "Image generation failed", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)