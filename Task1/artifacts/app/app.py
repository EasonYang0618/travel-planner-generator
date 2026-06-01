import requests
import re
import base64
import time
import logging
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os, json, hashlib

app = Flask(__name__)

logger = logging.getLogger(__name__)
CORS(app)

def normalize_budget_value(budget):
    b = str(budget).strip().lower()
    if b in ('low','l','budget'):
        return 'low'
    if b in ('high','h','premium'):
        return 'high'
    return 'medium'

def normalize_interests(raw):
    if raw is None:
        return []
    items = []
    if isinstance(raw, str):
        raw = [raw]
    for v in raw:
        if not isinstance(v, str):
            continue
        s = v.strip().lower()
        if s in ('nature','outdoors'):
            items.append('outdoor')
        elif s == 'museum':
            items.append('museums')
        elif s == 'history':
            items.append('culture')
        elif s == 'dining':
            items.append('food')
        elif s in ('nightlife','family','shopping','food','outdoor','culture','museums'):
            items.append(s)
        else:
            items.append(s)
    # dedupe preserving order
    seen = set(); out=[]
    for i in items:
        if i not in seen:
            seen.add(i); out.append(i)
    return out

def make_activity(activity_source, time_window="activity", budget="medium", destination=""):
    # accepts dict or string
    budget_norm = normalize_budget_value(budget)
    budget_scale = {'low':0.75,'medium':1.0,'high':1.4}.get(budget_norm,1.0)
    if isinstance(activity_source, dict):
        title = activity_source.get('title') or activity_source.get('name') or "Local Activity"
        desc = activity_source.get('description') or activity_source.get('desc') or ""
        base = float(activity_source.get('base_cost') or activity_source.get('cost') or 10.0)
        dur = int(activity_source.get('duration_minutes') or activity_source.get('duration_hours',0)*60 or 90)
        loc = activity_source.get('location') or activity_source.get('place') or destination or ""
    else:
        title = str(activity_source)
        desc = f"{title} - a curated {time_window} activity in {destination}."
        # heuristic base cost by time window
        base = 12.0 if time_window=='morning' else 18.0 if time_window=='afternoon' else 28.0
        dur = 120 if time_window=='morning' else 180 if time_window=='afternoon' else 150
        loc = destination or ""
    estimated = round(base * budget_scale, 2)
    act = {
        "title": title,
        "name": title,
        "description": desc,
        "time_window": time_window,
        "duration_minutes": int(dur),
        "estimated_cost": estimated,
        "location": loc,
        "image_prompt": f"{title} in {destination}" if destination else title
    }
    return act

def create_error(message, status_code=400, field=None):
    code = "invalid_input"
    fields = {}
    if field:
        fields[field] = message
        code = "missing_field" if "missing" in message.lower() else "invalid_input"
    payload = {"error": {"message": message, "code": code, "fields": fields}}
    return jsonify(payload), status_code

