import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GOOGLE_API_KEY")

print("Sending direct request to Google...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={key}"
data = json.dumps({"model": "models/text-embedding-004", "content": {"parts": [{"text": "Hello"}]}}).encode("utf-8")

try:
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        print("Status: SUCCESS (200) - Your key works perfectly!")
except urllib.error.HTTPError as e:
    print(f"Status: FAILED ({e.code})")
    print("Real Error from Google:", e.read().decode('utf-8'))
except Exception as e:
    print("System Error:", str(e))