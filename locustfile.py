from locust import HttpUser, task, between
import random

class RateLimitUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        # Each simulated user gets a unique ID
        # We send it as a header — middleware will use this instead of IP
        self.user_id = f"user_{random.randint(1, 10000)}"
        self.headers = {"X-User-ID": self.user_id}

    @task(3)
    def hit_fixed_window(self):
        with self.client.get(
            "/api/data",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")

    @task(2)
    def hit_sliding_window(self):
        with self.client.get(
            "/api/sliding",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")

    @task(1)
    def hit_token_bucket(self):
        with self.client.get(
            "/api/bucket",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")