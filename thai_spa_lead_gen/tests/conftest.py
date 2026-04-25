# thai_spa_lead_gen/tests/conftest.py
import pytest
import json

SAMPLE_LEAD = {
    "name": "Lotus Spa & Wellness",
    "slug": "lotus-spa-wellness",
    "place_id": "ChIJtest123",
    "address": "123 Sukhumvit Soi 23, Khlong Toei Nuea, Bangkok 10110",
    "phone": "02-123-4567",
    "rating": 4.7,
    "review_count": 142,
    "photos": [
        "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=test1",
        "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=test2",
    ],
    "opening_hours": {
        "weekday_text": [
            "Monday: 10:00 AM – 10:00 PM",
            "Tuesday: 10:00 AM – 10:00 PM",
            "Wednesday: 10:00 AM – 10:00 PM",
            "Thursday: 10:00 AM – 10:00 PM",
            "Friday: 10:00 AM – 10:00 PM",
            "Saturday: 10:00 AM – 10:00 PM",
            "Sunday: 10:00 AM – 10:00 PM",
        ]
    },
    "facebook_url": "https://www.facebook.com/lotusspa.bkk",
    "has_website": False,
    "area": "sukhumvit",
}

SAMPLE_BRAND = {
    "slug": "lotus-spa-wellness",
    "business_name_th": "โลตัส สปา แอนด์ เวลเนส",
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
    "gallery_photos": [
        "https://example.com/photo1.jpg",
        "https://example.com/photo2.jpg",
        "https://example.com/photo3.jpg",
    ],
    "services": [
        {"name_th": "นวดแผนไทย", "name_en": "Thai Massage", "duration_min": 60, "price_thb": 500},
        {"name_th": "อโรมาเธอราพี", "name_en": "Aromatherapy", "duration_min": 90, "price_thb": 900},
        {"name_th": "นวดหน้า", "name_en": "Facial Treatment", "duration_min": 60, "price_thb": 700},
    ],
    "about_text_th": "โลตัส สปา มอบประสบการณ์การนวดแผนไทยที่แท้จริง ด้วยสมุนไพรไทยคัดสรรและนักบำบัดมืออาชีพ",
    "about_text_en": "Lotus Spa offers authentic Thai massage experiences using carefully selected Thai herbs and professional therapists.",
    "top_reviews": [
        {"author": "Sarah M.", "rating": 5, "text": "Best Thai massage in Sukhumvit, very relaxing and professional staff."},
        {"author": "James K.", "rating": 5, "text": "Amazing aromatherapy session. Will definitely come back!"},
        {"author": "นภา ส.", "rating": 5, "text": "นวดดีมากค่ะ บรรยากาศสวย ราคาไม่แพง แนะนำเลย"},
    ],
    "line_id": "@lotusspa",
    "bts_mrt": "BTS Asok — 3 min walk",
    "google_maps_embed_url": "https://www.google.com/maps/embed?pb=test",
    "design_direction": "dark-luxury",
}

@pytest.fixture
def sample_lead():
    return dict(SAMPLE_LEAD)

@pytest.fixture
def sample_brand():
    return dict(SAMPLE_BRAND)

@pytest.fixture
def sample_leads_list():
    return [SAMPLE_LEAD]

@pytest.fixture
def sample_brands_list():
    return [SAMPLE_BRAND]
