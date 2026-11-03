import os
import json
import datetime
import urllib.parse
import requests
from google import genai
from google.genai import types

def resolve_poster(title: str, media_type: str = "Movie") -> str:
    """Resolves high-res poster via optional TMDB key, iTunes API, or Wikipedia REST API."""
    tmdb_key = os.environ.get("TMDB_API_KEY", "").strip()
    clean_title = title.split(":")[0].strip()

    # 1. Try TMDB if user provided a key
    if tmdb_key:
        try:
            endpoint = "tv" if media_type.lower() == "series" else "movie"
            url = f"https://api.themoviedb.org/3/search/{endpoint}?api_key={tmdb_key}&query={urllib.parse.quote(clean_title)}"
            r = requests.get(url, timeout=8)
            if r.ok:
                results = r.json().get("results", [])
                if results and results[0].get("poster_path"):
                    return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
        except Exception:
            pass

    # 2. Try iTunes Search API (Free, no key required)
    try:
        entity = "tvSeason" if media_type.lower() == "series" else "movie"
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(clean_title)}&entity={entity}&limit=1"
        r = requests.get(url, timeout=8)
        if r.ok:
            results = r.json().get("results", [])
            if results and results[0].get("artworkUrl100"):
                return results[0]["artworkUrl100"].replace("100x100bb", "600x900bb")
    except Exception:
        pass

    # 3. Try Wikipedia REST Summary API
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_title.replace(' ', '_'))}"
        r = requests.get(wiki_url, headers={"User-Agent": "MasterCatalogueBot/4.0"}, timeout=8)
        if r.ok:
            thumb = r.json().get("thumbnail", {}).get("source")
            if thumb:
                return thumb
    except Exception:
        pass

    return ""

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY secret in GitHub repository settings.")

    client = genai.Client(api_key=api_key)
    today_str = datetime.date.today().strftime("%b %d, %Y")

    prompt = f"""Today is {today_str}. Search live OTT charts and film festival news to provide:
1. Current #1 trending title in India across Netflix India, Prime Video India, JioHotstar, SonyLIV, and ZEE5.
2. Three critically acclaimed 2026 Indian or International festival/indie blindspot gems (with IMDb rating, director, cast, language, and 2-sentence synopsis).
Return strictly valid JSON with keys:
"syncDate": "{today_str}",
"syncSummary": "One-sentence summary of today's Indian & Global OTT trends",
"blindspots": [
  {{
    "title": "String",
    "year": 2026,
    "type": "Movie",
    "genre": "String",
    "imdb": 8.3,
    "language": "String",
    "country": "String",
    "creator": "String",
    "cast": "String",
    "platform": "String",
    "curatorBadge": "Daily Auto-Sync Discovery",
    "synopsis": "String"
  }}
]"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="application/json"
        ),
    )

    payload = json.loads(response.text)
    for idx, gem in enumerate(payload.get("blindspots", [])):
        gem["id"] = f"auto-gem-{idx}-{int(datetime.datetime.now().timestamp())}"
        gem["platformKey"] = "festival"
        gem["posterUrl"] = resolve_poster(gem.get("title", ""), gem.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Successfully wrote public/daily_catalogue.json for {today_str}")

if __name__ == "__main__":
    main()
