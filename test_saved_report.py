"""Manual helper: run this file directly while the Django server is running."""

import requests


if __name__ == "__main__":
    token = input("Paste your login token: ")
    brand_id = 2
    response = requests.get(
        f"http://127.0.0.1:8000/api/ai/report/{brand_id}/",
        headers={"Authorization": f"Token {token}"},
    )
    print(response.status_code)
    print(response.text)
