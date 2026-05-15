import requests
import re
import base64
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, datetime, random

app = Flask(__name__)
CORS(app)

INTEREST_MAP = {
    'nature': 'outdoor', 'outdoors': 'outdoor', 'outdoor': 'outdoor',
    'museum': 'museums', 'museums': 'museums',
    'history': 'culture', 'culture': 'culture',
    'dining': 'food', 'food': 'food', 'culinary': 'food'
}
DEFAULT_INTERESTS = ['culture', 'food', 'outdoor']

TEMPLATES = {
    'culture': {
        'morning': ["Historic walking tour of central {dest}", "Local market visit and neighborhood stroll"],
        'afternoon': ["Visit a cultural center or landmark", "Guided city history tour"],
        'evening': ["Attend a local performance or concert", "Evening stroll in the old town"]
    },
    'museums': {
        'morning': ["Explore the main museum of {dest}", "Special exhibition at the modern art museum"],
        'afternoon': ["Museum cafe and collections", "Interactive science center visit"],
        'evening': ["Museum night event or lecture"]
    },
    'food': {
        'morning': ["Local breakfast spot and bakery tour", "Coffee tasting at a specialty cafe"],
        'afternoon': ["Street food tour or cooking class", "Lunch at a recommended neighborhood restaurant"],
        'evening': ["Dinner at a top local restaurant", "Foodie walking tour of evening markets"]
    },
    'outdoor': {
        'morning': ["Scenic hike or park visit", "Botanical gardens and morning walk"],
        'afternoon': ["Boat ride or lakeside picnic", "Bike tour through scenic routes"],
        'evening': ["Sunset viewpoint and photography", "Riverside promenade and casual dining"]
    }
}

def normalize_interests(raw):
    if not raw:
        return []
    if isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.replace(';',',').split(',') if p.strip()]
    elif isinstance(raw, list):
        parts = [str(p).strip().lower() for p in raw if str(p).strip()]
    else:
        parts = []
    normalized = []
    for p in parts:
        mapped = INTEREST_MAP.get(p)
        if mapped and mapped not in normalized:
            normalized.append(mapped)
    return normalized

def choose_activity(interest, period, dest):
    opts = TEMPLATES.get(interest, {}).get(period, [])
    if not opts: return ""
    choice = random.choice(opts)
    return choice.format(dest=dest)

def budget_note_for(day_index, budget):
    notes = {
        'low': "Budget-friendly choices; prioritize free/low-cost activities.",
        'mid': "Mixed budget: some paid attractions and local dining.",
        'high': "Comfortable budget: include premium meals and paid experiences."
    }
    return notes.get(budget, "Varied budget options available.")

@app.route('/health', methods=['GET'])
def health():
    return jsonify(status="ok")

@app.route('/', methods=['GET'])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route('/api/itinerary', methods=['POST'])
def create_itinerary():
    data = request.get_json() or {}
    destination = (data.get('destination') or "").strip()
    days_raw = data.get('days')
    budget = (data.get('budget') or "mid").lower()
    travel_style = (data.get('travel_style') or "balanced").lower()
    interests_raw = data.get('interests')

    errors = []
    if not destination:
        errors.append({"field":"destination","message":"destination is required"})
    try:
        days = int(days_raw)
        if days < 1 or days > 14:
            errors.append({"field":"days","message":"days must be between 1 and 14"})
    except Exception:
        errors.append({"field":"days","message":"days must be an integer between 1 and 14"})
    if errors:
        return jsonify(errors=errors), 400

    normalized = normalize_interests(interests_raw)
    if not normalized:
        normalized = DEFAULT_INTERESTS.copy()

    random.seed(f"{destination}-{days}-{budget}-{','.join(normalized)}-{travel_style}")

    itinerary = []
    for d in range(1, days+1):
        day_block = {"day": d, "morning": "", "afternoon": "", "evening": "", "budget_note": budget_note_for(d, budget)}
        # Determine activity density
        if travel_style == 'relaxed':
            periods = ['morning','evening']
        elif travel_style == 'active':
            periods = ['morning','afternoon','evening']
        else:
            periods = ['morning','afternoon']
        # rotate interests
        for i, period in enumerate(periods):
            interest = normalized[(d + i) % len(normalized)]
            activity = choose_activity(interest, period, destination)
            setattr_val = activity
            day_block[period] = activity
        # Ensure at least one activity
        if not any(day_block[p] for p in ['morning','afternoon','evening']):
            day_block['afternoon'] = f"Free exploration in {destination} (flexible activities)"
        itinerary.append(day_block)

    overview = f"{days}-day {travel_style} trip to {destination} focused on {', '.join(normalized)} with a {budget} budget."
    tips = [
        "Book popular attractions in advance during high season.",
        "Carry a refillable water bottle and comfortable shoes.",
        "Check opening hours for museums and special events."
    ]
    response = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "interests": normalized,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": itinerary,
        "tips": tips,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    print(f"[{response['generated_at']}] Generated itinerary for {destination}, days={days}, interests={normalized}")
    return jsonify(response), 200


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
