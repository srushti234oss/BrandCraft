"""Manual helper: run this file directly while the Django server is running."""

import requests


if __name__ == "__main__":
    token = input("Paste your login token: ")
    response = requests.post(
        "http://127.0.0.1:8000/api/ai/start/",
        headers={"Authorization": f"Token {token}"},
        json={"brand_id": 2, "answer": ""},
    )
    print(response.status_code)
    print(response.text)
