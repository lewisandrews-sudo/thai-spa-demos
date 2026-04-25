import pytest
import sys
import os
import json
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from brand_extractor import extract_brand, _parse_claude_response, DESIGN_DIRECTION_MAP

MOCK_CLAUDE_JSON = {
    "business_name_th": "โลตัส สปา",
    "business_name_en": "Lotus Spa & Wellness",
    "tagline": "ศิลปะแห่งการเยียวยาแบบไทย",
    "tagline_en": "The Art of Thai Healing",
    "brand_tone": "luxury",
    "primary_color": "#1a1a2e",
    "secondary_color": "#16213e",
    "accent_color": "#c9a84c",
    "text_color": "#ffffff",
    "logo_url": None,
    "cover_photo_url": "https://example.com/cover.jpg",
    "gallery_photos": ["https://example.com/p1.jpg"],
    "services": [
        {"name_th": "นวดแผนไทย", "name_en": "Thai Massage", "duration_min": 60, "price_thb": 500}
    ],
    "about_text_th": "สปาคุณภาพสูง",
    "about_text_en": "Premium quality spa",
    "top_reviews": [{"author": "John", "rating": 5, "text": "Great!"}],
    "line_id": "@lotusspa",
    "bts_mrt": "BTS Asok — 3 min walk",
    "design_direction": "dark-luxury",
}


def test_parse_claude_response_valid_json():
    response_text = "```json\n" + json.dumps(MOCK_CLAUDE_JSON) + "\n```"
    result = _parse_claude_response(response_text)
    assert result["business_name_en"] == "Lotus Spa & Wellness"
    assert result["design_direction"] == "dark-luxury"


def test_parse_claude_response_raw_json():
    result = _parse_claude_response(json.dumps(MOCK_CLAUDE_JSON))
    assert result["brand_tone"] == "luxury"


def test_design_direction_map_covers_all_tones():
    for tone in ["luxury", "natural", "modern", "traditional"]:
        assert tone in DESIGN_DIRECTION_MAP


def test_extract_brand_uses_google_photos_as_fallback(mocker, sample_lead):
    sample_lead["facebook_url"] = None
    mock_anthropic = mocker.patch("brand_extractor.anthropic.Anthropic")
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(MOCK_CLAUDE_JSON))]
    )
    mocker.patch("brand_extractor._fetch_image_as_base64", return_value=None)

    result = extract_brand(sample_lead)
    assert result["slug"] == sample_lead["slug"]
    assert "services" in result
    assert "design_direction" in result


def test_extract_brand_injects_slug(mocker, sample_lead):
    mocker.patch("brand_extractor.anthropic.Anthropic").return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(MOCK_CLAUDE_JSON))]
    )
    mocker.patch("brand_extractor._fetch_image_as_base64", return_value=None)
    result = extract_brand(sample_lead)
    assert result["slug"] == "lotus-spa-wellness"


def test_extract_brand_adds_google_maps_embed(mocker, sample_lead):
    mocker.patch("brand_extractor.anthropic.Anthropic").return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(MOCK_CLAUDE_JSON))]
    )
    mocker.patch("brand_extractor._fetch_image_as_base64", return_value=None)
    result = extract_brand(sample_lead)
    assert "google_maps_embed_url" in result
    assert "ChIJtest123" in result["google_maps_embed_url"]