# phrase banks for interests
_PHRASE_BANKS = {
    'food': {
        'prefixes': ["Local", "Neighborhood", "Classic", "Hidden", "Breakfast", "Signature", "Market"],
        'morning': ["Breakfast Market", "Bakery Stop", "Tea House Tasting", "Local Breakfast Market", "Street-food Lane", "Morning Produce Market", "Neighborhood Noodle Stop"],
        'afternoon': ["Casual Lunch Counter", "Cooking Mini-Workshop", "Food Hall Tasting", "Riverside Cafe", "Culinary Walk", "Bakery Tour", "Market Sampling"],
        'evening': ["Supper Club", "Evening Snack Street", "Signature Restaurant Meal", "Night Food Alley", "Food Night Stalls", "Rooftop Bites", "Late Dessert Crawl"]
    },
    'outdoor': {
        'prefixes': ["Scenic", "Lakeside", "Riverside", "Garden", "Hilltop", "Park", "Old Street"],
        'morning': ["Lakefront Walk", "City Park Reset", "Garden Trail", "Old Street Photo Walk", "Morning Hill Path", "Botanical Corner", "Riverside Cycling"],
        'afternoon': ["Scenic Viewpoint", "Picnic Stop", "Long Garden Stroll", "Nature Trail", "Botanical Garden Visit", "Riverbank Path", "Scenic Promenade"],
        'evening': ["Sunset Promenade", "Evening Waterfront Walk", "Golden Hour Viewpoint", "Riverside Sunset Spot", "Nighttime Lighted Promenade", "Harbour Twilight Walk", "Evening Boardwalk"]
    },
    'culture': {
        'prefixes': ["Heritage", "Local", "Historic", "Cultural", "Archive", "Museum-adjacent", "Artisan"],
        'morning': ["Town Heritage Walk", "Local Museum Visit", "Art House Morning Tour", "Historic Lane Walk", "Cultural Gallery Intro", "Monument Walk", "Archive Viewing"],
        'afternoon': ["Exhibition Walk", "Cultural Centre Workshop", "Historic Site Guided Walk", "Artisan Workshop", "Museum Collections Tour", "Local History Trail", "Gallery Walk"],
        'evening': ["Cultural Performance", "Evening Light Walk", "Traditional Music Show", "Theatre Performance", "Heritage Evening Talk", "Evening Cultural Night", "Local Performance Night"]
    },
    'museums': {  # alias for culture but separate bank
        'prefixes': ["Curated", "Main", "Specialist", "Grand", "Interactive", "Children's", "Contemporary"],
        'morning': ["Museum Collections Visit", "Special Exhibition Morning", "Curator Tour", "Interactive Exhibit Intro", "Gallery Overview", "Design Museum Stop", "Historical Collections Walk"],
        'afternoon': ["Deep Dive Exhibition", "Hands-on Workshop", "Themed Collection Tour", "Museum Cafeteria Stop", "Repository Visit", "Museum Guided Session", "Architecture Exhibit Walk"],
        'evening': ["Evening Exhibition Opening", "Night Museum Visit", "Museum Lecture Night", "Curated Evening Viewing", "Special Event Evening", "Collection Spotlight Night", "Museum After-hours"]
    },
    'shopping': {
        'prefixes': ["Bazaar", "Market", "Boutique", "Vintage", "Design", "Artisan", "Lane"],
        'morning': ["Morning Market Browse", "Antique Lane", "Bakery & Market Stop", "Local Crafts Market", "Produce Lane Walk", "Street-side Boutiques", "Vintage Arcade"],
        'afternoon': ["Shopping Street Stroll", "Boutique Hopping", "Design Market Visit", "Mall Local Brands", "Handmade Crafts Stop", "Souvenir Market", "Artisan Alley"],
        'evening': ["Night Market Shopping", "Evening Market Stalls", "Late Boutique Browsing", "Evening Craft Fair", "Street Vendor Night", "Night Bazaar", "After-hours Market"]
    },
    'nightlife': {
        'prefixes': ["Live", "Rooftop", "Classic", "Local", "Late", "Acoustic", "Venue"],
        'morning': ["Music History Walk", "Record Shop Browse", "Street Art Walk", "Daytime Venue Tour", "Local Coffee & Stories", "Music Museum Visit", "Gig Venue Visit (Day)"],
        'afternoon': ["Vinyl Shop Browse", "Live Music Lunch Spot", "Backstage Tour", "Sound Exhibition Visit", "Cultural Music Workshop", "Afternoon Gig Preview", "Local Bands Hangout"],
        'evening': ["Rooftop Cocktails", "Live Music Set", "Night Market & Drinks", "Late-night Bar Hop", "DJ Nightclub Set", "Speakeasy Cocktail Evening", "Evening Live Performance"]
    },
    'family': {
        'prefixes': ["Family", "Kid-friendly", "Playful", "Interactive", "Fun", "Story", "Children's"],
        'morning': ["Family Park Play", "Children's Museum Visit", "Puppet Show Morning", "Interactive Science Stop", "Family Baking Class", "Kid-friendly Farm Visit", "Playground & Picnic"],
        'afternoon': ["Aquarium or Zoo Visit", "Hands-on Workshop", "Play Centre Afternoon", "Boat Ride and Treats", "Story Trail Walk", "Educational Centre Visit", "Family Bike Ride"],
        'evening': ["Family Puppet Night", "Outdoor Movie Evening", "Light Parade Night", "Evening Boat Ride", "Children's Theatre", "Family-friendly Dinner Show", "Evening Storytime"]
    }
}

def _expand_bank(interest):
    bank = _PHRASE_BANKS.get(interest)
    if bank:
        prefixes = bank['prefixes']
        out = {'morning': [], 'afternoon': [], 'evening': []}
        for slot in ('morning','afternoon','evening'):
            for p in prefixes:
                for phrase in bank[slot]:
                    out[slot].append(f"{p} {phrase}")
        return out
    # fallback generation for unknown interest
    prefixes = ["Local", "Community", "Hidden", "Classic", "Curated"]
    slot_phrases = {
        'morning': [f"{interest.capitalize()} Walk", f"{interest.capitalize()} Workshop", f"{interest.capitalize()} Market"],
        'afternoon': [f"{interest.capitalize()} Tour", f"{interest.capitalize()} Studio Visit", f"{interest.capitalize()} Exhibit"],
        'evening': [f"{interest.capitalize()} Evening Event", f"{interest.capitalize()} Night Stroll", f"{interest.capitalize()} Performance"]
    }
    out = {'morning': [], 'afternoon': [], 'evening': []}
    for slot in ('morning','afternoon','evening'):
        for p in prefixes:
            for phrase in slot_phrases[slot]:
                out[slot].append(f"{p} {phrase}")
    return out

