import os
import re
import json
import datetime
import urllib.parse
import requests

def resolve_poster(title: str, media_type: str = "Movie") -> str:
    """Fetches high-res poster artwork via iTunes or Wikipedia."""
    clean_title = title.split(":")[0].split("Season")[0].split("S1")[0].split("S2")[0].strip()

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
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY secret in repository settings.")

    today_str = datetime.date.today().strftime("%b %d, %Y")

    # STRICT INSTRUCTION FORCED LIVE WEB SEARCH GROUNDING
    prompt = f"""You are a live cinema and streaming analytics engine. Today is {today_str}. 
Perform a live search query across the web right now for current trending charts.
Provide the absolute freshest, real-time top 10 trending titles on Indian OTTs (Netflix India, Prime Video India, JioHotstar, SonyLIV, ZEE5) and Global OTTs (Netflix Global, Prime Video Global, Max, Disney+, Apple TV+), plus active festival/auteur blindspots.

Return STRICT valid JSON only matching this exact schema:
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
    {{
      "title": "Title",
      "director": "Director Name",
      "year": "2025/2026",
      "event": "Festival/Restoration",
      "imdb": "8.2",
      "where": "Platform",
      "note": "Review."
    }}
  ]
}}"""

    # Pass search tool parameter via REST payload if available, or rely on prompt grounding
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    payload_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }

    gen_resp = requests.post(url, json=payload_body, timeout=60)
    if not gen_resp.ok:
        # Fallback without explicit tool block if restricted on API tier
        payload_body = {"contents": [{"parts": [{"text": prompt}]}]}
        gen_resp = requests.post(url, json=payload_body, timeout=60)

    if not gen_resp.ok:
        raise RuntimeError(f"Gemini API generation failed: HTTP {gen_resp.status_code} {gen_resp.text}")

    res_json = gen_resp.json()
    candidate_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
    clean_text = clean_json_text(candidate_text)
    data = json.loads(clean_text)

    for platform, items in data.get("india", {}).items():
        for item in items:
            item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    for platform, items in data.get("global", {}).items():
        for item in items:
            item["poster"] = resolve_poster(item.get("title", ""), item.get("type", "Movie"))

    os.makedirs("public", exist_ok=True)
    with open("public/daily_catalogue.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated fresh public/daily_catalogue.json for {today_str}")

if __name__ == "__main__":
    main()
