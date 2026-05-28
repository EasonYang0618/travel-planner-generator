import requests
import re
import base64
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

INTEREST_MAP = {
    'nature': 'outdoor', 'outdoors': 'outdoor', 'outdoor': 'outdoor',
    'museum': 'museums', 'museums': 'museums',
    'history': 'culture', 'culture': 'culture',
    'dining': 'food', 'food': 'food',
    'nightlife': 'nightlife', 'family': 'family', 'shopping': 'shopping'
}

ACTIVITY_TEMPLATES = {
    'museums': {
        'morning': "Visit a prominent museum to explore local art and history.",
        'afternoon': "Take a guided tour in a specialty gallery or exhibition.",
        'evening': "Attend an evening lecture or museum special event if available."
    },
    'food': {
        'morning': "Start with a local breakfast spot or food market tasting.",
        'afternoon': "Join a food tour or try street food specialties.",
        'evening': "Dine at a recommended local restaurant or sample nightlife eats."
    },
    'outdoor': {
        'morning': "Walk a scenic trail or visit a city park for views and photos.",
        'afternoon': "Explore outdoor markets, gardens, or a nearby natural site.",
        'evening': "Relax at a waterfront, viewpoint or enjoy a sunset picnic."
    },
    'culture': {
        'morning': "Stroll historic neighborhoods and visit notable landmarks.",
        'afternoon': "Discover cultural centers, monuments, or heritage sites.",
        'evening': "Enjoy a cultural performance or a historic walking tour by lantern."
    },
    'nightlife': {
        'morning': "Sleep in or enjoy a leisurely brunch after a late night.",
        'afternoon': "Visit craft breweries or local cafés to prepare for the evening.",
        'evening': "Experience the city's nightlife: bars, live music, or clubs."
    },
    'family': {
        'morning': "Visit a child-friendly attraction like a zoo or interactive museum.",
        'afternoon': "Plan hands-on activities or a family picnic in a park.",
        'evening': "Choose an early family-friendly show or relaxed dinner spot."
    },
    'shopping': {
        'morning': "Browse local artisan markets and boutiques.",
        'afternoon': "Explore a shopping district and seek local specialties.",
        'evening': "Visit a night market or pick a relaxed café to review finds."
    }
}

BUDGET_NOTE = {
    'low': "Low budget: focus on free and low-cost activities.",
    'medium': "Medium budget: mix of free attractions and paid highlights.",
    'high': "High budget: include premium experiences and dining options."
}

def normalize_interests(raw):
    if not raw:
        return ['culture', 'food', 'outdoor']
    if isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.split(',') if p.strip()]
    elif isinstance(raw, list):
        parts = [str(p).strip().lower() for p in raw]
    else:
        parts = []
    mapped = []
    for p in parts:
        if p in INTEREST_MAP:
            v = INTEREST_MAP[p]
            if v not in mapped:
                mapped.append(v)
    if not mapped:
        return ['culture', 'food', 'outdoor']
    return mapped

def pick_activity(partials, interest, part_of_day, day_index, budget):
    templates = ACTIVITY_TEMPLATES.get(interest, {})
    base = templates.get(part_of_day)
    if not base:
        return ""
    # Slight variation deterministically
    suffix = ""
    if budget == 'low' and part_of_day == 'evening':
        suffix = " Opt for local low-cost options or street food."
    if day_index % 3 == 0:
        suffix += " Consider a shorter visit to leave time for wandering."
    return base + suffix

def generate_itinerary(destination, days, budget, interests, travel_style):
    overview = f"{days}-day trip to {destination}. Focus: {', '.join(interests)}. Budget: {budget}."
    tips = [
        "Book popular attractions in advance when possible.",
        "Mix iconic sights with local neighbourhood exploration.",
        "Keep afternoons flexible for rest or spontaneous discoveries."
    ]
    itinerary = []
    for i in range(1, days + 1):
        interest = interests[(i - 1) % len(interests)]
        # decide which parts to fill to ensure at least one activity
        morning = pick_activity(ACTIVITY_TEMPLATES, interest, 'morning', i, budget) if True else ""
        afternoon = pick_activity(ACTIVITY_TEMPLATES, interest, 'afternoon', i, budget) if True else ""
        evening = pick_activity(ACTIVITY_TEMPLATES, interest, 'evening', i, budget) if True else ""
        # If template missing (empty), try other interests to ensure at least one activity
        if not (morning or afternoon or evening):
            for alt in ['culture','food','outdoor']:
                morning = morning or pick_activity(ACTIVITY_TEMPLATES, alt, 'morning', i, budget)
                afternoon = afternoon or pick_activity(ACTIVITY_TEMPLATES, alt, 'afternoon', i, budget)
                evening = evening or pick_activity(ACTIVITY_TEMPLATES, alt, 'evening', i, budget)
                if morning or afternoon or evening:
                    break
        day_entry = {
            "day": i,
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "budget_note": BUDGET_NOTE.get(budget, BUDGET_NOTE['medium'])
        }
        itinerary.append(day_entry)
    # Add small personalized tip based on travel_style
    if travel_style:
        tips.append(f"Travel style note: {travel_style}. Tailor activities to your preferred pace.")
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

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route('/api/itinerary', methods=['POST'])
def api_itinerary():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    destination = data.get('destination') or data.get('city') or ""
    days = data.get('days')
    budget = (data.get('budget') or "medium").lower()
    raw_interests = data.get('interests')
    travel_style = data.get('travel_style') or data.get('style') or ""
    # validations
    if not isinstance(destination, str) or not destination.strip():
        return jsonify({"error": "destination is required"}), 400
    try:
        days = int(days)
    except Exception:
        return jsonify({"error": "days must be an integer"}), 400
    if not (1 <= days <= 14):
        return jsonify({"error": "days must be between 1 and 14"}), 400
    interests = normalize_interests(raw_interests)
    itinerary = generate_itinerary(destination.strip(), days, budget if budget in BUDGET_NOTE else "medium", interests, travel_style)
    return jsonify(itinerary)


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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)