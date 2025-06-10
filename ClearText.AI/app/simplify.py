import requests

BACKEND_URL = "https://266a-117-228-198-179.ngrok-free.app" # <--- UPDATED THIS LINE

def simplify_text(text):
    try:
        response = requests.post(BACKEND_URL, json={"text": text})
        response.raise_for_status()
        return response.json().get("simplified", "No result returned.")
    except Exception as e:
        return f"Error: {e}"