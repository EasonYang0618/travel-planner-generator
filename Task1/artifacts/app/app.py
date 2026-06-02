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
    s = str(budget)
    try:
        v = float(s)
    except Exception:
        return "medium"
    if v < 50:
        return "low"
    if v < 150:
        return "medium"
    return "high"

def normalize_interests(raw):
    if raw is None:
        return []
    out = []
    mapping = {"nature":"outdoor","outdoors":"outdoor","museum":"museums","history":"culture","dining":"food"}
    if isinstance(raw, str):
        items = [raw]
    else:
        items = list(raw)
    for it in items:
        try:
            key = str(it).strip().lower()
        except Exception:
            continue
        out.append(mapping.get(key, key))
    # keep only allowed forms and common ones
    return [i for i in out if i]

def make_activity(activity_source, time_window="activity", budget="medium", destination=""):
    # Accept tuple/list in order (title, description, estimated_cost, location, duration_minutes)
    title = ""
    description = ""
    est = 20
    location = destination or "City Center"
    duration = 60
    if isinstance(activity_source, dict):
        title = activity_source.get("title") or activity_source.get("name") or ""
        description = activity_source.get("description") or activity_source.get("desc") or ""
        try:
            est = float(activity_source.get("estimated_cost", activity_source.get("cost", 20)))
        except Exception:
            est = 20
        location = activity_source.get("location", location)
        duration = int(activity_source.get("duration_minutes", activity_source.get("duration_hours", duration)))
    elif isinstance(activity_source, (list, tuple)):
        try:
            title, description, est, location, duration = activity_source
        except (TypeError, ValueError):
            # fallback if wrong structure
            try:
                title = str(activity_source)
                description = f"{title} in {destination}"
            except Exception:
                title = "Activity"
            est = 20
            location = destination or "City Center"
            duration = 60
        try:
            est = float(est)
        except (TypeError, ValueError):
            est = 20.0
    else:
        # string
        title = str(activity_source)
        description = f"{title} around {destination}"
        est = 20.0
        location = destination or "City Center"
        duration = 60
    mult = {"low":0.7,"medium":1.0,"high":1.5}.get(budget,1.0)
    estimated_cost = round(est * mult, 2)
    return {
        "title": title,
        "name": title,
        "description": description,
        "time_window": time_window,
        "duration_minutes": int(duration),
        "estimated_cost": estimated_cost,
        "location": location
    }

def create_error(message, status_code=400, field=None):
    payload = {"error": message}
    if field:
        payload["fields"] = {field: message}
    return jsonify(payload), status_code

