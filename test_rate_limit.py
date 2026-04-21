import requests
import time

print("--- Token Bucket: /api/bucket ---")
print("Sending 15 requests instantly (capacity=10, refill=0.5/sec)")

for i in range(1, 16):
    r = requests.get("http://localhost:8000/api/bucket")
    remaining = r.headers.get("X-RateLimit-Remaining", "N/A")
    print(f"Request {i:2d} → Status: {r.status_code} | Tokens left: {remaining}")

print("\nWaiting 6 seconds for 3 tokens to refill...")
time.sleep(6)

print("\nSending 4 more requests after refill:")
for i in range(1, 5):
    r = requests.get("http://localhost:8000/api/bucket")
    remaining = r.headers.get("X-RateLimit-Remaining", "N/A")
    print(f"Request {i:2d} → Status: {r.status_code} | Tokens left: {remaining}")