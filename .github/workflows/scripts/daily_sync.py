import os
import re
import json
import time
import datetime
import urllib.parse
import requests

def resolve_poster(title: str, media_type: str = "Movie") -> str:
    clean_title = title.split(":")[0].split("Season")[0].split("S1")[0].split("S2")[0].strip()
    try:
        entity = "tvSeason" if str(media_type).lower() in ["show", "series", "limited series"] else "movie"
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(clean_title)}&entity={entity}&limit=1"
        r = requests.get(url, timeout=7)
        if r.ok and r.json().get("results"):
            res = r.json()["results"][0]
            if res.get("artworkUrl100"):
                return res["artworkUrl100"].replace("100x100bb", "600x900bb")
    except Exception: pass

    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_title.replace(' ', '_'))}"
        r = requests.get(wiki_url, headers={"User-Agent": "MasterCatalogueBot/4.0"}, timeout=7)
        if r.ok and r.json().get("thumbnail", {}).get("source"):
            return r.json()["thumbnail"]["source"]
    except Exception: pass
    
    return "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&q=80"

def clean_json_text(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key: raise RuntimeError("Missing GEMINI_API_KEY secret")

    today_str = datetime.date.today().strftime("%b %d, %Y")

    prompt = f"""You are a live streaming analytics engine. Today is {today_str}.
Use Google Search to find the ACTUAL real-time Top 10 trending charts for today on the specified platforms.
Return STRICT valid JSON only. Schema:
{{
  "syncDate": "{today_str}",
  "india": {{
    "netflix": [ {{ "rank": 1, "title": "Title", "type": "Film/Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
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
    {{ "title": "Title", "director": "Director Name", "year": "2026", "event": "Festival/Restoration", "imdb": "8.2", "where": "Platform", "note": "Review." }}
  ]
}}"""

    # CRITICAL FIX: THIS BLOCK TURNS ON LIVE GOOGLE SEARCH
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }

    # CRITICAL FIX: RETRY LOOP IF SERVER IS BUSY
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    data = None

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(2):
            try:
                r = requests.post(url, json=payload, timeout=40)
                if r.status_code == 200:
                    cand = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(clean_json_text(cand))
                    break
                elif r.status_code in [503, 429]:
                    print(f"{model} busy. Waiting 6 seconds...")
                    time.sleep(6)
            except Exception:
                time.sleep(3)
        if data: break

    if not data: raise RuntimeError("All Gemini endpoints failed or timed out.")

    for platform, items in data.get("india", {}).items():
        for item in items: item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))
    for platform, items in data.get("global", {}).items():
        for item in items: item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
