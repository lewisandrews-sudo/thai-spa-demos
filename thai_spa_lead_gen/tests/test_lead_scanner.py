import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lead_scanner import scan_leads, qualify_lead, resolve_facebook_url, slugify_name

MOCK_PLACES_RESULT = {
    "name": "Lotus Spa & Wellness",
    "place_id": "ChIJtest123",
    "formatted_address": "123 Sukhumvit Soi 23, Bangkok",
    "formatted_phone_number": "02-123-4567",
    "rating": 4.7,
    "user_ratings_total": 142,
    "photos": [{"photo_reference": "ref1", "width": 800}],
    "opening_hours": {"weekday_text": ["Monday: 10:00 AM – 10:00 PM"]},
    "website": None,
    "types": ["spa", "health", "establishment"],
}

def test_qualify_lead_passes_with_enough_reviews():
    assert qualify_lead(MOCK_PLACES_RESULT) is True

def test_qualify_lead_fails_with_website():
    lead = {**MOCK_PLACES_RESULT, "website": "https://example.com"}
    assert qualify_lead(lead) is False

def test_qualify_lead_fails_with_too_few_reviews():
    lead = {**MOCK_PLACES_RESULT, "user_ratings_total": 5}
    assert qualify_lead(lead) is False

def test_qualify_lead_fails_with_low_rating():
    lead = {**MOCK_PLACES_RESULT, "rating": 2.5}
    assert qualify_lead(lead) is False

def test_qualify_lead_excludes_known_chains():
    chain = {**MOCK_PLACES_RESULT, "name": "Let's Relax Spa Sukhumvit"}
    assert qualify_lead(chain) is False

def test_slugify_name():
    assert slugify_name("Lotus Spa & Wellness") == "lotus-spa-wellness"

def test_scan_leads_returns_qualified_list(mocker):
    mock_client = MagicMock()
    mock_client.places.return_value = {"results": [MOCK_PLACES_RESULT]}
    mock_client.place.return_value = {"result": MOCK_PLACES_RESULT}
    mocker.patch("lead_scanner.googlemaps.Client", return_value=mock_client)
    mocker.patch("lead_scanner.resolve_facebook_url", return_value="https://facebook.com/lotusspa")
    mocker.patch("lead_scanner.GOOGLE_API_KEY", "test-key")

    leads = scan_leads(area="sukhumvit", business_type="massage", count=5)
    assert isinstance(leads, list)
    assert all("slug" in lead for lead in leads)
    assert all("has_website" in lead for lead in leads)
    assert all(lead["has_website"] is False for lead in leads)
