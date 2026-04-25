import os
import json
import subprocess
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()
NETLIFY_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN", "")


@dataclass
class DeployResult:
    slug: str
    is_premium: bool
    success: bool
    url: str | None
    error: str | None = None


def build_site_name(slug: str, is_premium: bool) -> str:
    suffix = "premium" if is_premium else "starter"
    return f"{slug}-{suffix}"


def deploy_site(site_dir: str, slug: str, is_premium: bool) -> DeployResult:
    """
    Deploy a site directory to Netlify.
    Returns a DeployResult with the live URL or error message.
    """
    if not NETLIFY_TOKEN:
        print(f"  [skip] NETLIFY_AUTH_TOKEN not set — skipping deploy for {slug}")
        return DeployResult(slug=slug, is_premium=is_premium, success=False, url=None, error="No token")

    site_name = build_site_name(slug, is_premium)

    cmd = [
        "netlify", "deploy",
        "--dir", site_dir,
        "--site", site_name,
        "--prod",
        "--json",
        "--auth", NETLIFY_TOKEN,
    ]

    print(f"  Deploying: {site_name} ...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"  [error] Deploy failed for {site_name}: {result.stderr[:200]}")
        return DeployResult(slug=slug, is_premium=is_premium, success=False, url=None, error=result.stderr[:200])

    try:
        data = json.loads(result.stdout)
        url = data.get("deploy_url") or data.get("url")
        print(f"  Deployed: {url}")
        return DeployResult(slug=slug, is_premium=is_premium, success=True, url=url)
    except json.JSONDecodeError:
        # netlify CLI sometimes outputs non-JSON with url in it
        for line in result.stdout.splitlines():
            if "netlify.app" in line:
                url = line.strip().split()[-1]
                return DeployResult(slug=slug, is_premium=is_premium, success=True, url=url)
        return DeployResult(slug=slug, is_premium=is_premium, success=False, url=None, error="Could not parse URL")


def deploy_all(sites: list[dict], sites_dir: str) -> list[DeployResult]:
    """
    Deploy starter and premium for each business in the sites list.
    sites: list of dicts with 'slug' key.
    Returns list of DeployResult (2 per business).
    """
    results = []
    for site in sites:
        slug = site["slug"]
        starter_dir = os.path.join(sites_dir, slug, "starter")
        premium_dir = os.path.join(sites_dir, slug, "premium")

        if os.path.exists(starter_dir):
            results.append(deploy_site(starter_dir, slug, is_premium=False))
        if os.path.exists(premium_dir):
            results.append(deploy_site(premium_dir, slug, is_premium=True))

    return results
