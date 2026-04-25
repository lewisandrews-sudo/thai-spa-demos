# thai_spa_lead_gen/tests/test_report_generator.py
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from report_generator import generate_report, ReportRow


def test_generate_report_creates_html_file(sample_lead, sample_brand, tmp_path):
    rows = [
        ReportRow(
            lead=sample_lead,
            brand=sample_brand,
            starter_url="https://lotus-spa-wellness-starter.netlify.app",
            premium_url="https://lotus-spa-wellness-premium.netlify.app",
        )
    ]
    output_path = str(tmp_path / "report.html")
    generate_report(
        rows, output_path=output_path, area="sukhumvit", business_type="massage"
    )
    assert os.path.exists(output_path)
    content = open(output_path).read()
    assert "Lotus Spa" in content
    assert "lotus-spa-wellness-starter.netlify.app" in content
    assert "lotus-spa-wellness-premium.netlify.app" in content
    assert "สวัสดีครับ" in content
    assert "฿5,000" in content


def test_report_row_stores_both_urls(sample_lead, sample_brand):
    row = ReportRow(
        lead=sample_lead,
        brand=sample_brand,
        starter_url="https://a.netlify.app",
        premium_url="https://b.netlify.app",
    )
    assert row.starter_url == "https://a.netlify.app"
    assert row.premium_url == "https://b.netlify.app"
