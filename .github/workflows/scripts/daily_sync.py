import os
import re
import json
import datetime
import urllib.parse
import requests
from google import genai
from google.genai import types

def resolve_poster(title: str, media_type: str = "Movie") -> str:
    """Resolves high-res theatrical poster via iTunes or Wikipedia."""
    clean_title = title.split(":")[0].split("Season")[0].split("S1")[0].split("S2")[0].strip()

    # 1. Try iTunes Search API (Free, high-res)
    try:
        entity = "tvSeason" if media_type.lower() in ["show", "series", "limited series"] else "movie"
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

    # Default fallback cinephile placeholder
    return "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&q=80"

def clean_json_text(text: str) -> str:
    """Removes markdown code fences if Gemini wraps JSON."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY secret in GitHub repository settings.")

    client = genai.Client(api_key=api_key)
    today_str = datetime.date.today().strftime("%b %d, %Y")

    prompt = f"""Today is {today_str}. Search live OTT charts, trade reports, and film festival news.
Return STRICT valid JSON only. Structure must exactly match this template:
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

Provide 5 to 10 accurate titles for each platform based on today's actual trending charts."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="application/json"
        ),
    )

    clean_text = clean_json_text(response.text)
    payload = json.loads(clean_text)

    # Attach posters for India
    for platform, items in payload.get("india", {}).items():
        for item in items:
            item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    # Attach posters for Global
    for platform, items in payload.get("global", {}).items():
        for item in items:
            item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated public/daily_catalogue.json for {today_str}")

if __name__ == "__main__":
    main()
