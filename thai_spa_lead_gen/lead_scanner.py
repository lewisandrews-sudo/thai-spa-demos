import os
import re
import time
import requests
import googlemaps
from slugify import slugify  # python-slugify package
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

KNOWN_CHAINS = [
    "let's relax", "health land", "divana", "oasis spa",
    "rarinjinda", "banyan tree", "mandarin oriental", "st. regis",
]

AREA_COORDINATES = {
    "sukhumvit": "13.7307,100.5697",
    "silom":     "13.7283,100.5353",
    "thonglor":  "13.7292,100.5857",
    "ekkamai":   "13.7249,100.5861",
    "ari":       "13.7784,100.5448",
    "asok":      "13.7372,100.5600",
}

SEARCH_QUERIES = {
    "massage": ["นวดแผนไทย", "Thai massage", "นวด"],
    "spa":     ["สปา", "spa Bangkok", "day spa"],
    "onsen":   ["ออนเซ็น", "onsen Bangkok", "Japanese bath"],
    "all":     ["นวดแผนไทย", "สปา", "ออนเซ็น", "massage", "spa"],
}


def slugify_name(name: str) -> str:
    return slugify(name, max_length=50)


def qualify_lead(place: dict) -> bool:
    """Return True if this place is a viable lead."""
    if place.get("website"):
        return False
    if place.get("user_ratings_total", 0) < 20:
        return False
    if place.get("rating", 0) < 3.5:
        return False
    name_lower = place.get("name", "").lower()
    if any(chain in name_lower for chain in KNOWN_CHAINS):
        return False
    return True


def resolve_facebook_url(business_name: str, area: str = "Bangkok") -> str | None:
    """Use SerpAPI to find the Facebook page URL for a business."""
    if not SERPAPI_KEY:
        return None
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "q": f"{business_name} {area} Facebook",
                "api_key": SERPAPI_KEY,
                "num": 3,
            },
            timeout=10,
        )
        results = resp.json().get("organic_results", [])
        for r in results:
            link = r.get("link", "")
            # Match business pages only: facebook.com/pagename (no groups/hashtags)
            if re.search(r"facebook\.com/[^/\?#]+/?$", link):
                return link
    except Exception as e:
        print(f"  [warn] Facebook URL lookup failed for '{business_name}': {e}")
    return None


def build_photo_urls(photos: list, api_key: str, max_width: int = 800) -> list:
    return [
        f"https://maps.googleapis.com/maps/api/place/photo"
        f"?maxwidth={max_width}&photoreference={p['photo_reference']}&key={api_key}"
        for p in photos[:8]
    ]


def scan_leads(area: str = "sukhumvit", business_type: str = "all", count: int = 20) -> list:
    """
    Query Google Places API for massage/spa/onsen businesses in the given area
    that do not have a website. Returns a list of qualified lead dicts.
    """
    if not GOOGLE_API_KEY:
        raise EnvironmentError("GOOGLE_PLACES_API_KEY is not set — check your .env file")
    client = googlemaps.Client(key=GOOGLE_API_KEY)
    coords = AREA_COORDINATES.get(area, AREA_COORDINATES["sukhumvit"])
    queries = SEARCH_QUERIES.get(business_type, SEARCH_QUERIES["all"])

    seen_ids = set()
    leads = []

    for query in queries:
        if len(leads) >= count:
            break
        try:
            results = client.places(
                query=query,
                location=coords,
                radius=3000,
                language="th",
            ).get("results", [])
        except Exception as e:
            print(f"  [warn] Places search failed for '{query}': {e}")
            continue

        for r in results:
            if len(leads) >= count:
                break
            place_id = r.get("place_id")
            if place_id in seen_ids:
                continue
            seen_ids.add(place_id)

            # Fetch full details to get website field
            try:
                detail = client.place(
                    place_id,
                    fields=["name", "formatted_address", "formatted_phone_number",
                            "rating", "user_ratings_total", "photos",
                            "opening_hours", "website", "types"],
                    language="en",
                ).get("result", {})
            except Exception:
                continue

            if not qualify_lead(detail):
                continue

            time.sleep(0.5)  # polite delay
            facebook_url = resolve_facebook_url(detail.get("name", ""), area)
            time.sleep(1.0)

            photos = build_photo_urls(
                detail.get("photos", [])[:8], GOOGLE_API_KEY
            )

            lead = {
                "name": detail.get("name", ""),
                "slug": slugify_name(detail.get("name", "")),
                "place_id": place_id,
                "address": detail.get("formatted_address", ""),
                "phone": detail.get("formatted_phone_number", ""),
                "rating": detail.get("rating", 0),
                "review_count": detail.get("user_ratings_total", 0),
                "photos": photos,
                "opening_hours": detail.get("opening_hours", {}),
                "facebook_url": facebook_url,
                "has_website": False,
                "area": area,
            }
            leads.append(lead)
            print(f"  Found: {lead['name']} ({lead['review_count']} reviews)")

    return leads
