import requests

url = "http://127.0.0.1:8000/api/brands/create/"

token = "PASTE_YOUR_LOGIN_TOKEN_HERE"

headers = {
    "Authorization": f"Token {token}"
}

data = {
    "name": "TestBrand",
    "industry": "Cosmetics",
    "description": "My first authenticated brand"
}

response = requests.post(
    url,
    headers=headers,
    json=data
)

print("Status:", response.status_code)
print("Response:", response.text)