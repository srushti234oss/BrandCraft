"""Manual helper: run this file directly while the Django server is running."""

import requests


if __name__ == "__main__":
    response = requests.post(
        "http://127.0.0.1:8000/api/ai/login/",
        json={"username": "testuser_b", "password": "TestUserBPass456!"},
    )
    print(response.status_code)
    print(response.text)
