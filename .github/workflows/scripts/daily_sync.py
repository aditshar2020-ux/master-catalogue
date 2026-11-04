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
        r = requests.get(wiki_url, headers={"User-Agent": "MasterCatalogueBot/5.0"}, timeout=7)
        if r.ok and r.json().get("thumbnail", {}).get("source"):
            return r.json()["thumbnail"]["source"]
    except Exception: pass
    
    return "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&q=80"

def clean_json_text(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text

def get_curated_fallback(today_str: str) -> dict:
    """Offline fail-safe catalogue ensures Vercel never breaks if API limits are hit."""
    return {
        "syncDate": today_str,
        "india": {
            "netflix": [
                { "rank": 1, "title": "Dhurandhar", "type": "Film", "year": "2026", "imdb": "7.9", "verdict": "Action Spectacle", "tag": "Spy Thriller" },
                { "rank": 2, "title": "The Great Indian Kapil Show S2", "type": "Show", "year": "2026", "imdb": "7.4", "verdict": "Pop Cult Viral", "tag": "Comedy" },
                { "rank": 3, "title": "Pushpa 2: The Rule", "type": "Film", "year": "2025", "imdb": "7.7", "verdict": "Mass Elevation", "tag": "Action" },
                { "rank": 4, "title": "Khakee: The Bengal Chapter", "type": "Show", "year": "2026", "imdb": "8.3", "verdict": "Critical Gold", "tag": "Noir" },
                { "rank": 5, "title": "Amar Singh Chamkila", "type": "Film", "year": "2024", "imdb": "8.2", "verdict": "Auteur Biopic", "tag": "Musical" }
            ],
            "prime": [
                { "rank": 1, "title": "Mirzapur: The Movie", "type": "Film", "year": "2026", "imdb": "8.4", "verdict": "Cult Sensation", "tag": "Gangster" },
                { "rank": 2, "title": "Panchayat S4", "type": "Show", "year": "2026", "imdb": "8.9", "verdict": "All-Time Canon", "tag": "Rural Realism" },
                { "rank": 3, "title": "The Family Man S3", "type": "Show", "year": "2026", "imdb": "8.8", "verdict": "Auteur Thriller", "tag": "Espionage" },
                { "rank": 4, "title": "Paatal Lok S2", "type": "Show", "year": "2026", "imdb": "8.6", "verdict": "Hardcore Noir", "tag": "Investigative" },
                { "rank": 5, "title": "Jubilee", "type": "Show", "year": "2023", "imdb": "8.4", "verdict": "Cinematic Feat", "tag": "Period Drama" }
            ],
            "jiohotstar": [
                { "rank": 1, "title": "Thukra Ke Mera Pyaar S2", "type": "Show", "year": "2026", "imdb": "8.1", "verdict": "Revenge Craze", "tag": "Intense Drama" },
                { "rank": 2, "title": "House of the Dragon S3", "type": "Show", "year": "2026", "imdb": "8.5", "verdict": "Global Gold", "tag": "High Fantasy" },
                { "rank": 3, "title": "Special OPS 2", "type": "Show", "year": "2026", "imdb": "8.6", "verdict": "Precision Action", "tag": "Counter-Terror" },
                { "rank": 4, "title": "Laughter Chefs", "type": "Show", "year": "2026", "imdb": "7.2", "verdict": "Family Sitcom", "tag": "Comedy" },
                { "rank": 5, "title": "The Freelancer S2", "type": "Show", "year": "2025", "imdb": "8.0", "verdict": "Extraction", "tag": "Tactical" }
            ],
            "sonyliv": [
                { "rank": 1, "title": "Gullak S5", "type": "Show", "year": "2026", "imdb": "9.1", "verdict": "All-Time Canon", "tag": "Middle-Class" },
                { "rank": 2, "title": "Scam 2010: Subrata Roy", "type": "Show", "year": "2026", "imdb": "8.8", "verdict": "Financial Epic", "tag": "Hansal Mehta" },
                { "rank": 3, "title": "Freedom at Midnight S2", "type": "Show", "year": "2026", "imdb": "8.3", "verdict": "Historical Benchmark", "tag": "Archive" },
                { "rank": 4, "title": "Rocket Boys", "type": "Show", "year": "2023", "imdb": "8.8", "verdict": "Pure Genius", "tag": "History" },
                { "rank": 5, "title": "Maharani S4", "type": "Show", "year": "2026", "imdb": "7.9", "verdict": "Power Realism", "tag": "Politics" }
            ],
            "zee5": [
                { "rank": 1, "title": "Gyaarah Gyaarah S2", "type": "Show", "year": "2026", "imdb": "8.1", "verdict": "Walkie-Talkie Sci-Fi", "tag": "Mystery" },
                { "rank": 2, "title": "Pitchers S3", "type": "Show", "year": "2026", "imdb": "8.6", "verdict": "Founder Journey", "tag": "Startup" },
                { "rank": 3, "title": "Sunflower S3", "type": "Show", "year": "2026", "imdb": "7.5", "verdict": "Dark Comedy", "tag": "Murder" },
                { "rank": 4, "title": "Manorathangal", "type": "Show", "year": "2024", "imdb": "8.0", "verdict": "Literary Treasure", "tag": "Drama" },
                { "rank": 5, "title": "Tripling S4", "type": "Show", "year": "2026", "imdb": "8.5", "verdict": "Sibling Roadtrip", "tag": "Feel Good" }
            ]
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
Find the REAL-TIME Top 5 trending charts today on Indian OTTs (Netflix India, Prime Video India, JioHotstar, SonyLIV, ZEE5) and Global (Netflix, Prime, Max, Disney+, Apple TV+).
Return STRICT valid JSON only. Schema:
{{
  "syncDate": "{today_str}",
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

    payload_search = {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"googleSearch": {}}]}
    payload_standard = {"contents": [{"parts": [{"text": prompt}]}]}
    
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    data = None

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        print(f"Attempting live search with {model}...")
        r = requests.post(url, json=payload_search, timeout=45)
        if r.status_code == 200:
            try:
                data = json.loads(clean_json_text(r.json()["candidates"][0]["content"]["parts"][0]["text"]))
                break
            except Exception: pass
        elif r.status_code == 429:
            print("Rate limit (429) hit on search. Waiting 15 seconds...")
            time.sleep(15)

        print(f"Attempting standard sync with {model}...")
        r2 = requests.post(url, json=payload_standard, timeout=45)
        if r2.status_code == 200:
            try:
                data = json.loads(clean_json_text(r2.json()["candidates"][0]["content"]["parts"][0]["text"]))
                break
            except Exception: pass
        elif r2.status_code == 429:
            print("Rate limit (429) hit on standard. Waiting 15 seconds...")
            time.sleep(15)
            
        if data: break

    if not data:
        print("API rate limits exhausted. Deploying offline fail-safe.")
        data = get_curated_fallback(today_str)

    for platform, items in data.get("india", {}).items():
        for item in items: item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))
    for platform, items in data.get("global", {}).items():
        for item in items: item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
