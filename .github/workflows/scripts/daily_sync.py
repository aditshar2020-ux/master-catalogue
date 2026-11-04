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
        r = requests.get(wiki_url, headers={"User-Agent": "MasterCatalogueBot/6.0"}, timeout=7)
        if r.ok and r.json().get("thumbnail", {}).get("source"):
            return r.json()["thumbnail"]["source"]
    except Exception: pass
    
    return "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&q=80"

def get_curated_fallback(today_str: str) -> dict:
    """Fallback only triggers if Google heavily rate-limits your key."""
    return {
        "syncDate": today_str,
        "syncMode": "OFFLINE FALLBACK (Rate Limit Hit)",
        "india": {
            "netflix": [ { "rank": 1, "title": "Dhurandhar", "type": "Film", "year": "2026", "imdb": "7.9", "verdict": "Action Spectacle", "tag": "Spy Thriller" } ],
            "prime": [ { "rank": 1, "title": "Mirzapur: The Movie", "type": "Film", "year": "2026", "imdb": "8.4", "verdict": "Cult Sensation", "tag": "Gangster" } ],
            "jiohotstar": [ { "rank": 1, "title": "Thukra Ke Mera Pyaar S2", "type": "Show", "year": "2026", "imdb": "8.1", "verdict": "Revenge Craze", "tag": "Intense Drama" } ],
            "sonyliv": [ { "rank": 1, "title": "Gullak S5", "type": "Show", "year": "2026", "imdb": "9.1", "verdict": "All-Time Canon", "tag": "Middle-Class" } ],
            "zee5": [ { "rank": 1, "title": "Gyaarah Gyaarah S2", "type": "Show", "year": "2026", "imdb": "8.1", "verdict": "Walkie-Talkie Sci-Fi", "tag": "Mystery" } ]
        },
        "global": {
            "netflix": [ { "rank": 1, "title": "Squid Game S3", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Mania", "tag": "Survival" } ],
            "prime": [ { "rank": 1, "title": "The Boys S5", "type": "Show", "year": "2026", "imdb": "8.7", "verdict": "Satire", "tag": "Hero" } ],
            "max": [ { "rank": 1, "title": "The Last of Us S2", "type": "Show", "year": "2025", "imdb": "8.8", "verdict": "Devastating", "tag": "Drama" } ],
            "disney": [ { "rank": 1, "title": "Andor S2", "type": "Show", "year": "2025", "imdb": "8.4", "verdict": "Rebellion", "tag": "Sci-Fi" } ],
            "apple": [ { "rank": 1, "title": "Severance S2", "type": "Show", "year": "2025", "imdb": "8.7", "verdict": "Masterwork", "tag": "Sci-Fi" } ]
        },
        "beyond": [
            { "title": "All We Imagine as Light", "director": "Payal Kapadia", "year": "2024", "event": "Cannes Grand Prix", "imdb": "7.9", "where": "MUBI", "note": "Mumbai sisterhood." }
        ]
    }

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key: raise RuntimeError("Missing GEMINI_API_KEY")

    today_str = datetime.date.today().strftime("%b %d, %Y")

    prompt = f"""You are a live streaming analytics engine. Today is {today_str}.
Use Google Search to find the ACTUAL real-time Top 10 trending charts today on Indian OTTs (Netflix India, Prime Video India, JioHotstar, SonyLIV, ZEE5) and Global (Netflix, Prime, Max, Disney+, Apple TV+).
Return STRICT valid JSON only. Schema:
{{
  "syncDate": "{today_str}",
  "syncMode": "LIVE SEARCH (Accurate)",
  "india": {{
    "netflix": [ {{ "rank": 1, "title": "Title", "type": "Film", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "prime": [ {{ "rank": 1, "title": "Title", "type": "Film", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "jiohotstar": [ {{ "rank": 1, "title": "Title", "type": "Film", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "sonyliv": [ {{ "rank": 1, "title": "Title", "type": "Film", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "zee5": [ {{ "rank": 1, "title": "Title", "type": "Film", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ]
  }},
  "global": {{
    "netflix": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "prime": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "max": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "disney": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ],
    "apple": [ {{ "rank": 1, "title": "Title", "type": "Show", "year": "2026", "imdb": "8.0", "verdict": "Verdict", "tag": "Genre" }} ]
  }},
  "beyond": [
    {{ "title": "Title", "director": "Director Name", "year": "2026", "event": "Festival", "imdb": "8.2", "where": "Platform", "note": "Review." }}
  ]
}}"""

    # FORCE STRICT JSON MIME TYPE SO IT CANNOT HALLUCINATE TEXT
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    data = None

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        print(f"Executing LIVE Search Sync with {model}...")
        
        for attempt in range(2):
            try:
                r = requests.post(url, json=payload, timeout=45)
                if r.status_code == 200:
                    cand = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(cand.strip())
                    print(f"SUCCESS: Valid JSON payload received from {model}")
                    break
                elif r.status_code in [503, 429]:
                    print(f"Google Rate Limit hit (HTTP {r.status_code}). Backing off 10s...")
                    time.sleep(10)
                else:
                    print(f"API Error {r.status_code}: {r.text}")
                    break
            except Exception as e:
                print(f"Parsing error: {e}")
                time.sleep(3)
        if data: break

    if not data:
        print("CRITICAL: All models blocked or failed. Writing offline fallback.")
        data = get_curated_fallback(today_str)

    # Attach posters
    for platform, items in data.get("india", {}).items():
        for item in items: item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))
    for platform, items in data.get("global", {}).items():
        for item in items: item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
