import requests
import re
import base64
import time
import logging
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import hashlib

app = Flask(__name__)

logger = logging.getLogger(__name__)
CORS(app)

def normalize_budget_value(budget):
    """
    Normalize budget to one of: low, medium, high.
    Uses str(budget) as required.
    """
    s = str(budget).strip().lower()
    # if text labels provided
    if s in ("low", "medium", "high"):
        return s
    # try numeric interpretation
    try:
        v = float(s)
        if v <= 2:
            return "low"
        if v <= 4:
            return "medium"
        return "high"
    except Exception:
        # fallback default
        return "medium"

def normalize_interests(raw):
    """
    Normalize interests input to a list of lowercase strings with mappings:
    nature/outdoors -> outdoor
    museum -> museums
    history -> culture
    dining -> food
    preserve nightlife, family, shopping
    """
    mapping = {
        "nature": "outdoor",
        "outdoors": "outdoor",
        "outdoor": "outdoor",
        "museum": "museums",
        "museums": "museums",
        "history": "culture",
        "dining": "food",
        "food": "food",
        "nightlife": "nightlife",
        "family": "family",
        "shopping": "shopping",
        "culture": "culture",
    }
    result = []
    if raw is None:
        return result
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        items = [str(raw)]
    for it in items:
        if it is None:
            continue
        key = str(it).strip().lower()
        if not key:
            continue
        norm = mapping.get(key, key)
        if norm not in result:
            result.append(norm)
    return result

def make_activity(activity_source, time_window="activity", budget="medium", destination=""):
    """
    Build a consistent activity dict from either a POI dict or a category string.
    Must not use a dict as a key.
    """
    # budget multiplier
    mult = {"low": 0.6, "medium": 1.0, "high": 1.6}.get(str(budget), 1.0)
    # helper to get fields from dict safely
    if isinstance(activity_source, dict):
        title = activity_source.get("title") or activity_source.get("name") or "Local activity"
        name = activity_source.get("name") or title
        description = activity_source.get("description") or activity_source.get("desc") or f"A pleasant {title.lower()} in {destination}".strip()
        location = activity_source.get("location") or destination or "Central area"
        base_cost = activity_source.get("estimated_cost") or activity_source.get("cost") or activity_source.get("price") or 20.0
        # duration preference: minutes then hours
        duration_minutes = activity_source.get("duration_minutes")
        duration_hours = activity_source.get("duration_hours")
        if duration_minutes is None and duration_hours is not None:
            try:
                duration_minutes = int(float(duration_hours) * 60)
            except Exception:
                duration_minutes = 60
        if duration_minutes is None:
            duration_minutes = activity_source.get("duration") or 60
        try:
            estimated_cost = float(base_cost) * mult
        except Exception:
            estimated_cost = 20.0 * mult
        image_prompt = activity_source.get("image_prompt") or f"{title} in {destination}"
    else:
        # activity_source is a category string
        title = str(activity_source).title()
        name = title
        description = f"{title} experience in {destination} during the {time_window}."
        location = destination or "Central area"
        base_cost = 25.0
        duration_minutes = 90 if time_window == "afternoon" else 60
        estimated_cost = base_cost * mult
        image_prompt = f"{title} in {destination}"
    # assemble activity dict
    activity = {
        "title": str(title),
        "name": str(name),
        "description": str(description),
        "time_window": str(time_window),
        "duration_minutes": int(duration_minutes) if isinstance(duration_minutes, (int, float)) else 60,
        "estimated_cost": round(float(estimated_cost), 2),
        "location": str(location),
        "image_prompt": str(image_prompt),
    }
    return activity

def _det_hash(*parts):
    s = "|".join(str(p) for p in parts)
    h = hashlib.md5(s.encode("utf-8")).hexdigest()
    return int(h[:16], 16)

