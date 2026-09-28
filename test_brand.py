"""Manual helper: run this file directly while the Django server is running."""

import requests


if __name__ == "__main__":
    token = input("Paste your login token: ")
    response = requests.post(
        "http://127.0.0.1:8000/api/brands/create/",
        headers={"Authorization": f"Token {token}"},
        json={
            "name": "MyNewBrand",
            "industry": "Cosmetics",
            "description": "My first authenticated brand",
        },
    )
    print(response.status_code)
    print(response.text)
