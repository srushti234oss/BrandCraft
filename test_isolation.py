"""Manual helper: run this file directly while the Django server is running."""

import requests


if __name__ == "__main__":
    token = input("Paste User A's login token: ")
    response = requests.get(
        "http://127.0.0.1:8000/api/ai/report/4/",
        headers={"Authorization": f"Token {token}"},
    )
    print(response.status_code)
    print(response.text)
