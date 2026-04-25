import os
import json
import time
import base64
import re
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

DESIGN_DIRECTION_MAP = {
    "luxury":      "dark-luxury",
    "natural":     "warm-natural",
    "modern":      "modern-minimal",
    "traditional": "thai-tropical",
}

BRAND_EXTRACTION_PROMPT = """You are a brand analyst specialising in Thai wellness businesses.
Analyse the provided Facebook page screenshots and business data for this Thai spa/massage/onsen business.

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{
  "business_name_th": "Thai name or null",
  "business_name_en": "English name",
  "tagline": "short Thai tagline or null",
  "tagline_en": "short English tagline",
  "brand_tone": "luxury OR natural OR modern OR traditional",
  "primary_color": "#hex — dominant background colour",
  "secondary_color": "#hex — secondary colour",
  "accent_color": "#hex — CTA/highlight colour",
  "text_color": "#hex — main text colour (light or dark based on bg)",
  "logo_url": "URL or null",
  "cover_photo_url": "best photo URL for hero background",
  "gallery_photos": ["url1", "url2"],
  "services": [{"name_th": "...", "name_en": "...", "duration_min": 60, "price_thb": 500}],
  "about_text_th": "2–3 sentence Thai description",
  "about_text_en": "2–3 sentence English description",
  "top_reviews": [{"author": "...", "rating": 5, "text": "..."}],
  "line_id": "@handle or null",
  "bts_mrt": "nearest BTS/MRT station description or null",
  "design_direction": "dark-luxury OR warm-natural OR modern-minimal OR thai-tropical"
}

Brand tone classification guide:
- luxury: upscale pricing (฿1,000+), marble/gold aesthetic, formal language → dark-luxury
- natural: warm earthy tones, traditional Thai, neighbourhood feel → warm-natural
- modern: minimalist, Japanese-influenced, younger crowd, clean design → modern-minimal
- traditional: lush greenery, Thai cultural motifs, outdoor/garden → thai-tropical
"""


def _fetch_image_as_base64(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        return None


def _parse_claude_response(text: str) -> dict:
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\n?", "", text).strip()
    return json.loads(text)


def _scrape_facebook_page(facebook_url: str) -> dict:
    """Use Playwright to scrape public Facebook page data."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page.goto(facebook_url, timeout=15000)
            time.sleep(3)

            screenshot = page.screenshot(full_page=False, type="jpeg", quality=80)
            cover_screenshot = base64.b64encode(screenshot).decode("utf-8")

            text_content = page.inner_text("body")[:3000]

            browser.close()
            return {"screenshot_b64": cover_screenshot, "text": text_content}
    except Exception as e:
        print(f"    [warn] Facebook scrape failed: {e}")
        return {}


def extract_brand(lead: dict) -> dict:
    """
    Extract brand intelligence for a lead using Facebook scraping + Claude.
    Falls back to Google Places photos if Facebook is unavailable.
    Returns a brand dict.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    content = []

    if lead.get("facebook_url"):
        print(f"    Scraping Facebook: {lead['facebook_url']}")
        fb_data = _scrape_facebook_page(lead["facebook_url"])
        if fb_data.get("screenshot_b64"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": fb_data["screenshot_b64"],
                },
            })
        if fb_data.get("text"):
            content.append({"type": "text", "text": f"Facebook page text:\n{fb_data['text']}"})

    # Add Google Places photos as additional context (up to 3)
    for photo_url in lead.get("photos", [])[:3]:
        b64 = _fetch_image_as_base64(photo_url)
        if b64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })

    # Add structured lead data + prompt
    content.append({
        "type": "text",
        "text": (
            f"Business name: {lead['name']}\n"
            f"Address: {lead['address']}\n"
            f"Phone: {lead['phone']}\n"
            f"Rating: {lead['rating']} ({lead['review_count']} reviews)\n"
            f"Area: {lead['area']}\n\n"
            f"{BRAND_EXTRACTION_PROMPT}"
        ),
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": content}],
    )

    brand = _parse_claude_response(response.content[0].text)
    brand["slug"] = lead["slug"]

    # Fallback: use first Google photo if Claude didn't return a cover
    if not brand.get("cover_photo_url") and lead.get("photos"):
        brand["cover_photo_url"] = lead["photos"][0]

    # Merge Google Places photos into gallery
    existing_gallery = brand.get("gallery_photos", [])
    for p in lead.get("photos", []):
        if p not in existing_gallery:
            existing_gallery.append(p)
    brand["gallery_photos"] = existing_gallery[:8]

    # Inject Google Maps embed URL
    brand["google_maps_embed_url"] = (
        f"https://www.google.com/maps/embed/v1/place"
        f"?key={os.getenv('GOOGLE_PLACES_API_KEY', '')}"
        f"&q=place_id:{lead['place_id']}"
    )

    return brand