def build_itinerary(destination, days, budget, interests, travel_style):
    budget_norm = normalize_budget_value(budget)
    interests = interests or []
    if not interests:
        interests = ["culture"]
    # phrase banks per interest
    prefixes = ["Local", "Hidden", "Signature", "Historic", "Scenic", "Neighbourhood", "Authentic"]
    slot_modifiers = ["Return to", "Deeper into", "Fresh look at", "Extended visit to", "Evening revisit"]
    banks = {}
    # helper to create pool tuples: (title, description, base_cost, location, duration_minutes)
    def pool_for(name, morning_phrases, afternoon_phrases, evening_phrases, base_loc="Central"):
        m = []
        a = []
        e = []
        for p in morning_phrases:
            for pre in prefixes:
                title = f"{pre} {p[0]}"
                desc = p[1].format(destination=destination)
                m.append((title, desc, p[2], p[3] or base_loc, p[4]))
        for p in afternoon_phrases:
            for pre in prefixes:
                title = f"{pre} {p[0]}"
                desc = p[1].format(destination=destination)
                a.append((title, desc, p[2], p[3] or base_loc, p[4]))
        for p in evening_phrases:
            for pre in prefixes:
                title = f"{pre} {p[0]}"
                desc = p[1].format(destination=destination)
                e.append((title, desc, p[2], p[3] or base_loc, p[4]))
        return {"morning": m, "afternoon": a, "evening": e}
    # Define per-interest phrase lists (phrase, description_template, base_cost, location, duration_minutes)
    food_m = [("Breakfast Market","Savour local morning bites at a bustling market in {destination}",15,"Food Quarter",45),
              ("Tea House Tasting","Sample traditional teas at a neighbourhood tea house in {destination}",10,"Tea Lane",30),
              ("Bakery Stop","Fresh pastries and coffee at a popular bakery in {destination}",8,"Bakery Row",30)]
    food_a = [("Cooking Mini-Workshop","Hands-on cooking session featuring local flavours in {destination}",45,"Culinary Studio",90),
              ("Casual Lunch Counter","Try a popular casual lunch spot loved by locals in {destination}",12,"Midtown",60),
              ("Market Tasting Route","Stall-to-stall tasting through a daytime food market in {destination}",18,"Market District",75)]
    food_e = [("Evening Snack Street","Explore night snacks and small plates along a lively street in {destination}",20,"Night Food Street",60),
              ("Signature Restaurant Meal","A seated experience at a well-regarded local restaurant in {destination}",60,"Dining District",120),
              ("Dessert Cafe","Sweet treats and relaxed evening cafe time in {destination}",15,"Dessert Alley",50)]
    outdoor_m = [("Lakefront Walk","Gentle morning walk beside the lake in {destination}",0,"Lakeside",40),
                 ("City Park Reset","Refresh in a city park with local flora in {destination}",0,"City Park",50),
                 ("Garden Trail","Morning stroll through garden paths in {destination}",0,"Botanical Corner",45)]
    outdoor_a = [("Scenic Viewpoint","Hike or walk to a viewpoint with city vistas in {destination}",0,"Hilltop",60),
                 ("Riverside Cycling","Cycle along scenic riverfront paths in {destination}",10,"Riverbank",90),
                 ("Picnic Stop","Relax with a packed picnic in a scenic spot in {destination}",8,"Green Meadow",60)]
    outdoor_e = [("Sunset Promenade","Watch the sunset from a waterfront promenade in {destination}",0,"Promenade",40),
                 ("Evening Waterfront Walk","Calm evening stroll along lit waterfront in {destination}",0,"Harbor",35),
                 ("Night Lights Stroll","See illuminated cityscapes on an evening walk in {destination}",0,"Old Quay",45)]
    culture_m = [("Museum Visit","Morning at a museum exploring local collections in {destination}",20,"Museum Quarter",90),
                 ("Heritage Lane Walk","Walk historic lanes lined with plaques and architecture in {destination}",5,"Old Town",60),
                 ("Local Crafts Morning","Visit artisan workshops and small studios in {destination}",15,"Artisan Row",75)]
    culture_a = [("Gallery Circuit","Afternoon visits to galleries and special exhibits in {destination}",18,"Gallery Row",90),
                 ("Historic House Tour","Guided tour of a preserved historic house in {destination}",12,"Heritage Area",60),
                 ("Cultural Centre Workshop","Participate in a craft or music workshop in {destination}",25,"Cultural Hub",90)]
    culture_e = [("Live Performance","Attend a local performance or small concert in {destination}",30,"Theatre Quarter",120),
                 ("Evening Light Walk","See landmarks beautifully lit after dark in {destination}",0,"Landmark Promenade",50),
                 ("Night Market Craft Finds","Browse crafts and souvenirs at an evening market in {destination}",10,"Night Bazaar",60)]
    museums_m = culture_m
    museums_a = culture_a
    museums_e = culture_e
    nightlife_m = [("Late Start Brunch","Relaxed late morning with a hearty brunch in {destination}",15,"Brunch Lane",75),
                   ("Daytime Bar Tour Intro","Meet bartenders and learn about local spirits in a daytime session in {destination}",12,"Bar Row",60),
                   ("Music Cafe Visit","Chill in a music cafe featuring daytime sets in {destination}",8,"Music Corner",60)]
    nightlife_a = [("Record Store & Cafe","Afternoon crate-digging at local record stores and cafes in {destination}",10,"Music District",70),
                   ("Rooftop Preview","Visit a rooftop for daytime views preparatory to evening venues in {destination}",5,"Rooftop Alley",45),
                   ("Cocktail Lab Session","Learn cocktail basics in an afternoon session in {destination}",30,"Mix Lab",90)]
    nightlife_e = [("Live Music Night","Enjoy live music at a local venue in {destination}",25,"Live Venues",150),
                   ("Cocktail Bar Crawl","An evening of signature cocktails at curated bars in {destination}",40,"Bar Quarter",180),
                   ("Rooftop Drinks","Sunset and night-time drinks at a rooftop bar in {destination}",35,"Rooftop",120)]
    family_m = [("Interactive Museum","Hands-on exhibits perfect for families in {destination}",15,"Family Museum",90),
                ("Animal Farm Visit","Meet local farm animals and enjoy family activities in {destination}",10,"Green Farm",80),
                ("Puppet Workshop","Child-friendly workshop to make simple puppets in {destination}",12,"Workshop Hall",60)]
    family_a = [("Science Centre","Explore kid-friendly science exhibits in {destination}",14,"Science Park",90),
                ("Playground Picnic","Afternoon at a popular playground with picnic spots in {destination}",0,"Playground",60),
                ("Boat Ride","Gentle family boat trip along calm waters in {destination}",20,"Harbor",45)]
    family_e = [("Evening Storytime","Local storytelling and low-key evening activities for families in {destination}",0,"Story Hall",45),
                ("Night Light Show","Family-friendly light show or projection in {destination}",10,"Square",40),
                ("Casual Family Dinner","A relaxed family restaurant with kids' options in {destination}",20,"Family Eats",60)]
    shopping_m = [("Antique Lane","Morning browsing in antique and vintage shops in {destination}",0,"Antique Row",60),
                  ("Local Market Finds","Hunt for local goods at morning markets in {destination}",10,"Market District",75),
                  ("Boutique Window Walk","Explore boutique windows and small shops in {destination}",0,"Shopping Street",50)]
    shopping_a = [("Mall & Crafts","Visit modern malls and craft-focused lanes in {destination}",20,"Mall Area",120),
                  ("Collector Shops","Seek out specialty shops and collectors' stores in {destination}",15,"Collector Row",90),
                  ("Handmade Market","Support local makers at an artisan market in {destination}",12,"Maker Market",80)]
    shopping_e = [("Night Market Shopping","Evening market stalls with unique finds in {destination}",15,"Night Bazaar",90),
                  ("Evening Boutiques","Shops open late with evening ambience in {destination}",20,"Boutique Lane",80),
                  ("Souvenir Stroll","Collect keepsakes along a lit shopping stretch in {destination}",10,"Old Market",60)]
    interest_banks = {
        "food": pool_for("food", food_m, food_a, food_e, "Food Quarter"),
        "outdoor": pool_for("outdoor", outdoor_m, outdoor_a, outdoor_e, "Outdoor Area"),
        "culture": pool_for("culture", culture_m, culture_a, culture_e, "Cultural District"),
        "museums": pool_for("museums", museums_m, museums_a, museums_e, "Museum Quarter"),
        "nightlife": pool_for("nightlife", nightlife_m, nightlife_a, nightlife_e, "Night Quarter"),
        "family": pool_for("family", family_m, family_a, family_e, "Family Zone"),
        "shopping": pool_for("shopping", shopping_m, shopping_a, shopping_e, "Shopping Street")
    }
    # ensure interests exist in banks; fallback to culture
    banks = {k:v for k,v in interest_banks.items()}
    used_titles_by_slot = {"morning": set(), "afternoon": set(), "evening": set()}
    rotation_index = {"morning":0, "afternoon":0, "evening":0}
    itinerary = []
    themes = ["arrival and orientation","local culture","food and neighbourhoods","scenery and slower pace","hidden corners","final highlights","exploration and markets"]
    # selection function
    def select_activity_for(day, slot, interest):
        pool = banks.get(interest, banks.get("culture"))[slot]
        # deterministic order: pool already in prefix-major order
        for item in pool:
            title = item[0]
            if title not in used_titles_by_slot[slot]:
                used_titles_by_slot[slot].add(title)
                return make_activity(item, time_window=slot, budget=budget_norm, destination=destination)
        # all used -> reuse with day-specific modifier
        idx = (day - 1) % len(slot_modifiers)
        modifier = slot_modifiers[idx]
        # pick next base by rotation_index
        base = pool[rotation_index[slot] % len(pool)]
        rotation_index[slot] = (rotation_index[slot] + 1) % len(pool)
        new_title = f"{modifier} {base[0]}"
        new_desc = f"{base[1]} — {modifier} exploration for day {day} in {destination}"
        modified = (new_title, new_desc, base[2], base[3], base[4])
        return make_activity(modified, time_window=slot, budget=budget_norm, destination=destination)
    for d in range(1, days+1):
        theme = themes[(d-1) % len(themes)]
        day_acts = {}
        # rotate interest choice by slot to increase variety
        for si, slot in enumerate(["morning","afternoon","evening"]):
            if interests:
                interest = interests[(d-1 + si) % len(interests)]
            else:
                interest = "culture"
            act = select_activity_for(d, slot, interest)
            day_acts[slot] = act
        budget_note = {"low":"Budget-friendly choices and local eats","medium":"Balanced spending with a few highlights","high":"Room for premium experiences and signature meals"}.get(budget_norm,"Balanced")
        itinerary.append({
            "day": d,
            "theme": theme,
            "morning": day_acts["morning"],
            "afternoon": day_acts["afternoon"],
            "evening": day_acts["evening"],
            "budget_note": budget_note
        })
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
    data = request.get_json(silent=True) or {}
    destination = data.get("destination")
    days = data.get("days")
    budget = data.get("budget")
    interests_raw = data.get("interests") or data.get("interest")
    travel_style = data.get("travel_style", "balanced")
    # validate
    if not destination:
        return create_error("destination is required", 400, "destination")
    try:
        days_i = int(days)
    except Exception:
        return create_error("days must be an integer", 400, "days")
    if days_i < 1 or days_i > 14:
        return create_error("days must be between 1 and 14", 400, "days")
    # normalize interests
    interests = normalize_interests(interests_raw)
    if not interests:
        interests = ["culture"]
    # build
    itinerary = build_itinerary(destination, days_i, budget, interests, travel_style)
    overview = f"{days_i}-day trip to {destination} focused on {', '.join(interests)} with a {normalize_budget_value(budget)} budget and {travel_style} travel style."
    tips = [
        "Pack a comfortable pair of shoes for walking-focused days.",
        "Check opening hours for museums and markets.",
        "Reserve popular restaurants in advance if traveling on weekends."
    ]
    result = {
        "destination": destination,
        "days": days_i,
        "budget": normalize_budget_value(budget),
        "interests": interests,
        "travel_style": travel_style,
        "overview": overview,
        "itinerary": itinerary,
        "tips": tips
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
    port = int(os.environ.get("PORT", "5000"))
    app.run(host='0.0.0.0', port=port)