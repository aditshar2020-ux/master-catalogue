import os
import re
import json
import time
import datetime
import urllib.parse
import requests

def resolve_poster(title: str, media_type: str = "Movie") -> str:
    """Fetches high-res poster artwork via iTunes or Wikipedia."""
    clean_title = title.split(":")[0].split("Season")[0].split("S1")[0].split("S2")[0].strip()

    # 1. Try iTunes Search API
    try:
        entity = "tvSeason" if str(media_type).lower() in ["show", "series", "limited series"] else "movie"
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(clean_title)}&entity={entity}&limit=1"
        r = requests.get(url, timeout=7)
        if r.ok:
            results = r.json().get("results", [])
            if results and results[0].get("artworkUrl100"):
                return results[0]["artworkUrl100"].replace("100x100bb", "600x900bb")
    except Exception:
        pass

    # 2. Try Wikipedia REST API
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_title.replace(' ', '_'))}"
        r = requests.get(wiki_url, headers={"User-Agent": "MasterCatalogueBot/4.0"}, timeout=7)
        if r.ok:
            thumb = r.json().get("thumbnail", {}).get("source")
            if thumb:
                return thumb
    except Exception:
        pass

    return "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&q=80"

def clean_json_text(text: str) -> str:
    """Strips markdown code fences from AI response."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def request_gemini_with_fallback(api_key: str, payload_body: dict):
    """Tries primary model, retries on 503, and falls back to alternate models."""
    candidate_models = [
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest"
    ]

    last_error = ""

    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        print(f"Attempting generation with: {model_name}")

        for attempt in range(1, 4):
            try:
                resp = requests.post(url, json=payload_body, timeout=60)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in [503, 429]:
                    print(f"Server busy (HTTP {resp.status_code}) on {model_name}, attempt {attempt}/3. Waiting 6 seconds...")
                    time.sleep(6)
                    last_error = f"{model_name}: {resp.status_code} {resp.text}"
                else:
                    last_error = f"{model_name}: {resp.status_code} {resp.text}"
                    print(f"{model_name} failed with {resp.status_code}: {resp.text}")
                    break
            except Exception as e:
                last_error = str(e)
                print(f"Network error on {model_name}: {e}")
                time.sleep(3)

    raise RuntimeError(f"All Gemini candidate models failed: {last_error}")

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY secret in repository settings.")

    today_str = datetime.date.today().strftime("%b %d, %Y")

    prompt = f"""Today is {today_str}. Provide the latest top trending titles on Indian and Global OTT platforms, plus festival gems.
Return STRICT valid JSON only. The JSON must follow this exact schema:
{{
  "syncDate": "{today_str}",
  "india": {{
    "netflix": [ {{ "rank": 1, "title": "Title", "type": "Film/Show", "year": "2026", "imdb": "8.0", "verdict": "Critical Gold/Hype", "tag": "Genre" }} ],
    "prime": [ {{ "rank": 1, "title": "Title", "type": "Film/Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "jiohotstar": [ {{ "rank": 1, "title": "Title", "type": "Film/Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "sonyliv": [ {{ "rank": 1, "title": "Title", "type": "Film/Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "zee5": [ {{ "rank": 1, "title": "Title", "type": "Film/Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ]
  }},
  "global": {{
    "netflix": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "prime": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "max": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "disney": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "apple": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ]
  }},
  "beyond": [
    {{
      "title": "Title",
      "director": "Director Name",
      "year": "2025/2026",
      "event": "Cannes/Venice/TIFF/Restoration",
      "imdb": "8.2",
      "where": "MUBI / Criterion / Festivals",
      "note": "Two-sentence critical review."
    }}
  ]
}}

Provide 5 to 10 accurate titles for each platform based on current trending charts."""

    payload_body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    res_json = request_gemini_with_fallback(api_key, payload_body)

    candidate_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
    clean_text = clean_json_text(candidate_text)
    data = json.loads(clean_text)

    # Attach live poster artwork
    for platform, items in data.get("india", {}).items():
        for item in items:
            item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    for platform, items in data.get("global", {}).items():
        for item in items:
            item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated public/daily_catalogue.json for {today_str}")

if __name__ == "__main__":
    main()
