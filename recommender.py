import os
import json
import time
import random
import requests
import spacy

# 1) Dynamic MAL genres/tags via Jikan v4

def fetch_mal_genres() -> dict[str,int]:
    """Fetch MAL genre list so we can match any official genre name."""
    resp = requests.get("https://api.jikan.moe/v4/genres/anime")
    resp.raise_for_status()
    genres = resp.json().get("data", [])
    return {g["name"].lower(): g["mal_id"] for g in genres}

MAL_GENRES = fetch_mal_genres()
CACHE_DIR = "data"
CACHE_PATH = os.path.join(CACHE_DIR, "genre_cache.json")
ANILIST_CACHE_PATH = os.path.join(CACHE_DIR, "anilist_cache.json")

# Initialize spaCy NLP pipeline
nlp = spacy.load("en_core_web_sm")

# 2) Parsing & intent with spaCy

def extract_keywords(text: str) -> list[str]:
    """Extract noun chunks and adjectives/nouns via spaCy."""
    doc = nlp(text.lower())
    phrases = {chunk.text for chunk in doc.noun_chunks}
    tokens = {tok.text for tok in doc if tok.pos_ in ("NOUN", "ADJ")}
    return list(phrases.union(tokens))

def parse_user_request(text: str) -> dict:
    tokens = extract_keywords(text)
    # genres from MAL_GENRES
    genres = [tok for tok in tokens if tok in MAL_GENRES]
    # episodes filter: "under N"
    max_eps = None
    if "under" in tokens:
        idx = tokens.index("under")
        if idx + 1 < len(tokens) and tokens[idx+1].isdigit():
            max_eps = int(tokens[idx+1])
    # hidden‑gem preference
    rating_pref = "hidden gem" if "hidden" in tokens and "gem" in tokens else None
    return {"genres": genres, "max_episodes": max_eps, "rating_pref": rating_pref}

# 3) Jikan fetch helpers (genre + top + search)
 

def _load_cache(path: str) -> dict:
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}

def _save_cache(path: str, cache: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    json.dump(cache, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def fetch_by_genre(genre_id: int, pages: int = 2) -> list[dict]:
    cache = _load_cache(CACHE_PATH)
    key = f"genre_{genre_id}_p{pages}"
    if key in cache:
        return cache[key]
    all_data = []
    for page in range(1, pages+1):
        r = requests.get(
            "https://api.jikan.moe/v4/anime",
            params={"genres": genre_id, "page": page}
        )
        r.raise_for_status()
        all_data.extend(r.json().get("data", []))
        time.sleep(1)
    cache[key] = all_data
    _save_cache(CACHE_PATH, cache)
    return all_data

def fetch_search_mal(query: str, pages: int = 1) -> list[dict]:
    all_data = []
    for page in range(1, pages+1):
        r = requests.get(
            "https://api.jikan.moe/v4/anime",
            params={"q": query, "page": page}
        )
        r.raise_for_status()
        all_data.extend(r.json().get("data", []))
        time.sleep(1)
    return all_data

def fetch_top_anime(pages: int = 2) -> list[dict]:
    all_data = []
    for page in range(1, pages+1):
        r = requests.get("https://api.jikan.moe/v4/top/anime", params={"page": page})
        r.raise_for_status()
        all_data.extend(r.json().get("data", []))
        time.sleep(1)
    return all_data

# 4) AniList GraphQL search fallback with caching

def fetch_anilist(query: str, per_page: int = 10) -> list[dict]:
    cache = _load_cache(ANILIST_CACHE_PATH)
    key = query.lower()
    if key in cache:
        return cache[key]
    gql = """
    query ($search: String, $perPage: Int) {
      Page(perPage: $perPage) {
        media(search: $search, type: ANIME) {
          title { romaji }
          siteUrl
          averageScore
          episodes
        }
      }
    }
    """
    variables = {"search": query, "perPage": per_page}
    resp = requests.post(
        "https://graphql.anilist.co",
        json={"query": gql, "variables": variables}
    )
    resp.raise_for_status()
    media = resp.json()["data"]["Page"]["media"]
    results = [
        {"title": m["title"]["romaji"], "url": m["siteUrl"], 
         "score": m.get("averageScore") and m["averageScore"]/10, 
         "episodes": m.get("episodes")} for m in media
    ]
    cache[key] = results
    _save_cache(ANILIST_CACHE_PATH, cache)
    return results

# 5) Core recommender
def recommend_anime(query: str) -> list[dict]:
    parsed = parse_user_request(query)
    candidates = []
    if parsed["genres"]:
        for g in parsed["genres"]:
            gid = MAL_GENRES[g]
            candidates += fetch_by_genre(gid, pages=2)
    elif query.strip():
        candidates = fetch_search_mal(query, pages=1)
    if not candidates and query.strip():
        candidates = fetch_anilist(query, per_page=10)
    if not candidates:
        candidates = fetch_top_anime(pages=2)
    # Deduplicate exact URLs
    seen = set(); unique = []
    for a in candidates:
        if a["url"] not in seen:
            unique.append(a); seen.add(a["url"])
    candidates = unique
    # Deduplicate by base title (before colon or dash)
    base_seen = set(); unique_base = []
    for a in candidates:
        base = a["title"].split(":")[0].split("-")[0].strip()
        if base.lower() not in base_seen:
            unique_base.append(a); base_seen.add(base.lower())
    candidates = unique_base
    # Episode filter
    if parsed["max_episodes"] is not None:
        candidates = [a for a in candidates if a.get("episodes") and a["episodes"] <= parsed["max_episodes"]]
    # Hidden‑gem filter
    if parsed["rating_pref"] == "hidden gem":
        candidates = [a for a in candidates if a.get("score") and a["score"] < 7]
    # Shuffle & pick top 10
    random.shuffle(candidates)
    candidates = sorted(candidates, key=lambda a: a.get("score") or 0, reverse=True)[:10]
    return [{"title": a["title"], "url": a["url"]} for a in candidates]

# 6) Default “Trending”
def get_default_recs() -> list[dict]:
    data = fetch_top_anime(pages=2)
    random.shuffle(data)
    top10 = sorted(data, key=lambda a: a.get("score") or 0, reverse=True)[:10]
    return [{"title": a["title"], "url": a["url"]} for a in top10]