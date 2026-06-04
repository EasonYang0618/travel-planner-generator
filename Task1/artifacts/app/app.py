import requests
import re
import base64
import time
import logging
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os

app = Flask(__name__)

logger = logging.getLogger(__name__)
CORS(app)

def normalize_budget_value(budget):
    s = str(budget).lower()
    if 'low' in s:
        return 'low'
    if 'high' in s:
        return 'high'
    return 'medium'

def normalize_interests(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [raw]
    else:
        items = list(raw)
    mapping = {
        'nature': 'outdoor',
        'outdoors': 'outdoor',
        'museum': 'museums',
        'museums': 'museums',
        'history': 'culture',
        'dining': 'food',
        'food': 'food',
        'nightlife': 'nightlife',
        'family': 'family',
        'shopping': 'shopping',
        'culture': 'culture',
        'outdoor': 'outdoor'
    }
    result = []
    for it in items:
        if not isinstance(it, str):
            continue
        key = it.strip().lower()
        mapped = mapping.get(key, key)
        if mapped not in result:
            result.append(mapped)
    return result

def create_error(message, status_code=400, field=None):
    payload = {'error': message}
    if field:
        payload['fields'] = {field: message}
    return jsonify(payload), status_code

def make_activity(activity_source, time_window="activity", budget="medium", destination=""):
    # Accept POI dict, category string, or tuple/list produced by banks
    try:
        if isinstance(activity_source, dict):
            title = activity_source.get('title') or activity_source.get('name') or 'Local Activity'
            desc = activity_source.get('description') or activity_source.get('desc') or ''
            cost = activity_source.get('budget') or activity_source.get('estimated_cost') or 0
            loc = activity_source.get('location') or activity_source.get('place') or destination
            dur = activity_source.get('duration') or activity_source.get('duration_minutes') or 60
        elif isinstance(activity_source, (list, tuple)):
            # order: (title, description, estimated_cost, location, duration_minutes)
            try:
                title, desc, cost, loc, dur = activity_source
            except (TypeError, ValueError):
                # Fallback if tuple size mismatch
                title = str(activity_source)
                desc = ''
                cost = 0
                loc = destination
                dur = 60
        else:
            # treat as category string
            title = str(activity_source)
            desc = f"{title} around {destination}" if destination else title
            cost = 0
            loc = destination
            dur = 60
        # estimated cost numeric
        try:
            est = float(cost)
        except (TypeError, ValueError):
            est = 0.0
        # adjust by budget
        b = normalize_budget_value(budget)
        factor = 1.0
        if b == 'low':
            factor = 0.75
        elif b == 'high':
            factor = 1.4
        est = round(est * factor, 2)
        activity = {
            'title': title,
            'name': title,
            'description': desc,
            'time_window': time_window,
            'duration_minutes': int(dur) if isinstance(dur, (int, float)) else 60,
            'estimated_cost': est,
            'location': loc or destination or ''
        }
        return activity
    except Exception as e:
        # ensure returning a JSON serialisable fallback
        return {
            'title': 'Activity',
            'name': 'Activity',
            'description': 'Details unavailable',
            'time_window': time_window,
            'duration_minutes': 60,
            'estimated_cost': 0.0,
            'location': destination or ''
        }

def build_slot_bank(prefixes, slot_phrases, base_cost, locations, duration_choices):
    bank = []
    for p in prefixes:
        for sp in slot_phrases:
            for loc in locations:
                # create up to enough unique combos; stop when bank large enough
                title = f"{p} {sp}"
                desc = f"{sp.capitalize()} near {loc}"
                cost = base_cost
                dur = duration_choices[len(bank) % len(duration_choices)]
                bank.append((title, desc, cost, loc, dur))
                if len(bank) >= 30:
                    break
            if len(bank) >= 30:
                break
        if len(bank) >= 30:
            break
    return bank

def build_interest_banks(destination):
    prefixes = ["Local", "Classic", "Hidden", "Heritage", "Neighbourhood", "Signature", "Community"]
    duration_choices = [45,60,90,120]
    banks = {}
    # Food
    food_m = ["Breakfast Market", "Bakery Stop", "Tea House Tasting", "Morning Noodle Stall", "Produce Market"]
    food_a = ["Casual Lunch Counter", "Food Hall Tasting", "Cooking Mini-Workshop", "Café and Pastry Stop"]
    food_e = ["Evening Snack Street", "Riverside Dinner", "Supper Club Visit", "Signature Restaurant Meal"]
    banks['food'] = {
        'morning': build_slot_bank(prefixes, food_m, 8, ["Old Quarter","Market Lane","Riverside"], duration_choices),
        'afternoon': build_slot_bank(prefixes, food_a, 12, ["Main Street","Food Hall","Cooking School"], duration_choices),
        'evening': build_slot_bank(prefixes, food_e, 25, ["Harbour","Rooftop","Riverside"], duration_choices),
    }
    # Outdoor
    out_m = ["Lakefront Walk","City Park Reset","Garden Trail","Hill Path","Photo Walk"]
    out_a = ["Scenic Viewpoint","Botanical Corner","Riverside Cycling","Picnic Stop","Old Street Walk"]
    out_e = ["Sunset Promenade","Evening Waterfront Walk","Twilight Lookout","Lantern Path"]
    banks['outdoor'] = {
        'morning': build_slot_bank(prefixes, out_m, 0, ["Lakeside","Central Park","Hilltop"], duration_choices),
        'afternoon': build_slot_bank(prefixes, out_a, 0, ["Botanic Garden","Cycling Route","Riverside"], duration_choices),
        'evening': build_slot_bank(prefixes, out_e, 0, ["Promenade","Waterfront","Lookout"], duration_choices),
    }
    # Culture (and museums)
    cult_m = ["Heritage Lane Walk","Local History Trail","Artisan Quarter Intro","Temple Morning Visit"]
    cult_a = ["Museum Highlights","Gallery Route","Craft Workshop","Historical Walk"]
    cult_e = ["Evening Light Walk","Cultural Performance","Storytelling Session","Night Exhibit Preview"]
    banks['culture'] = {
        'morning': build_slot_bank(prefixes, cult_m, 5, ["Heritage District","Old Town"], duration_choices),
        'afternoon': build_slot_bank(prefixes, cult_a, 10, ["Museum Row","Gallery Alley"], duration_choices),
        'evening': build_slot_bank(prefixes, cult_e, 15, ["Town Square","Theatre"], duration_choices),
    }
    banks['museums'] = banks['culture']
    # Nightlife
    night_m = ["Evening-only placeholder"]  # will not be used in morning
    night_a = ["Afternoon-only placeholder"]  # will not be used in afternoon
    night_e = ["Night Market Walk","Live Music Bar","Cocktail Rooftop","Evening Performance","Late Supper Crawl"]
    banks['nightlife'] = {
        'morning': build_slot_bank(prefixes, ["Morning café warmup"], 5, ["Downtown"], duration_choices),
        'afternoon': build_slot_bank(prefixes, ["Leisure stroll"], 5, ["Shopping Strip"], duration_choices),
        'evening': build_slot_bank(prefixes, night_e, 20, ["Night District","Rooftop"], duration_choices),
    }
    # Family
    fam_m = ["Interactive Museum","Family Park Play","Children's Farm Visit","Kids Science Corner"]
    fam_a = ["Aquarium Tour","Zoo Visit","Hands-on Workshop","Theme Park Ride"]
    fam_e = ["Evening Puppet Show","Family-friendly Dinner","Lights Parade","Kid-friendly Movie Night"]
    banks['family'] = {
        'morning': build_slot_bank(prefixes, fam_m, 10, ["Family Area","Science Park"], duration_choices),
        'afternoon': build_slot_bank(prefixes, fam_a, 15, ["Aquarium","Zoo"], duration_choices),
        'evening': build_slot_bank(prefixes, fam_e, 12, ["Town Hall","Riverside"], duration_choices),
    }
    # Shopping
    shop_m = ["Market Browsing","Antique Lane","Local Crafts Stalls","Boutique Opening"]
    shop_a = ["Designer Walk","Shopping Arcade","Artisan Workshop Visit","Textile Market"]
    shop_e = ["Evening Bazaar","Late Market Bargains","Night Shopping Stroll","Afterhours Market"]
    banks['shopping'] = {
        'morning': build_slot_bank(prefixes, shop_m, 10, ["Market Lane","Old Quarter"], duration_choices),
        'afternoon': build_slot_bank(prefixes, shop_a, 20, ["Shopping Street","Arcade"], duration_choices),
        'evening': build_slot_bank(prefixes, shop_e, 15, ["Bazaar","Night Market"], duration_choices),
    }
    return banks

def build_itinerary(destination, days, budget, interests, travel_style):
    interests = normalize_interests(interests)
    if not interests:
        interests = ['culture']
    budget_norm = normalize_budget_value(budget)
    banks = build_interest_banks(destination)
    # ensure interests are valid keys
    interests = [i if i in banks else ('culture' if i=='museums' else i) for i in interests]
    # used titles per slot
    used_titles_by_slot = {'morning': set(), 'afternoon': set(), 'evening': set()}
    rotation_index = {'morning': 0, 'afternoon': 0, 'evening': 0}
    themes = [
        "Arrival and orientation","Local culture","Food and neighbourhoods","Scenery and slower pace",
        "Hidden corners","Active discovery","Markets and craft","Relaxed highlights","Architectural gems",
        "Family-friendly day","Shopping and style","Nightlife highlights","Heritage deep-dive","Final highlights"
    ]
    tips = []
    itinerary = []
    for d in range(1, days+1):
        theme = themes[(d-1) % len(themes)]
        day_obj = {'day': d, 'theme': theme}
        slot_selection = {}
        for slot, offset in [('morning',0), ('afternoon',1), ('evening',2)]:
            # pick interest rotating so slots vary
            sel_interest = interests[(d-1 + offset) % len(interests)]
            # enforce nightlife only evening content: if nightlife selected but slot isn't evening, choose neighbouring interest
            if sel_interest == 'nightlife' and slot != 'evening':
                sel_interest = interests[(d) % len(interests)]
            bank = banks.get(sel_interest) and banks[sel_interest].get(slot, [])
            # if bank empty, fallback to culture slot bank
            if not bank:
                bank = banks['culture'][slot]
            # pick an unused title deterministically starting at rotation_index
            chosen = None
            bank_len = len(bank)
            start = rotation_index[slot] % bank_len if bank_len>0 else 0
            attempts = 0
            for i in range(bank_len):
                idx = (start + i) % bank_len
                candidate = bank[idx]
                title = candidate[0]
                if title not in used_titles_by_slot[slot]:
                    chosen = candidate
                    rotation_index[slot] = idx + 1
                    used_titles_by_slot[slot].add(title)
                    break
                attempts += 1
                if attempts >= bank_len:
                    break
            if chosen is None:
                # all used: pick one with deterministic variation in description
                idx = start % bank_len if bank_len>0 else 0
                base = bank[idx]
                var_phrases = [" with extended route", " with a local guide angle", " focusing on stories and craft"]
                var = var_phrases[(d + offset) % len(var_phrases)]
                title, desc, cost, loc, dur = base
                desc = desc + var
                chosen = (title + "", desc, cost, loc, dur)
                rotation_index[slot] = (idx + 1) % bank_len
            activity = make_activity(chosen, time_window=slot, budget=budget_norm, destination=destination)
            slot_selection[slot] = activity
        day_obj['morning'] = slot_selection['morning']
        day_obj['afternoon'] = slot_selection['afternoon']
        day_obj['evening'] = slot_selection['evening']
        # budget note
        note = f"Estimated average day cost: {budget_norm}"
        day_obj['budget_note'] = note
        itinerary.append(day_obj)
        # tips generation (simple deterministic)
        if d == 1:
            tips.append(f"Arrive early to {destination} to adjust and enjoy a gentle orientation walk.")
        if d == days:
            tips.append("Save a highlight for your final day for relaxed departure.")
    overview = f"A {days}-day travel plan for {destination} focused on {', '.join(interests)} tailored to a {budget_norm} budget and {travel_style or 'balanced'} travel style."
    result = {
        'destination': destination,
        'days': days,
        'budget': budget_norm,
        'interests': interests,
        'travel_style': travel_style or '',
        'overview': overview,
        'itinerary': itinerary,
        'tips': tips
    }
    return result

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route('/api/itinerary', methods=['POST'])
def api_itinerary():
    if not request.is_json:
        return create_error("Request must be JSON", 400)
    data = request.get_json()
    destination = data.get('destination')
    days = data.get('days')
    budget = data.get('budget')
    interests = data.get('interests')
    travel_style = data.get('travel_style', '')
    # Validation
    if not destination or not isinstance(destination, str) or not destination.strip():
        return create_error("Missing or invalid destination", 400, field='destination')
    try:
        days_int = int(days)
    except Exception:
        return create_error("Days must be an integer", 400, field='days')
    if days_int < 1 or days_int > 14:
        return create_error("Days must be between 1 and 14", 400, field='days')
    if not budget:
        return create_error("Missing budget", 400, field='budget')
    norm_budget = normalize_budget_value(budget)
    norm_interests = normalize_interests(interests)
    if not norm_interests:
        return create_error("At least one interest required", 400, field='interests')
    if len(norm_interests) > 6:
        return create_error("No more than 6 interests allowed", 400, field='interests')
    # Build itinerary
    itinerary_response = build_itinerary(destination.strip(), days_int, norm_budget, norm_interests, travel_style or '')
    # Ensure response top-level keys
    top_keys = ['destination','days','budget','interests','travel_style','overview','itinerary','tips']
    response = {k: itinerary_response.get(k) for k in top_keys}
    status_code = 201 if days_int >= 7 else 200
    return jsonify(response), status_code


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
        timeout=600,
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
        result_response = requests.get(result_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=600)
        result_response.raise_for_status()
        result_data = result_response.json()
        payload = result_data.get("resp_data", result_data)
        status = payload.get("status")
        if status in {"success", "completed"}:
            image_urls = payload.get("image_list") or []
            images = payload.get("images") or []
            if image_urls:
                image_response = requests.get(image_urls[0], timeout=600)
                image_response.raise_for_status()
                with open(output_path, "wb") as image_file:
                    image_file.write(image_response.content)
                return request_id
            if images and images[0].get("b64_json"):
                with open(output_path, "wb") as image_file:
                    image_file.write(base64.b64decode(images[0]["b64_json"]))
                return request_id
            if images and images[0].get("url"):
                image_response = requests.get(images[0]["url"], timeout=600)
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