"""Manual helper: run this file directly while the Django server is running."""

import requests


if __name__ == "__main__":
    token = input("Paste User B's login token: ")
    response = requests.post(
        "http://127.0.0.1:8000/api/brands/create/",
        headers={"Authorization": f"Token {token}"},
        json={
            "name": "UserBBrand",
            "industry": "Cosmetics",
            "description": "Brand created by User B for security testing",
        },
    )
    print(response.status_code)
    print(response.text)
