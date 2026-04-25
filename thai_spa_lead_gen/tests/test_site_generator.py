# thai_spa_lead_gen/tests/test_site_generator.py
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from site_generator import generate_site, TEMPLATE_MAP

def test_template_map_covers_all_directions():
    for direction in ["dark-luxury", "warm-natural", "modern-minimal", "thai-tropical"]:
        assert direction in TEMPLATE_MAP

def test_generate_site_starter_has_no_booking(sample_lead, sample_brand, tmp_path):
    starter_path, _ = generate_site(sample_lead, sample_brand, output_dir=str(tmp_path), deploy_url="https://test.netlify.app")
    content = open(starter_path).read()
    assert "booking" not in content.lower() or "Line to Book" in content
    assert sample_brand["business_name_en"] in content
    assert "og:title" in content
    assert "og:image" in content

def test_generate_site_premium_has_booking_widget(sample_lead, sample_brand, tmp_path):
    _, premium_path = generate_site(sample_lead, sample_brand, output_dir=str(tmp_path), deploy_url="https://test.netlify.app")
    content = open(premium_path).read()
    assert "booking-service" in content
    assert "submitBooking" in content
    assert "netlify/functions/book" in content

def test_generate_site_includes_og_tags(sample_lead, sample_brand, tmp_path):
    starter_path, _ = generate_site(sample_lead, sample_brand, output_dir=str(tmp_path), deploy_url="https://test.netlify.app")
    content = open(starter_path).read()
    assert 'property="og:title"' in content
    assert 'property="og:image"' in content
    assert 'property="og:url"' in content

def test_generate_site_uses_brand_colors(sample_lead, sample_brand, tmp_path):
    starter_path, _ = generate_site(sample_lead, sample_brand, output_dir=str(tmp_path), deploy_url="https://test.netlify.app")
    content = open(starter_path).read()
    assert sample_brand["primary_color"] in content
    assert sample_brand["accent_color"] in content

def test_generate_site_creates_admin_for_premium(sample_lead, sample_brand, tmp_path):
    _, premium_path = generate_site(sample_lead, sample_brand, output_dir=str(tmp_path), deploy_url="https://test.netlify.app")
    premium_dir = os.path.dirname(premium_path)
    admin_path = os.path.join(premium_dir, "..", f"{sample_brand['slug']}-admin", "index.html")
    assert os.path.exists(os.path.normpath(admin_path))
