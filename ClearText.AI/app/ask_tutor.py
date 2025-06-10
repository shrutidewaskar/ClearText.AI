import requests

BACKEND_URL = "https://266a-117-228-198-179.ngrok-free.app" # <--- UPDATED THIS LINE

def ask_tutor(line):
    try:
        response = requests.post(BACKEND_URL, json={"text": line})
        response.raise_for_status()
        return response.json().get("explanation", "No explanation returned.")
    except Exception as e:
        return f"Error: {e}"