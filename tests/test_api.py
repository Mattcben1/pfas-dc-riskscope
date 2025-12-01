 from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200

def test_simulate_location():
    r = client.post("/simulate-location", json={"lat": 39.0, "lon": -77.0})
    assert r.status_code == 200
    assert "state" in r.json()

