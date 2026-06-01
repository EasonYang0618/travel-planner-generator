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
    s = str(budget).strip().lower()
    if s in ("low", "budget", "cheap"):
        return "low"
    if s in ("high", "premium", "expensive"):
        return "high"
    return "medium"

def normalize_interests(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [raw]
    else:
        items = list(raw)
    out = []
    for it in items:
        if not isinstance(it, str):
            continue
        s = it.strip().lower()
        if s in ("nature", "outdoors", "outdoor", "outdoors"):
            out.append("outdoor")
        elif s == "museum":
            out.append("museums")
        elif s == "history":
            out.append("culture")
        elif s == "dining":
            out.append("food")
        elif s in ("nightlife", "family", "shopping", "food", "culture", "museums", "outdoor"):
            out.append(s)
        else:
            out.append(s)
    # deduplicate preserving order
    seen = set()
    res = []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res

def make_activity(activity_source, time_window="activity", budget="medium", destination=""):
    # Accept dict POI or string category/name
    if isinstance(activity_source, dict):
        title = activity_source.get("title") or activity_source.get("name") or "Local Activity"
        description = activity_source.get("description") or activity_source.get("desc") or ""
        duration = activity_source.get("duration_minutes") or activity_source.get("duration_hours")
        base_cost = activity_source.get("estimated_cost", 20)
        location = activity_source.get("location") or activity_source.get("location_hint") or destination or "city center"
    else:
        title = str(activity_source)
        description = f"A typical {title.lower()} experience in {destination}" if destination else f"A {title.lower()} experience"
        duration = 60
        base_cost = 20
        location = destination or "city center"
    # Normalize budget multiplier
    b = normalize_budget_value(budget)
    mult = {"low": 0.7, "medium": 1.0, "high": 1.4}.get(b, 1.0)
    estimated_cost = round(float(base_cost) * mult, 2)
    duration_minutes = duration if isinstance(duration, int) else (int(duration)*60 if isinstance(duration, float) else (duration or 60))
    return {
        "title": title,
        "description": description,
        "time_window": time_window,
        "duration_minutes": int(duration_minutes),
        "estimated_cost": estimated_cost,
        "location": location,
        "image_prompt": f"{title} in {destination}".strip()
    }

def create_error(message, status_code=400, field=None):
    err = {"error": message}
    if field:
        err["field"] = field
    return jsonify(err), status_code

def build_itinerary(destination, days, budget, interests, travel_style):
    # Build per-interest banks (14 morning/14 afternoon/14 evening per interest)
    # Templates for each interest
    banks = {}
    def make_bank(name, morning_bases, afternoon_bases, evening_bases):
        banks[name] = {
            "morning": [{"title": t, "description": f"{t} to start your morning."} for t in morning_bases],
            "afternoon": [{"title": t, "description": f"{t} as a daytime activity."} for t in afternoon_bases],
            "evening": [{"title": t, "description": f"{t} perfect for the evening."} for t in evening_bases],
        }
    # Food bank
    food_morning = ["Local Breakfast Market","Tea House Tasting","Bakery Stop","Neighborhood Noodle Stop","Morning Produce Market","Coffee Roastery Visit","Street-Food Breakfast Lane","Pastry Sampling Walk","Riverside Cafe Breakfast","Food Hall Morning Tour","Traditional Breakfast Table","Market Coffee & Buns","Casual Breakfast Counter","Sunrise Cafe Session"]
    food_afternoon = ["Casual Lunch Counter","Cooking Mini-Workshop","Dessert Cafe Visit","Signature Restaurant Lunch","Food Hall Tasting","Neighborhood Food Walk","Market Tasting Session","Farm-to-Table Lunch","Culinary Museum Stop","Bakery Workshop","Street Food Sampling","Tea Pairing Session","Lunch at Riverside","Local Deli Stop"]
    food_evening = ["Evening Snack Street","Supper Club","Food Night Market","Chef's Table Experience","Rooftop Dinner","Small-Plate Crawl","Night Food Stalls","Local Dinner Alley","Seafood Night Market","Late Dessert Crawl","Evening Tea & Sweets","Nighttime Food Court","Candlelight Bistro","Street-food Evening Loop"]
    make_bank("food", food_morning, food_afternoon, food_evening)
    # Outdoor bank
    out_morning = ["Lakefront Walk","City Park Reset","Garden Trail","Botanical Corner Stroll","Sunrise Hill Path","Old Street Photo Walk","Picnic Stop Morning","Riverside Cycling Start","Seaside Promenade","Forest Edge Walk","Meadow Path Walk","Riverbank Jog","Historic Garden Walk","Quiet Canal Walk"]
    out_afternoon = ["Scenic Viewpoint","Garden Trail Extended","River Walk","Botanical Corner","Hilltop Picnic","Scenic Boat Ride","Park Exploration","Countryside Lane","Wetland Boardwalk","Heritage Park Visit","Panoramic Lookout","Coastal Cliff Walk","Lakeside Loop","Stately Tree Avenue"]
    out_evening = ["Sunset Promenade","Evening Waterfront Walk","Harbor Stroll At Dusk","Lakeside Twilight Walk","Golden Hour Viewpoint","Evening Boardwalk","Riverside Lantern Walk","Sunset Hill Path","Seafront Stroll","Nighttime Promenade","Twilight Garden Visit","Moonlight Shore Walk","Evening Pier Walk","Harbor Lights Walk"]
    make_bank("outdoor", out_morning, out_afternoon, out_evening)
    # Culture bank
    cult_morning = ["Heritage Lane Walk","Architectural Stroll","Local History Walk","Historical Church Visit","Old Town Orientation","Monument Walk","Cultural Quarter Stroll","Town Square Stories","Artisan Street Walk","Historical Market Morning","Guided Heritage Talk","Legacy Buildings Walk","Storytelling Corner Visit","Historical House Exterior Tour"]
    cult_afternoon = ["City Museum Visit","Local History Museum","Cultural Center Tour","Archive Exhibit","Gallery Walk","Heritage Workshop","Artist Studio Visit","Traditional Craft Demonstration","Town Museum Afternoon","Historical House Interior","Museum Special Exhibit","Civic Heritage Tour","Folklore Workshop","Community Museum Stop"]
    cult_evening = ["Cultural Performance","Traditional Music Night","Folklore Show","Evening Storytelling Session","Heritage Light Walk","Local Theatre Performance","Classical Concert","Dance Evening","Late Museum Event","Cultural Film Night","Nighttime Performance","Craft Night Market","Evening Cultural Salon","Community Music Night"]
    make_bank("culture", cult_morning, cult_afternoon, cult_evening)
    # Museums (distinct naming)
    mus_morning = ["Small Museum Morning","Curator's Talk","Museum Highlights Tour","Gallery Opening Walk","Special Exhibit Preview","Design Museum Start","Museum Collections Start","Maritime Museum Morning","Museum Sketching Session","Archive Morning Visit","Anthropology Displays","Science Center Morning","Local Gallery Breakfast Session","Museum Rooftop Cafe"]
    mus_afternoon = ["Major Museum Visit","Contemporary Gallery","Interactive Exhibit","Maritime Exhibit","Art Deco Museum","Science Hall Visit","Museum Workshops","Children's Discovery Zone","Temporary Exhibit Tour","Guided Curator Tour","Museum Sculpture Garden","Historical Exhibit","Design Lab Afternoon","Photography Exhibit"]
    mus_evening = ["Museum Late Night","Gallery Opening Night","Evening Exhibit Talk","Art Reception","Curator Lecture Evening","Museum Concert","Night Gallery Crawl","Artist Talk Night","After-hours Tour","Museum Film Screening","Open Mic at Gallery","Evening Archive Talk","Museum Night Program","Gallery Salon"]
    make_bank("museums", mus_morning, mus_afternoon, mus_evening)
    # Nightlife bank
    night_morning = ["Leisurely Brunch Spot","Late Breakfast Cafe","Recovery Morning Coffee","Lazy Morning Market","Chill Daytime Lounge","Brunch Courtyard","Coffee & People Watch","Late Bakery Visit","Sunday Brunch Route","Brunch Terrace","Morning Cocktail Mocktail","Brunch Pop-up","Weekend Brunch Lane","Brunch Garden"]
    night_afternoon = ["Vinyl Bar Visit","Cocktail Workshop (afternoon)","Distillery Tour","Rooftop Visit","Live Music Matinee","Barbecue Street Lunch","Jazz Cafe Afternoon","Speakeasy Tour (day)","Mixology Class (day)","Brewer's Tour","Afternoon Taproom","Rooftop Bar Walk","Music Venue Tour","Cultural Bar History"]
    night_evening = ["Rooftop Cocktails","Live Music Night","Night Market Crawl","Cocktail Bar Hopping","Late-night Jazz","Dance Club Night","Evening Speakeasy","Rooftop DJ Set","Late Street Food & Drinks","Bottle Bar Experience","Night Concert","Stand-up Comedy Night","Evening Pub Quiz","Nighttime Rooftop Lounge"]
    make_bank("nightlife", night_morning, night_afternoon, night_evening)
    # Family bank
    fam_morning = ["Playground Morning","Kid-friendly Museum","Puppet Show Matinee","Family Farm Visit","Interactive Science Morning","Aquarium Morning","Children's Garden","Family Bike Ride","Zoo Morning Visit","Storytime Session","Family Cooking Class","Soft-play Morning","Park with Carousel","Hands-on Workshop"]
    fam_afternoon = ["Theme Park Afternoon","Aquarium Visit","Interactive Center","Boat Ride for Families","Family Picnic","Children's Workshop","Local Farm Experience","Science Center Afternoon","Educational Show","Mini-golf","Family Market Visit","Ice-cream Trail","Boat Picnic","Family Friendly Walk"]
    fam_evening = ["Evening Puppet Show","Family Movie Night","Children's Storytime Evening","Night Aquarium Visit","Family-friendly Dinner","Outdoor Cinema","Evening Light Show for Kids","Board Game Cafe Evening","Family Night Market","Stargazing Event","Family Concert","Kid-friendly Theatre","Evening Carousel","Family Lantern Walk"]
    make_bank("family", fam_morning, fam_afternoon, fam_evening)
    # Shopping bank
    shop_morning = ["Artisan Market Stroll","Boutique Street Morning","Antique Lane Visit","Local Market Morning","Design District Walk","Vintage Store Hunt","Farmers Market","Crafts Lane","Market Coffee & Stroll","Souvenir Lane","Morning Flea Market","Handmade Goods Walk","Textile Market","Local Designer Showroom"]
    shop_afternoon = ["Shopping Arcade","Boutique Hopping","Designer Outlet Visit","Shopping Mall Stroll","Handicraft Workshop","Market Bargain Afternoon","Jewelry Lane","Bookshop Crawl","Artisan Workshops","Department Store Visit","Specialty Food Shops","Craft Market Afternoon","Market Cooking Gear","Local Maker Fair"]
    shop_evening = ["Night Market Shopping","Evening Boutique Openings","Artisan Night Fair","Late Shopping Arcade","Evening Craft Market","Designer Pop-up Night","Late Bookshop Event","Shopping Street Lights","Night Bazaar","Evening Souvenir Hunt","Handmade Night Market","Fashion Night Out","Night Market Tasting","Evening Collectibles Fair"]
    make_bank("shopping", shop_morning, shop_afternoon, shop_evening)

    # Ensure every requested interest has a bank; if unknown interest, fallback to culture-like bank
    for it in interests:
        if it not in banks:
            make_bank(it,
                      [f"{it.title()} Morning Walk {n}" for n in range(1,15)],
                      [f"{it.title()} Afternoon Experience {n}" for n in range(1,15)],
                      [f"{it.title()} Evening Event {n}" for n in range(1,15)])

    used_titles_by_slot = {"morning": set(), "afternoon": set(), "evening": set()}
    rotation_index = {"morning": 0, "afternoon": 0, "evening": 0}
    itinerary = []
    dest_sum = sum(ord(c) for c in destination) if destination else 0
    b = normalize_budget_value(budget)
    for day in range(1, days+1):
        slot_objs = {}
        theme_options = ["arrival and orientation","local culture","food and neighbourhoods","scenery and slower pace","hidden corners","final highlights","heritage focus","market day","relaxation day","active exploration"]
        theme = theme_options[(day + dest_sum) % len(theme_options)]
        for slot_i, slot in enumerate(["morning","afternoon","evening"]):
            # pick interest for this slot deterministically
            if interests:
                interest = interests[(day + slot_i + dest_sum) % len(interests)]
            else:
                interest = "culture"
            bank = banks.get(interest, banks.get("culture"))
            slot_bank = bank.get(slot, [])
            if not slot_bank:
                slot_bank = [{"title": f"{interest.title()} {slot.title()} Experience {i}", "description": ""} for i in range(14)]
            start = (dest_sum + day + slot_i + len(interest)) % len(slot_bank)
            chosen = None
            # Find a title not used in this slot
            for offset in range(len(slot_bank)):
                idx = (start + offset) % len(slot_bank)
                title = slot_bank[idx].get("title")
                if title not in used_titles_by_slot[slot]:
                    chosen = slot_bank[idx]
                    used_titles_by_slot[slot].add(title)
                    rotation_index[slot] = (rotation_index[slot] + 1) % len(slot_bank)
                    break
            if chosen is None:
                # all used, allow reuse but add revisit note in description
                idx = start
                chosen = slot_bank[idx].copy()
                chosen_title = chosen.get("title")
                chosen_desc = chosen.get("description","")
                chosen = chosen.copy()
                chosen["description"] = f"{chosen_desc} Revisited on day {day} as part of a deeper look."
            act = make_activity(chosen, time_window=slot, budget=b, destination=destination)
            slot_objs[slot] = act
        # Budget note derived from sum of estimated costs
        day_cost = slot_objs["morning"]["estimated_cost"] + slot_objs["afternoon"]["estimated_cost"] + slot_objs["evening"]["estimated_cost"]
        note = f"Estimated total for the day: ${round(day_cost,2)} for a {b} budget."
        itinerary.append({
            "day": day,
            "theme": theme,
            "morning": slot_objs["morning"],
            "afternoon": slot_objs["afternoon"],
            "evening": slot_objs["evening"],
            "budget_note": note
        })
    return itinerary

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
def api_itinerary():
    data = request.get_json(silent=True)
    if not data:
        return create_error("Invalid JSON body", 400)
    destination = data.get("destination")
    days = data.get("days")
    budget = data.get("budget", "medium")
    interests = normalize_interests(data.get("interests") or [])
    travel_style = data.get("travel_style", "balanced")
    # Validate destination
    if not destination or not isinstance(destination, str) or not destination.strip():
        return create_error("destination is required", 400, field="destination")
    # Validate days
    try:
        days_int = int(days)
    except Exception:
        return create_error("days must be an integer between 1 and 14", 400, field="days")
    if days_int < 1 or days_int > 14:
        return create_error("days must be between 1 and 14", 400, field="days")
    budget_norm = normalize_budget_value(budget)
    # Build itinerary
    itinerary = build_itinerary(destination.strip(), days_int, budget_norm, interests or ["culture"], travel_style)
    overview = f"A {days_int}-day {travel_style} trip to {destination.strip()} focused on {', '.join(interests) if interests else 'general experiences'}."
    tips = [
        "Carry a refillable water bottle and comfortable shoes.",
        "Check opening hours for museums and markets in advance.",
        "Allow extra time for transit between neighbourhoods.",
        f"If you prefer a {travel_style} pace, adjust morning/afternoon activities accordingly."
    ]
    response = {
        "destination": destination.strip(),
        "days": days_int,
        "budget": budget_norm,
        "interests": interests,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": itinerary,
        "tips": tips
    }
    return jsonify(response), 201


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
    app.run(host='0.0.0.0', port=port)