def build_itinerary(destination, days, budget, interests, travel_style):
    """
    Build an itinerary list containing exactly one dict per day.
    Each day includes day, morning, afternoon, evening, budget_note.
    """
    dest = destination or "Your destination"
    budget_norm = normalize_budget_value(budget)
    interests_list = normalize_interests(interests)
    # ensure at least one interest
    if not interests_list:
        interests_list = ["culture", "food"]

    # activity banks per interest with multiple concrete templates
    banks = {}

    banks["food"] = [
        {"title": "Breakfast street-food lane", "description": "Start with local breakfast specialties at a bustling lane.", "estimated_cost": 8, "duration_minutes": 45, "location": "Market Lane"},
        {"title": "Local market tasting", "description": "Sample regional produce and small bites at the morning market.", "estimated_cost": 15, "duration_minutes": 60, "location": "Main Market"},
        {"title": "Signature restaurant meal", "description": "Enjoy a curated tasting menu at a noted local restaurant.", "estimated_cost": 45, "duration_minutes": 90, "location": "Gourmet Quarter"},
        {"title": "Dessert and tea stop", "description": "Relax with a local dessert and tea at a cosy café.", "estimated_cost": 12, "duration_minutes": 40, "location": "Tea Street"},
        {"title": "Evening snack street", "description": "Walk a lively snack street sampling quick evening treats.", "estimated_cost": 10, "duration_minutes": 50, "location": "Snack Alley"},
    ]

    banks["outdoor"] = [
        {"title": "Lakefront walk", "description": "A gentle walk along the lakefront with scenic views.", "estimated_cost": 0, "duration_minutes": 60, "location": "Lakeside"},
        {"title": "City park reset", "description": "Relax in a spacious city park and observe local life.", "estimated_cost": 0, "duration_minutes": 50, "location": "Central Park"},
        {"title": "Scenic viewpoint", "description": "Short hike to a viewpoint overlooking the city.", "estimated_cost": 0, "duration_minutes": 80, "location": "Hilltop View"},
        {"title": "Garden or nature trail", "description": "Stroll through curated gardens and nature trails.", "estimated_cost": 5, "duration_minutes": 70, "location": "Botanic Garden"},
    ]

    banks["museums"] = [
        {"title": "City museum visit", "description": "Explore the city museum with local exhibits.", "estimated_cost": 12, "duration_minutes": 90, "location": "Museum District"},
        {"title": "Special exhibition", "description": "See a featured temporary exhibition.", "estimated_cost": 18, "duration_minutes": 75, "location": "Exhibit Hall"},
        {"title": "Architectural tour", "description": "Guided look at historic buildings and museum architecture.", "estimated_cost": 10, "duration_minutes": 60, "location": "Old Quarter"},
    ]

    banks["culture"] = [
        {"title": "Historic neighbourhoods", "description": "Wander through historic streets and learn local stories.", "estimated_cost": 0, "duration_minutes": 80, "location": "Historic District"},
        {"title": "Local cultural center", "description": "Visit a cultural center with performances or workshops.", "estimated_cost": 20, "duration_minutes": 90, "location": "Cultural Center"},
        {"title": "Guided heritage walk", "description": "Join a short guided walk focused on history and culture.", "estimated_cost": 12, "duration_minutes": 70, "location": "Heritage Trail"},
    ]

    banks["nightlife"] = [
        {"title": "Live music evening", "description": "Enjoy live local music at a neighbourhood venue.", "estimated_cost": 20, "duration_minutes": 120, "location": "Music Row"},
        {"title": "Cocktail bar crawl", "description": "Sample crafted cocktails at a trio of bars.", "estimated_cost": 35, "duration_minutes": 150, "location": "Bar Street"},
        {"title": "Local performance", "description": "Attend a short theatrical or dance performance.", "estimated_cost": 25, "duration_minutes": 90, "location": "Town Theatre"},
    ]

    banks["family"] = [
        {"title": "Interactive science center", "description": "Hands-on exhibits for all ages.", "estimated_cost": 18, "duration_minutes": 120, "location": "Science Center"},
        {"title": "Urban zoo visit", "description": "See animals and enjoy family-friendly shows.", "estimated_cost": 22, "duration_minutes": 150, "location": "City Zoo"},
        {"title": "Boat ride and picnic", "description": "Short boat trip with a picnic in a park.", "estimated_cost": 15, "duration_minutes": 100, "location": "River Pier"},
    ]

    banks["shopping"] = [
        {"title": "Crafts market browsing", "description": "Browse handmade goods and local crafts.", "estimated_cost": 10, "duration_minutes": 60, "location": "Craft Market"},
        {"title": "Boutique street walk", "description": "Explore boutique shops and designer stores.", "estimated_cost": 30, "duration_minutes": 90, "location": "Shopping Street"},
        {"title": "Outlet or local mall", "description": "Visit a larger shopping center for variety.", "estimated_cost": 20, "duration_minutes": 120, "location": "City Mall"},
    ]

    # Ensure every interest has a bank; fallback to culture
    for it in interests_list:
        if it not in banks:
            banks[it] = banks.get("culture", [])

    themes = [
        "Arrival and orientation",
        "Local culture and history",
        "Food and neighbourhoods",
        "Scenery and slower pace",
        "Hidden corners and markets",
        "Final highlights and favourites",
    ]

    itinerary = []
    for day in range(1, int(days) + 1):
        # pick a theme deterministically
        theme_idx = _det_hash(destination, day, travel_style) % len(themes)
        theme = themes[theme_idx]

        day_slots = {}
        slot_names = ["morning", "afternoon", "evening"]
        picked_sources = []
        total_cost = 0.0
        for slot in slot_names:
            # choose which interest to use for this slot deterministically
            interest_idx = _det_hash(destination, day, slot, travel_style) % len(interests_list)
            interest = interests_list[interest_idx]
            bank = banks.get(interest) or []
            # ensure non-empty bank
            if not bank:
                # fallback to a simple generated activity
                source = {"title": f"{interest.title()} experience", "description": f"A {interest} activity in {destination}", "estimated_cost": 10}
            else:
                pick_idx = _det_hash(destination, day, slot, interest) % len(bank)
                source = bank[pick_idx]
            # avoid exact duplicate selection within same day/slot by shifting if already picked
            attempt = 0
            while source in picked_sources and attempt < 3:
                pick_idx = (pick_idx + 1) % len(bank) if bank else pick_idx
                source = bank[pick_idx] if bank else source
                attempt += 1
            picked_sources.append(source)
            activity = make_activity(source, time_window=slot, budget=budget_norm, destination=destination)
            total_cost += float(activity.get("estimated_cost", 0.0))
            day_slots[slot] = activity

        budget_note = round(total_cost, 2)
        day_obj = {
            "day": day,
            "theme": theme,
            "morning": day_slots["morning"],
            "afternoon": day_slots["afternoon"],
            "evening": day_slots["evening"],
            "budget_note": budget_note,
        }
        itinerary.append(day_obj)

    return itinerary