def build_itinerary(destination, days, budget, interests, travel_style):
    interests = interests or []
    if not interests:
        interests = ['culture']
    # deterministic seed from normalized input
    norm = json.dumps({"destination":destination,"days":days,"budget":budget,"interests":sorted(interests),"travel_style":travel_style}, sort_keys=True)
    seed = int(hashlib.sha256(norm.encode('utf-8')).hexdigest(), 16)
    # prepare banks per interest
    banks = {i: _expand_bank(i) for i in interests}
    used_titles_by_slot = {'morning': set(), 'afternoon': set(), 'evening': set()}
    slot_rot_start = {
        'morning': seed % 7,
        'afternoon': (seed//7) % 7,
        'evening': (seed//49) % 7
    }
    itinerary = []
    interest_cycle = []
    # create a rotation of interests deterministic
    for d in range(days):
        interest_cycle.append(interests[(seed + d) % len(interests)])
    themes = ["arrival and orientation","local culture","food and neighbourhoods","scenery and slower pace","hidden corners","final highlights","shopping and markets","family friendly","nightlife highlights","museums and galleries","parks and viewpoints","heritage trail","creative workshops","relaxation and spa"]
    for d in range(1, days+1):
        primary = interest_cycle[d-1]
        day_theme = themes[(seed + d + len(primary)) % len(themes)]
        day_obj = {"day": d, "theme": day_theme}
        day_acts = {}
        for slot in ('morning','afternoon','evening'):
            bank = banks.get(primary, {}).get(slot, [])
            # ensure deterministic ordering starting point
            start_idx = (slot_rot_start[slot] + d + sum(ord(c) for c in destination[:5])) % max(1, len(bank))
            chosen_title = None
            # attempt to pick unused title without endless loops
            attempts = 0
            for offset in range(len(bank)):
                idx = (start_idx + offset) % len(bank)
                candidate = bank[idx]
                attempts += 1
                if candidate not in used_titles_by_slot[slot]:
                    chosen_title = candidate
                    break
                if attempts >= len(bank):
                    break
            if chosen_title is None:
                # all used; allow reuse but vary description
                chosen_title = bank[(start_idx + d) % len(bank)]
                description = f"{chosen_title} revisited with a new route and focus for day {d} in {destination}."
            else:
                description = f"{chosen_title} - a {slot} activity in {destination}."
                used_titles_by_slot[slot].add(chosen_title)
            act = make_activity(chosen_title, time_window=slot, budget=budget, destination=destination)
            # if reuse case, override description
            if "revisited" in description:
                act['description'] = description
            # ensure evening-only constraints: if title suggests nightlife phrases, force evening slot
            if any(k in chosen_title.lower() for k in ('night','bar','cocktail','club','rooftop','dj','live music','performance')) and slot != 'evening':
                # move to evening alternative: pick evening bank item instead
                ebank = banks.get(primary, {}).get('evening', [])
                if ebank:
                    new_title = ebank[(start_idx + d) % len(ebank)]
                    act = make_activity(new_title, time_window='evening', budget=budget, destination=destination)
                    used_titles_by_slot['evening'].add(new_title)
                    day_acts[slot] = act
                    continue
            day_acts[slot] = act
        # budget note
        bnote = f"Estimated costs scaled for a {budget} budget."
        day_obj.update({
            "morning": day_acts['morning'],
            "afternoon": day_acts['afternoon'],
            "evening": day_acts['evening'],
            "budget_note": bnote
        })
        itinerary.append(day_obj)
    return itinerary

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
        return create_error("Invalid or missing JSON body", 400)
    destination = data.get('destination')
    days = data.get('days')
    budget_raw = data.get('budget', 'medium')
    interests_raw = data.get('interests', [])
    travel_style = data.get('travel_style', 'balanced')
    # validation
    if not destination or not isinstance(destination, str) or not destination.strip():
        return create_error("Missing destination", 400, field="destination")
    destination = destination.strip()[:100]
    try:
        days_i = int(days)
    except Exception:
        return create_error("Days must be an integer", 400, field="days")
    if days_i < 1 or days_i > 14:
        return create_error("Days out_of_range (1-14)", 400, field="days")
    budget = normalize_budget_value(budget_raw)
    interests = normalize_interests(interests_raw)
    if not interests:
        return create_error("At least one interest required", 400, field="interests")
    if not isinstance(travel_style, str) or not travel_style.strip():
        return create_error("Missing travel_style", 400, field="travel_style")
    # build itinerary
    itinerary = build_itinerary(destination, days_i, budget, interests, travel_style)
    overview = f"{days_i}-day plan for {destination} focusing on {', '.join(interests[:3])}."
    tips = [
        f"Adjust days for pace: {travel_style}.",
        "Carry a reusable water bottle and local transport card.",
        f"Budget level: {budget}. Book evening events in advance."
    ]
    resp = {
        "destination": destination,
        "days": days_i,
        "budget": budget,
        "interests": interests,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": itinerary,
        "tips": tips
    }
    return jsonify(resp), 200


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