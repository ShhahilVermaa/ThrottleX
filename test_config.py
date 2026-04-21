import requests
import time

BASE = "http://localhost:8000"

print("--- Step 1: Check current config ---")
r = requests.get(f"{BASE}/admin/config")
print(r.json())

print("\n--- Step 2: Hit /api/data (limit=10) ---")
for i in range(1, 4):
    r = requests.get(f"{BASE}/api/data")
    print(f"Request {i} → {r.status_code} | Remaining: {r.headers.get('X-RateLimit-Remaining')}")

print("\n--- Step 3: Hot-update limit to 2 ---")
r = requests.post(f"{BASE}/admin/config/api/data", json={
    "limit": 2,
    "window": 60,
    "algorithm": "fixed"
})
print(r.json())

print("\n--- Step 4: Hit /api/data again (limit now 2) ---")
for i in range(1, 5):
    r = requests.get(f"{BASE}/api/data")
    print(f"Request {i} → {r.status_code} | Remaining: {r.headers.get('X-RateLimit-Remaining')}")

print("\n--- Step 5: Reset config back to default ---")
r = requests.delete(f"{BASE}/admin/config/api/data")
print(r.json())