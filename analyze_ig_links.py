import requests

urls_to_analyze = [
    "https://www.instagram.com/p/DVBc8GLEVoQ/?igsh=MTluODRjM3RseWZqbw==",
    "https://www.instagram.com/p/DVBIoR4DGug/?igsh=eno5cDY0OXFjczRi",
    "https://instagram.com/reel/DRKKb1cDBmB"
]

for url in urls_to_analyze:
    print(f"\nAnalyzing: {url}")
    try:
        response = requests.post("http://127.0.0.1:8000/api/analyze-url", json={"url": url})
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Classification: {data.get('post', {}).get('classification')}")
        print(f"Severity: {data.get('post', {}).get('severity')}")
        print(f"Locations Extracted: {data.get('post', {}).get('locations')}")
    except Exception as e:
        print(f"Failed to reach API: {e}")