def create_error(message, status_code=400, field=None):
    """
    Create a consistent JSON error response for validation failures.
    """
    payload = {"error": str(message)}
    if field:
        payload["fields"] = field
    return make_response(jsonify(payload), int(status_code))

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")
@app.route("/ui", methods=["GET"])
def ui():
    # Minimal frontend with stable IDs and JS functions required by tests.
    html = """
    <!doctype html>
    <html>
    <head><meta charset="utf-8"><title>Planner UI</title></head>
    <body>
    <h1>Travel Itinerary Planner</h1>
    <form id="plannerForm" onsubmit="return false;">
      <label>Destination: <input id="destination" name="destination"></label><br>
      <label>Days: <input id="days" name="days" type="number" min="1" max="14"></label><br>
      <label>Budget: <input id="budget" name="budget"></label><br>
      <label>Interests (comma): <input id="interests" name="interests"></label><br>
      <label>Travel style: <input id="travel_style" name="travel_style"></label><br>
      <button id="submitBtn" onclick="collectFormData()">Plan Trip</button>
    </form>
    <div id="formMessage"></div>
    <div id="errorMessage" style="color:red"></div>
    <div id="resultsContainer">
      <div id="daysContainer"></div>
    </div>
    <script>
    // Stable functions for tests
    function collectFormData() {
      setLoading(true);
      const data = {
        destination: document.getElementById('destination').value || '',
        days: parseInt(document.getElementById('days').value || '0', 10),
        budget: document.getElementById('budget').value || '',
        interests: (document.getElementById('interests').value || '').split(',').map(s=>s.trim()).filter(Boolean),
        travel_style: document.getElementById('travel_style').value || ''
      };
      if (!validateFormData(data)) { setLoading(false); return; }
      fetch('/api/itinerary', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(data)
      }).then(r=>r.json().then(js=>({status:r.status, body:js}))).then(r=>{
        setLoading(false);
        if (r.status >= 400) {
          showError(JSON.stringify(r.body));
        } else {
          renderItinerary(r.body);
        }
      }).catch(e=>{ setLoading(false); showError(String(e)); });
    }
    function validateFormData(data) {
      const err = [];
      if (!data.destination) err.push('destination required');
      if (!(Number.isInteger(data.days) && data.days >=1 && data.days<=14)) err.push('days 1-14');
      if (err.length) { showError(err.join('; ')); return false; }
      return true;
    }
    function setLoading(isLoading) {
      document.getElementById('formMessage').textContent = isLoading ? 'Loading...' : '';
    }
    function showError(msg) {
      document.getElementById('errorMessage').textContent = msg;
    }
    function formatActivityText(act) {
      if (!act) return '';
      if (typeof act === 'string') return act;
      // Build readable string from object fields.
      const title = act.title || act.name || '';
      const desc = act.description || '';
      const cost = (act.estimated_cost !== undefined) ? ('$'+act.estimated_cost) : '';
      return title + ' — ' + desc + (cost ? (' ('+cost+')') : '');
    }
    function renderActivity(container, act) {
      const div = document.createElement('div');
      div.textContent = formatActivityText(act);
      container.appendChild(div);
    }
    function renderDay(dayObj) {
      const dayDiv = document.createElement('div');
      dayDiv.className = 'day';
      const h = document.createElement('h3');
      h.textContent = 'Day ' + dayObj.day + ' — ' + (dayObj.theme || '');
      dayDiv.appendChild(h);
      const morning = document.createElement('div');
      morning.textContent = 'Morning: ';
      renderActivity(morning, dayObj.morning);
      dayDiv.appendChild(morning);
      const afternoon = document.createElement('div');
      afternoon.textContent = 'Afternoon: ';
      renderActivity(afternoon, dayObj.afternoon);
      dayDiv.appendChild(afternoon);
      const evening = document.createElement('div');
      evening.textContent = 'Evening: ';
      renderActivity(evening, dayObj.evening);
      dayDiv.appendChild(evening);
      const note = document.createElement('div');
      note.textContent = 'Budget note: ' + dayObj.budget_note;
      dayDiv.appendChild(note);
      return dayDiv;
    }
    function renderItinerary(resp) {
      document.getElementById('errorMessage').textContent = '';
      document.getElementById('formMessage').textContent = 'Itinerary for ' + (resp.destination || '') ;
      const container = document.getElementById('daysContainer');
      container.innerHTML = '';
      if (!resp.itinerary || !Array.isArray(resp.itinerary)) {
        showError('Invalid itinerary');
        return;
      }
      resp.itinerary.forEach(d=>{
        container.appendChild(renderDay(d));
      });
    }
    </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/generated_images/<path:filename>", methods=["GET"])
def generated_image_file(filename):
    return send_from_directory(os.path.join(app.root_path, "generated_images"), filename)

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    if not request.is_json:
        return create_error("Expected JSON body", 400)
    data = request.get_json()
    # Validate required fields
    dest = data.get("destination")
    days = data.get("days")
    budget = data.get("budget")
    interests = data.get("interests")
    travel_style = data.get("travel_style", "balanced")
    if not dest or not str(dest).strip():
        return create_error("destination is required", 400, field="destination")
    # days must be integer between 1 and 14
    try:
        days_int = int(days)
    except Exception:
        return create_error("days must be an integer", 400, field="days")
    if days_int < 1 or days_int > 14:
        return create_error("days must be between 1 and 14", 400, field="days")
    # interests should be list or convertible
    if interests is None:
        interests_list = []
    else:
        interests_list = interests
    # Build itinerary
    try:
        itinerary = build_itinerary(dest, days_int, budget, interests_list, travel_style)
    except Exception as e:
        return create_error("Failed to build itinerary: " + str(e), 500)
    # Tips - simple deterministic tips based on travel style
    tips_map = {
        "relaxed": ["Take time at cafés and avoid tight schedules.", "Prioritise one major site per day."],
        "active": ["Wear comfortable shoes for walks.", "Book activities in advance where possible."],
        "balanced": ["Mix guided tours with independent exploration.", "Allow a free evening each few days."],
    }
    tips = tips_map.get(str(travel_style).lower(), tips_map["balanced"])
    response_payload = {
        "destination": str(dest),
        "days": days_int,
        "budget": budget,
        "interests": normalize_interests(interests_list),
        "travel_style": travel_style,
        "overview": f"A {days_int}-day trip plan for {dest}.",
        "itinerary": itinerary,
        "tips": tips,
    }
    return make_response(jsonify(response_payload), 201)


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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)