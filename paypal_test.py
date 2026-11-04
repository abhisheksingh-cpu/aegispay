
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("PAYPAL_CLIENT_ID")
client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

if not client_id or not client_secret:
    raise SystemExit("PayPal credentials are missing from .env")

response = httpx.post(
    "https://api-m.sandbox.paypal.com/v1/oauth2/token",
    auth=(client_id, client_secret),
    data={"grant_type": "client_credentials"},
    headers={"Accept": "application/json"},
    timeout=20.0,
)

if response.is_success:
    data = response.json()
    print("PayPal Sandbox authentication successful.")
    print("Token type:", data.get("token_type"))
    print("Expires in seconds:", data.get("expires_in"))
else:
    print("Authentication failed.")
    print("HTTP status:", response.status_code)
    print("Response:", response.text[:1000])
