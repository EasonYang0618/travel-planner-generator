import sys
import types
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

if "flask_cors" not in sys.modules:
    cors_module = types.ModuleType("flask_cors")
    cors_module.CORS = lambda app: app
    sys.modules["flask_cors"] = cors_module

import app as travel_app  # noqa: E402


def test_health_endpoint():
    client = travel_app.app.test_client()
    response = client.get("/health")
    assert response.status_code in (200, 201)
    assert response.get_json()["status"] == "ok"


def test_itinerary_endpoint_generates_user_destination():
    client = travel_app.app.test_client()
    response = client.post(
        "/api/itinerary",
        json={
            "destination": "Paris",
            "days": 2,
            "budget": "medium",
            "interests": ["culture", "food"],
            "travel_style": "balanced",
        },
    )
    data = response.get_json()
    assert response.status_code in (200, 201)
    assert data["destination"] == "Paris"
    assert data["days"] == 2
    assert len(data["itinerary"]) == 2
    assert "Paris" in str(data["overview"])


def test_itinerary_rejects_invalid_days():
    client = travel_app.app.test_client()
    response = client.post(
        "/api/itinerary",
        json={"destination": "Tokyo", "days": 30, "budget": "low"},
    )
    assert response.status_code == 400
    error_data = response.get_json()
    error_text = " ".join(str(part) for part in [error_data.get("error"), error_data.get("details"), error_data.get("errors")] if part)
    assert "days" in error_text


def test_destination_image_endpoint_uses_dynamic_destination(monkeypatch):
    client = travel_app.app.test_client()

    def fake_submit(prompt, output_path):
        Path(output_path).write_bytes(b"fake image bytes")
        return "fake-request-id"

    monkeypatch.setattr(travel_app, "submit_apifree_destination_image", fake_submit)
    response = client.post(
        "/api/destination-image",
        json={
            "destination": "Barcelona",
            "interests": ["food", "outdoor"],
            "travel_style": "relaxed",
        },
    )
    data = response.get_json()
    assert response.status_code in (200, 201)
    assert data["destination"] == "Barcelona"
    assert "Barcelona" in data["prompt"]
    assert data["image_url"].endswith("/barcelona.png")
    assert data["request_id"] == "fake-request-id"

    generated_file = APP_DIR / "generated_images" / "barcelona.png"
    if generated_file.exists():
        generated_file.unlink()
