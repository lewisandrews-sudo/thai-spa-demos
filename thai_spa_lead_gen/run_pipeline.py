#!/usr/bin/env python3
# thai_spa_lead_gen/run_pipeline.py
"""
Thai Spa Lead Generator & Site Builder
Usage: python run_pipeline.py --area sukhumvit --type massage --count 20
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SITES_DIR = BASE_DIR / "sites"
REPORT_PATH = BASE_DIR / "report.html"


def run_pipeline(area: str, business_type: str, count: int, skip_deploy: bool, dry_run: bool):
    from lead_scanner import scan_leads
    from brand_extractor import extract_brand
    from site_generator import generate_site
    from booking_backend import provision_booking_table
    from deployer import deploy_all, DeployResult
    from report_generator import generate_report, ReportRow

    # ── Step 1: Lead Discovery ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  STEP 1: Scanning for {count} {business_type} leads in {area}...")
    print(f"{'='*60}")

    leads_cache = DATA_DIR / "leads.json"
    if leads_cache.exists():
        print(f"  [cache] Loading leads from {leads_cache}")
        leads = json.loads(leads_cache.read_text())
    else:
        leads = scan_leads(area=area, business_type=business_type, count=count)
        DATA_DIR.mkdir(exist_ok=True)
        leads_cache.write_text(json.dumps(leads, ensure_ascii=False, indent=2))

    print(f"  → {len(leads)} leads found\n")

    if dry_run:
        print("  [dry-run] Stopping after lead discovery.")
        return

    # ── Step 2: Brand Extraction ────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"  STEP 2: Extracting brand intelligence (Claude)...")
    print(f"{'='*60}")

    brands_cache = DATA_DIR / "brands.json"
    if brands_cache.exists():
        print(f"  [cache] Loading brands from {brands_cache}")
        brands = json.loads(brands_cache.read_text())
    else:
        brands = []
        for i, lead in enumerate(leads):
            print(f"  [{i+1}/{len(leads)}] {lead['name']}")
            try:
                brand = extract_brand(lead)
                brands.append(brand)
                time.sleep(1)  # rate-limit politeness
            except Exception as e:
                print(f"  [error] Brand extraction failed for {lead['name']}: {e}")
        brands_cache.write_text(json.dumps(brands, ensure_ascii=False, indent=2))

    print(f"  → {len(brands)} brands extracted\n")

    # Build lookup: slug → brand, slug → lead
    brand_map = {b["slug"]: b for b in brands}
    lead_map  = {l["slug"]: l for l in leads}

    # ── Step 3: Site Generation ─────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"  STEP 3: Generating sites...")
    print(f"{'='*60}")

    SITES_DIR.mkdir(exist_ok=True)
    generated = []
    for brand in brands:
        lead = lead_map.get(brand["slug"])
        if not lead:
            continue
        try:
            generate_site(lead, brand, output_dir=str(SITES_DIR), deploy_url="")
            generated.append(brand["slug"])
        except Exception as e:
            print(f"  [error] Site gen failed for {brand['slug']}: {e}")

    print(f"  → {len(generated) * 2} sites generated ({len(generated)} businesses)\n")

    if skip_deploy:
        print("  [skip-deploy] Skipping Netlify deployment.")
        rows = [
            ReportRow(lead=lead_map[s], brand=brand_map[s], starter_url=None, premium_url=None)
            for s in generated if s in lead_map and s in brand_map
        ]
        generate_report(rows, str(REPORT_PATH), area=area, business_type=business_type, open_browser=True)
        return

    # ── Step 4: Booking Backend ─────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"  STEP 4: Provisioning Supabase booking tables...")
    print(f"{'='*60}")
    for slug in generated:
        provision_booking_table(slug)

    # ── Step 5: Deploy ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  STEP 5: Deploying to Netlify ({len(generated) * 2} sites)...")
    print(f"{'='*60}")

    deploy_results: list[DeployResult] = deploy_all(
        [{"slug": s} for s in generated],
        sites_dir=str(SITES_DIR),
    )

    # Map results back to slugs
    url_map: dict[str, dict] = {}
    for r in deploy_results:
        if r.slug not in url_map:
            url_map[r.slug] = {}
        key = "premium_url" if r.is_premium else "starter_url"
        url_map[r.slug][key] = r.url if r.success else None

    # ── Step 6: Report ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  STEP 6: Generating report...")
    print(f"{'='*60}")

    rows = []
    for slug in generated:
        if slug not in lead_map or slug not in brand_map:
            continue
        urls = url_map.get(slug, {})
        rows.append(ReportRow(
            lead=lead_map[slug],
            brand=brand_map[slug],
            starter_url=urls.get("starter_url"),
            premium_url=urls.get("premium_url"),
        ))

    generate_report(rows, str(REPORT_PATH), area=area, business_type=business_type, open_browser=True)

    success_count = sum(1 for r in deploy_results if r.success)
    print(f"\n{'='*60}")
    print(f"  Pipeline complete!")
    print(f"  Leads: {len(leads)} | Sites: {len(generated)*2} | Deployed: {success_count}")
    print(f"  Report: {REPORT_PATH}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thai Spa Lead Generator")
    parser.add_argument("--area", default="sukhumvit",
                        choices=["sukhumvit", "silom", "thonglor", "ekkamai", "ari", "asok"],
                        help="Bangkok area to target")
    parser.add_argument("--type", dest="business_type", default="all",
                        choices=["massage", "spa", "onsen", "all"],
                        help="Type of business to find")
    parser.add_argument("--count", type=int, default=20,
                        help="Max number of leads to process")
    parser.add_argument("--skip-deploy", action="store_true",
                        help="Generate sites locally, skip Netlify deployment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Lead discovery only, no site generation")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Delete leads.json and brands.json to force fresh scan")
    args = parser.parse_args()

    if args.clear_cache:
        for f in ["data/leads.json", "data/brands.json"]:
            p = BASE_DIR / f
            if p.exists():
                p.unlink()
                print(f"  [cache] Cleared {f}")

    # Change to script dir so relative paths work
    os.chdir(BASE_DIR)
    run_pipeline(
        area=args.area,
        business_type=args.business_type,
        count=args.count,
        skip_deploy=args.skip_deploy,
        dry_run=args.dry_run,
    )
